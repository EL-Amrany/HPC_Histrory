
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


# Initialize vector index
# Load HPC documents
loader = DirectoryLoader("data/")
embeddings = OpenAIEmbeddings(api_key="sk-proj-Kl1lflhbwL0QhXOnzJ1UT3BlbkFJoqsfEVjW0uZyLwo2DCVr")
index_creator = VectorstoreIndexCreator(embedding=embeddings)
index = index_creator.from_loaders([loader])

llm = ChatOpenAI(
    model="gpt-4o",
    openai_api_key="sk-proj-Kl1lflhbwL0QhXOnzJ1UT3BlbkFJoqsfEVjW0uZyLwo2DCVr",
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
        'correct_answer': ''
    }
    return redirect(url_for('chatbot.chat_page'))
@chatbot_bp.route('/ask', methods=['POST'])
@login_required
def ask():
    data = request.get_json()
    user_input = data.get('message', '').strip().lower()

    state = session.get('lesson_state', {})
    stage = state.get('stage', 'explain')
    concept = state.get('concept', 'SLURM basics')
    retry_count = state.get('retry_count', 0)
    rewards = state.get('rewards', 0)
    history = state.get('history', [])

    if stage == 'explain':
        prompt = f"""
        You are an interactive HPC tutor. Explain the concept '{concept}' clearly, including:
        - A full paragraph of explanation
        - One step-by-step example
        - End with a multiple choice question (A to D) 

        Internally, include the correct answer on the last line like: Answer: B
        (This line will be parsed but never shown to the user)
        include this sentence at the end : provide a one letter answer
        
        Provide the entire module directly as HTML only. Do not add markdown or backticks.
        """

        response_raw = index.query(prompt, llm=llm)

        # Extract and remove the answer line
        answer_match = re.search(r"answer:\s*([a-d])", response_raw, re.IGNORECASE)
        correct_answer = answer_match.group(1).lower() if answer_match else 'a'
        cleaned_response = re.sub(r"answer:\s*[a-d]", "", response_raw, flags=re.IGNORECASE).strip()

        # Optional: Parse and reformat question
        question_match = re.search(r"(question:.*?)(a\).+?b\).+?c\).+?d\).+)", cleaned_response, re.IGNORECASE | re.DOTALL)
        if question_match:
            question_text = question_match.group(1).strip()
            choices_text = question_match.group(2).strip()
            full_question = f"{question_text} {choices_text}"
        else:
            full_question = "What is Slurm? A) ... B) ... C) ... D)"

        state.update({
            'stage': 'awaiting_answer',
            'current_question': full_question,
            'correct_answer': correct_answer,
            'retry_count': 0
        })

        response_html = Markup(markdown(cleaned_response))
        history.append({'bot': response_html})

    elif stage == 'awaiting_answer':
        correct = state.get('correct_answer', 'a')

        def is_correct_answer(user_input, correct):
            input_clean = user_input.lower().strip(".) ")
            return input_clean == correct.lower()

        if is_correct_answer(user_input, correct):
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

            if concept not in state.get('completed', []):
                state.setdefault('completed', []).append(concept)

            if len(state['completed']) >= 3:
                response_raw = "✅ **Correct!** 🎉 You’ve completed 3 modules! Consider downloading your certificate."
            else:
                response_raw = "✅ **Correct!** Let's move on to the next step."

            state['stage'] = 'explain'
        else:
            retry_count += 1
            if retry_count >= 2:
                state['stage'] = 'review'
                response_raw = "❌ That's not quite right. **Let's review the concept.**"
            else:
                state['stage'] = 'awaiting_answer'
                response_raw = "❌ Try again! **Focus on the key explanation.**"

        state['rewards'] = rewards
        state['retry_count'] = retry_count
        response_html = Markup(markdown(response_raw))

    elif stage == 'review':
        prompt = f"Re-explain '{concept}' simply with a basic example. Then ask the same MCQ: {state['current_question']}"
        response_raw = index.query(prompt, llm=llm)
        state['stage'] = 'awaiting_answer'
        response_html = Markup(markdown(response_raw))

    state['history'] = history
    session['lesson_state'] = state

    return jsonify({"response": str(response_html)})