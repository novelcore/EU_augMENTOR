import ast
import openai 

EVALUATION_PROMPT_TEMPLATE = """You are an expert judge evaluating a Retrieval-Augmented Generation (RAG) answer.

# Instructions
Score the answer from 0–10 on the following criteria:
- Groundedness: Is the answer supported by the context?
- Context Relevance: Is the context relevant to the question?
- Correctness: Are the facts accurate?
- Completeness: Does it fully answer the question?
- Answer Relevancy: Is the answer focused on the query?
- Faithfulness: Is it faithful to the context?

# Output
Format your output in JSON format but do not wrap the output in a code block:
{
  "Groundedness": {"reasoning": "...", "score": ...},
  "Context Relevance": {"reasoning": "...", "score": ...},
  "Correctness": {"reasoning": "...", "score": ...},
  "Completeness": {"reasoning": "...", "score": ...},
  "Answer Relevancy": {"reasoning": "...", "score": ...},
  "Faithfulness": {"reasoning": "...", "score": ...},
  "total_score": ...
}

# Information
Question:
{query}
Context:
{context}
Answer:
{response}
"""


def evaluation(query:str=None, context:str=None, response:str=None, openai_settings:dict=None)->str:
    """
    Evaluates the quality of a generated response based on a given question and context using multiple criteria.

    This function uses a GPT-based model to assess the response against the following evaluation metrics:
    - Groundedness
    - Context Relevance
    - Correctness
    - Completeness
    - Answer Relevancy
    - Faithfulness

    Each metric includes a score and reasoning. A total score is also returned, normalized to a scale of 0 to 100.

    Args:
        query (str, optional): The original user query.
        context (str, optional): The supporting context retrieved to answer the query.
        response (str, optional): The generated answer to be evaluated.

    Returns:
        dict: A dictionary containing individual scores and reasoning for each metric, along with a `total_score` field.

    Example:
        >>> evaluation(query="What is AI?", context="...", response="AI is ...")
        {
            "Groundedness": { "reasoning": "...", "score": 9 },
            "Context Relevance": { "reasoning": "...", "score": 10 },
            ...
            "total_score": 92.5
        }
    """
    openai.api_key = openai_settings['api_key']

    # Create prompt
    prompt = EVALUATION_PROMPT_TEMPLATE.replace("{query}", query)
    prompt = prompt.replace("{context}", context)
    prompt = prompt.replace("{response}", response)

    # Prepare messages for ChatGPT-based models
    messages = [
            { "role": "system", "content": "You are an expert judge evaluating the Retrieval Augmented Generation applications. Your task is to evaluate a given answer based on a context and question using the criteria provided below" },
            { "role": "user", "content": prompt },
        ]

    response = openai.ChatCompletion.create(
                            model=openai_settings['model_name'],
                            messages=messages,
                            temperature=openai_settings['temperature'],
                        )

    # Extract content from the response
    response = ast.literal_eval(response.choices[0].message.content)
    response['total_score'] *= (100.0/60.0)
    
    return response