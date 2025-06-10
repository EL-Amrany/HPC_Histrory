from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from flask_login import login_required, current_user
from app import db
from utils.chat_logic import build_tutor_prompt
from models.progress import Progress
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import DirectoryLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain_openai import OpenAIEmbeddings
from markupsafe import Markup
import re
from markdown import markdown

# Load documents
loader = DirectoryLoader("data/")
embeddings = OpenAIEmbeddings(api_key="open-ai_key")
index_creator = VectorstoreIndexCreator(embedding=embeddings)
index = index_creator.from_loaders([loader])

llm = ChatOpenAI(
    model="gpt-4o",
    openai_api_key="open-ai_key",
)

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chat')

@chatbot_bp.route('/')
@login_required
def chat_page():
    return render_template("chat.html")

@chatbot_bp.route('/start_concept', methods=['POST'])
@login_required
def start_concept():
    concept = request.form.get('concept')
    session['lesson_state'] = {
        'stage': 'explain',
        'concept': concept,
        'retry_count': 0,
        'rewards': 0,
        'xp': 0,
        'completed': [],
        'history': [],
        'current_question': '',
        'correct_answer': '',
        'correct_text': ''
    }
    return redirect(url_for('chatbot.chat_page'))

def explain(concept, state, feedback=''):
    prompt = f"""
    You are an interactive HPC tutor. Explain the concept '{concept}' clearly, including:
    - Include this sentence in the first line : {feedback}
    - A full paragraph of explanation
    - One step-by-step example
    - End with a multiple choice question (A to D)

    Internally, include the correct answer on the last line like: Answer: B
    (This line will be parsed but never shown to the user)
    include this sentence at the end : provide a one letter answer

    Provide the entire module directly as HTML only. Do not add markdown or backticks.
    """
    response_raw = index.query(prompt, llm=llm)

    # Extract answer letter and clean response
    answer_match = re.search(r"answer:\s*([a-d])", response_raw, re.IGNORECASE)
    correct_letter = answer_match.group(1).lower() if answer_match else 'a'
    cleaned_response = re.sub(r"answer:\s*[a-d]", "", response_raw, flags=re.IGNORECASE).strip()

    # Extract full correct answer text
    option_match = re.search(rf"{correct_letter.upper()}\)\s*(.*?)\s*(?:[A-D]\)|$)", cleaned_response, re.IGNORECASE)
    correct_text = option_match.group(1).strip().lower() if option_match else ''

    # Update state
    state.update({
        'stage': 'awaiting_answer',
        'current_question': cleaned_response,
        'correct_answer': correct_letter,
        'correct_text': correct_text,
        'retry_count': 0
    })

    return Markup(markdown(cleaned_response))

def is_correct_answer(user_input, correct_letter, correct_text):
    user_input = user_input.strip().lower()
    correct_letter = correct_letter.strip().lower()
    correct_text = correct_text.strip().lower()

    user_input_clean = re.sub(r"[^\w\s]", "", user_input)

    if user_input_clean == correct_letter:
        return True


    patterns = [
        rf"\b{correct_letter}\b",
        rf"option\s+{correct_letter}",
        rf"answer\s+(is\s+)?{correct_letter}",
        rf"i\s+choose\s+{correct_letter}",
        rf"i\s+think\s+(it's\s+)?{correct_letter}"
    ]
    for pattern in patterns:
        if re.search(pattern, user_input_clean):
            return True

    if correct_text in user_input:
        return True

    return False

def is_correct_answer(user_input, correct_letter, correct_text):
    input_clean = user_input.lower().strip(".) ")
    return input_clean == correct_letter.lower()

@chatbot_bp.route('/ask', methods=['POST'])
@login_required
def ask():
    data = request.get_json()
    user_input = data.get('message', '').strip()

    state = session.get('lesson_state', {})
    stage = state.get('stage', 'explain')
    concept = state.get('concept', 'SLURM basics')
    retry_count = state.get('retry_count', 0)
    rewards = state.get('rewards', 0)
    history = state.get('history', [])
    response_html=''

    if state['stage'] == 'explain':
        response_html = explain(concept, state)
        history.append({'bot': response_html})

    elif state['stage'] == 'awaiting_answer':
        correct_letter = state.get('correct_answer', 'a')
        correct_text = state.get('correct_text', '')

        if is_correct_answer(user_input, correct_letter, correct_text):
            rewards += 1
            current_user.progress += 5
            db.session.commit()

            progress = Progress.query.filter_by(user_id=current_user.id, module_name=concept).first()
            if not progress:
                progress = Progress(user_id=current_user.id, module_name=concept)
                db.session.add(progress)
            if progress.xp is None:
                progress.xp = 0

            progress.xp += 5
            progress.completion_percentage = min(progress.xp, 100)

            if progress.xp >= 30:
                progress.badge = "🥇 HPC Hero"
            elif progress.xp >= 15:
                progress.badge = "🥈 Slurm Star"
            elif progress.xp >= 5:
                progress.badge = "🥉 Bash Beginner"

            db.session.commit()

            state.setdefault('completed', []).append(concept)

            if len(state['completed']) >= 3:
                feedback = "✅ **Correct!** 🎉 You’ve completed 3 modules! Consider downloading your certificate."
            else:
                feedback = "✅ **Correct!** Here's your next concept!"

            history.append({'bot': Markup(markdown(feedback))})

            # Move on to next concept
            state['stage'] = 'explain'
            
            response_html = explain(concept, state,feedback)

        else:
            
            retry_count += 1
            if retry_count <2 :
                
                state['retry_count'] = retry_count
                response_html = Markup(markdown("❌ Try again! .**"))

            else:
                state['stage'] = 'review'
                




    if state['stage'] == 'review':
        prompt = f" Include the sentence in the biginning (❌ That's not quite right let's review the concept!) .and Re-explain '{concept}' simply with a basic example. Then ask the same MCQ: {state['current_question']} but do not include this feedback now  (Correct! Here's your next concept!)"
        response_raw = index.query(prompt, llm=llm)
        state['stage'] = 'awaiting_answer'
        response_html = Markup(markdown(response_raw))

    state['rewards'] = rewards
    state['history'] = history
    session['lesson_state'] = state

    return jsonify({"response": str(response_html)})
