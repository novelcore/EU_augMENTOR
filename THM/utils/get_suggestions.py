from langchain.graphs import Neo4jGraph
from langchain.prompts.prompt import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains.llm import LLMChain
import ast

# prompt = """You are an assistant which support a Teacher in a class. You must select one of the available modules from the Information section
# to recommend to a learner for improving its knowledges and performance. The user needs are available in Question section.

# The information part contains the provided information that you must use to construct an answer.
# The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.

# # Question
# {question}

# # Information
# {information}

# # Instructions:
# - The Information section contains the provided information that you must use to answer.
# - The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
# - Use only the Information section to make your response.
# - Explain your reply in detail.
# - Reply the title of the recommended module and an explanation. 

# """

# prompt = """You are an assistant which supports a teacher in a class. A learner made a query of selecting a room based on its need and you must proposed to him/her some rooms.
# In the Information Section, there are some room code and their corresponding descriptions. Propose some rooms to the learner in order to satisfy his/her need based on its query.
# Give detailed explanations about your selections
prompt = """You are an assistant which support a Teacher in a class. A learner made a query to the Teacher for selecting a room for improving its knowledge on a specific subject. The rooms are actually classes that the learner is able to register.
Your task is to recommend some rooms to the learner for improving its knowledge and performance on the subject in the query.

In the Query section, there is the learner's query describing the subject that wishes to improve its knowledge.

In the Information section, there is list of the available rooms from which you must select to recommend to the learner for improving its knowledge on the requested subject. You can selected all of them, some of them or none of them.
For each room, there is the room code and its corresponding description. 
The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.

# Query
{query}

# Information:
{information}

# Template
Room: <room code>
Recommendation: <recommendation why this room is recommended>
Relevance: <relevance score in %>

# Instructions:
- Do not include any apologies in your answer.
- Select the the rooms that have relevance with the subject in the query. You can select all of them, some of them or none of them.
- If none of the available rooms is able to satisfy the need of the user reply: "There are no available rooms for the requested subject".
- The suggested rooms will be sorted based on their relevance score.
- Use the template for presenting each recommended room.
- If the query refers information about learner's username then ignore it.
- Give details and reasoning for the recommendations.

Answer:"""
# - Βriefly recommend the learner to study the resources (videos and tutorial of each room) for improving his/her performance.
# - Provide a roadmap and instructions to the learner about the learning path.

# - Start the reply with: "Dear Learner,".
# - Conclude the reply as
# Kind regards,
# Ioannis

def get_suggestion_about_learning(faiss_index=None, username:str=None, graph:Neo4jGraph=None, question:str=None):

    if username is not None:
        query = f"""MATCH (l:LEARNER {{username: '{username}'}})
        RETURN l.completed_rooms as completed_rooms"""    

        completed_rooms = ast.literal_eval(graph.query(query)[0]['completed_rooms'])
        print(completed_rooms)
        
    # Get top-5 similar classes
    response = faiss_index.similarity_search_with_score(question, k = 5)

    information = ""
    for (item, score) in response:
        print(item.metadata['code'], score)
        if score > 0.38: continue
        information += f"""- Room code: {item.metadata['code']}. Description: {item.page_content}.\n"""
    
    if information == "":
        return "There are no available rooms for the requested subject", "There are no available rooms for the requested subject"
    else:
        openai_settings = {
            "model_name": "gpt-3.5-turbo",  # Choices: {"gpt-3.5-turbo", "gpt-3.5-turbo-16k"}
            "temperature": 0,
            "api_key": "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",
        }    
        llm = ChatOpenAI(model_name=openai_settings["model_name"], temperature=openai_settings["temperature"], openai_api_key=openai_settings['api_key'])
        my_chain = LLMChain(llm=llm, prompt=PromptTemplate(input_variables=["query", "information"], template=prompt))
        
        # Reply to the query
        response = my_chain({"query": question, "information": information})   
        print("Suggested rooms:", response)
        
    return response["text"], response["text"]
    