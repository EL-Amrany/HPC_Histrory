import os
from langchain_community.document_loaders import DirectoryLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv

# Make sure you do this early!
load_dotenv()



# Load HPC documents
loader = DirectoryLoader("data/")
embeddings = OpenAIEmbeddings(api_key="sk-proj-Kl1lflhbwL0QhXOnzJ1UT3BlbkFJoqsfEVjW0uZyLwo2DCVr")
index_creator = VectorstoreIndexCreator(embedding=embeddings)
index = index_creator.from_loaders([loader])

llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    openai_api_key="sk-proj-Kl1lflhbwL0QhXOnzJ1UT3BlbkFJoqsfEVjW0uZyLwo2DCVr",
) 

def get_chatbot_response(user_message, skill_level, progress):
    """
    Return an adaptive HPC response based on user skill_level and progress.
    You can refine the logic to produce simpler or more complex answers.
    """

    # Example: add some dynamic instructions
    if skill_level == 'beginner':
        difficulty_instruction = "Explain as if you are teaching someone new to HPC. Keep it simple."
    elif skill_level == 'intermediate':
        difficulty_instruction = "Provide more in-depth explanations and some HPC-specific commands or code."
    else:  # advanced
        difficulty_instruction = "Offer advanced concepts, performance tuning tips, etc."

    # Build prompt for the LLM
    custom_prompt = f"""
    You are an HPC instructor. The user has a skill level = {skill_level}, progress = {progress}.
    {difficulty_instruction}

    User's question: {user_message}

    Answer thoroughly, referencing HPC best practices, but keep it concise.
    """

    # Query the vector index of HPC docs for context
    response = index.query(custom_prompt, llm=llm)

    return response

def build_adaptive_learning_prompt(user_history, skill_level="beginner"):
    prompt = f"""
    You are an adaptive HPC instructor chatbot teaching a student at the {skill_level} level. 
    Your goal is to teach HPC gradually, adjusting complexity based on the user's answers.
    
    Follow these steps strictly:
    
    1. Provide a concise explanation of a fundamental HPC concept appropriate for their skill level.
    2. Immediately ask one comprehension question about this concept to test the student's understanding. 
       - Clearly state: "Question:" followed by the question.
       - Provide multiple-choice answers labeled clearly as (A), (B), (C), (D).
    3. Wait for the student's response before proceeding further.
    
    Here’s the conversation so far for context:
    {user_history}

    Now, proceed as instructed.
    """
    return prompt


def build_tutor_prompt(history, concept, skill_level):
    return f"""
You are an interactive tutor teaching High-Performance Computing (HPC).
The student is a {skill_level} learner.

Your current concept: "{concept}"

1. Begin by clearly explaining this concept at their skill level.
2. Immediately follow up with a multiple-choice question (labelled A, B, C, D) to check understanding.
3. Do NOT answer the question. Only present it.
4. Use <strong> key terms </strong>, <code>example snippets</code>, and clear steps.

Previous context:
{history}

Now proceed.
"""

def get_quiz_question(concept):
    return f"Ask one multiple choice quiz about {concept} with labeled choices A to D and only one correct answer."


from langchain_openai import ChatOpenAI
from langchain.indexes import VectorstoreIndexCreator
from langchain_community.document_loaders import DirectoryLoader
from langchain_openai import OpenAIEmbeddings




def evaluate_answer_with_llm(user_response, expected_question):
    """
    Evaluates if a user's response to a question is correct using the LLM.
    Returns a tuple: (True/False, feedback string)
    """
    evaluation_prompt = f"""
You are an HPC tutor evaluating a student's response to a quiz.

Question: {expected_question}
Student Answer: {user_response}

Respond in this format:
1. "correct" or "incorrect" at the start.
2. Then give a one-line explanation or suggestion.

Example:
correct: Yes, SLURM is used to submit and manage jobs on HPC clusters.

Now evaluate the student's answer:
"""

    response = llm.predict(evaluation_prompt).strip().lower()

    if response.startswith("correct"):
        return True, response
    elif response.startswith("incorrect"):
        return False, response
    else:
        return False, "unclear: I couldn’t evaluate your answer. Try rephrasing."

def extract_question(response):
    import re
    match = re.search(r"Question:(.*?)(?:\n|$)", response)
    return match.group(1).strip() if match else ""


def get_next_concept(current):
    concepts = [
        "What is HPC?",
        "What is a cluster?",
        "SLURM basics",
        "Running jobs on ULHPC",
        "Bash scripting basics"
    ]
    try:
        index = concepts.index(current)
        return concepts[(index + 1) % len(concepts)]
    except ValueError:
        return "What is HPC?"
