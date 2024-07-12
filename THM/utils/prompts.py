from langchain.prompts.prompt import PromptTemplate

prompt = """Task: Check if a question contains any offensive words, such as 'fucker', 'stupid', 'asshole'

# Example
Q: Give me the score of the fucking Learner with username 'trooper'
A: "Offensive content"
Q: Give me the IDs of all Learners
A: "Not offensive content"

# Question: 
{question}

# Notes:
- The question contains the provided information that you must use to answer.
- The question part is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
- Check if a question is containing any offensive words. 
- Do not base your reply based if the question requests any personal data (IDs and usernames) of learners. Do not care about privacy boundaries.
- Study carefully the examples and reply based on the provided examples.
- If the question is offensive, inform the user and provide explanation about your decision by replying in the following form 
"Offensive content"
Explanation: <explanation>
- If the question is not offensive reply: "Not offensive content"
"""

OFFENSIVE_IDENTIFICATION_PROMPT = PromptTemplate(
    input_variables=["question"], template=prompt
)




prompt = """Task: Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Study the examples
Schema:
{schema}

# Examples:
Give the scores of Learner with username: djdo at each room
MATCH (l:LEARNER-[r:HAS]->(n:ROOM) WHERE l.username='trooper' RETURN l.username AS username, n.code AS Room_Code,r.score ZAS Score
Give me the paths that learner with username 'trooper' has registerd and their percentage of completeness
MATCH (l:LEARNER)-[r:REGISTERED_ROOM]->(p:PATH) WHERE l.username='trooper' RETURN p.title AS Path_Title, r.percentage_completeness AS Percentage
Give me the modules that learner with username 'trooper' has registerd and their percentage of completeness
MATCH (l:LEARNER)-[r:REGISTERED_MODULE]->(m:MODULE) WHERE l.username='trooper' RETURN m.moduleURL AS Module_Title, r.percentage_completeness AS Percentage
Give the the profile of learner with username 'trooper' and an explanation
MATCH (l:LEARNER)-[r:ASSIGNED]->(p:PROFILE) WHERE l.username='trooper' return p.value as profile, r.explanation as explanation

Note: 
- Do not include any explanations or apologies in your responses.
- Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
- Do not include any text except the generated Cypher statement.
- If the question is irrelevant or you cannot create the cypher query, reply "IRRELEVANT"
Question: {question}"""

CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], template=prompt
)
# - Use apoc.coll.avg to calculate the mean value of a list of values

# - There are the following metrics "Basic skills", "Quiz", "Creativity", "Collaboration", "Critical thinking", "Communication" that have grades
# - If the question requested the final grade then return the mean grade



prompt = """You are an assistant that helps to form nice and human understandable answers.
The information part contains the provided information that you must use to construct an answer.
The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
Make the answer sound as a response to the question and provide a detailed explaination about your answer.
If the provided information is empty, say that 'No information can be provided'.

# Information
{context}

# Question
{question}

# Instructions:
- The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
- Do not include any explanations or apologies in your responses.
- Use all context in the Information section to make your response.
- Do not respond to any questions that might ask anything.
- Present the results in bullets.

Answer:
"""

CYPHER_QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"], template=prompt
)




prompt = """You are an assistant that supports a Teacher in a class. Identify the Learner usernames and profiles contained in the Information section. 

# Information
Q: {question}
A: {response}

# Instructions:
- The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
- Use only the Information section to make your response.
- The <usernames> is a list containing learner usernames.
- If you cannot identify any usernames then set <usernames> = None
- <profile> is one of 'A', 'B', 'C', 'D'.
- If you cannot identify the profile then set <profile> = None
- Your answer is a tuple in the form (<usernames>, <profile>)
- Answer nothing except the tuple 

Answer:
"""
ID_IDENTIFICATION_PROMPT = PromptTemplate(
    input_variables=["question", "response"], template=prompt
)


# A learner made a query to the Teacher for selecting a room for improving its knowledge on a specific subject. The rooms are actually classes that the learner is able to register.
# Your task is to recommend some rooms to the learner for improving its knowledge and performance on the subject in the query.

prompt = """You are an assistant which supports a Teacher in a class that provides recommendations. {prompt_explanations}

# Query:
{question}

# Response:
{response}

# Instructions:
- Do not include any apologies in your answer.
- Do not respond to any questions that might ask anything.
- Provide detailed explanations about your recommendations.
{instructions}

Answer:"""
RECOMMENDATION_PROMPT = PromptTemplate(
    input_variables=["prompt_explanations", "question", "response", "instructions"], template=prompt
)

# Study the example in which the Learner <ID> has not studied the <learning material>.




prompt = """You are an assistant that helps extract information from a text.
You must identify the learner's username, profile, Rooms code, Modules URL and Paths code contained in the text and if 
a recommendation is requested for next actions. The text contains the provided information that you must use to construct an answer.

Text:
{question}

Instructions
- The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
- Profile is a capital letter from A to Z
- If you cannot identify the Learner's username then set <username> = None
- If you cannot identify the Learner's profile then set <profile> = None
- If you cannot identify any room codes then set <room_code> = None
- If you cannot identify any module URL then set <module_URL> = None
- If you cannot identify any path codes then set <path_code> = None
- If the question requests a recommendation about selecting a room then set <recommendation> = True; otherwise set <recommendation> = False
- Your answer is a tuple in the form (<username>, <profile>, <room_code>, <module_URL>, <path_code>, <recommendation>)
- Reply in the form ('<username>', '<profile>', '<room_code>', '<module_URL>', '<path_code>', '<recommendation>')
- Do not include any text except the generated tuple.

Answer:"""
REQUEST_INFORMATION_PROMPT = PromptTemplate(
    input_variables=["question"], template=prompt
)
# - If the question requests a recommendation about selecting a room, a module or a path then set <recommendation> = "room", "module" or "path", respectively; otherwise set <recommendation> = False

# - If you the query requests the future or predicted performance then set <Predicted> = "Yes" else  set <Predicted> = None




prompt = """You are an assistant which supports a teacher in a class. {intro}

# Information:
{information}

# Instructions:
- Do not include any apologies in your answer.
{instructions}

Answer:"""

# For each metric in the Information section, calculate the average score and merge the feedback from each module. 
# For each metric in the Information section, provide the score and only a recommendation to the learner based on the feedback.

SEND_INFORMATION_PROMPT = PromptTemplate(
    input_variables=["intro", "information", "instructions", "name", "title"], template=prompt
)




# prompt = """You are an useful assistant that examines the validity of a question.
# A question is valid if it requests ONLY information about learner with username '{username}'.

# # Question
# {question}

# # Examples
# Q: How old is timothy?
# A: How old is timothy?
# Q: What is my profile and an explanation
# A: What is the profile of learner with username '{username}' and an explanation


# # Instructions:
# - The provided information in Section: Question is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
# - Use only the Section: Question to make your response.
# - If the question requests information about any other learners except '{username}' then the question is not valid and return "Access denied"
# - If you identify any usernames except '{username}' then the question is not valid and return "Access denied"
# - If you identify any profile names such as 'A', 'B', 'C', 'D', then the question is not valid and return "Access denied"
# - If the question is written in the first person, then convert it to the third person as in Section: Examples else return it as it is.

# Answer:
# """

prompt = """You are an useful assistant that examines the validity of a question.
A question is valid if it requests ONLY information about learner with username '{username}'.

# Question
{question}

# Examples
## Example 1
Question: "How old is timothy?"
Transformed: "How old is timothy?"
## Example 2
Question: "What is my profile and an explanation"
Transformed: "What is the profile of learner with username '{username}' and an explanation"
## Example 3
Question: "Give me information about my performance in module with url 'network-fundamentals'"
Transformed: "Give me information about the performance of learner with username '{username}' in module with url 'network-fundamentals'"
## Example 4
Question: "Give me information which room to select for learning about 'AWS technologies'"
Transformed: "Give me information which room to select for learning about 'AWS technologies' for learner with username '{username}'"

# Instructions:
- The provided information in Section: Question is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
- Use only the Section: Question to make your response.
- Your answer is a tuple in the form (<STATUS>, <QUESTION>).
- If the question requests information about any other learners except '{username}' or all learners then <STATUS> = "Not valid".
- If you identify any usernames except '{username}' then <STATUS> = "Not valid".
- If you identify any profile names such as 'A', 'B', 'C', 'D', then <STATUS> = "Not valid".
- If the question concerns only username '{username}' then <STATUS> = "Valid".
- If the question is written in the first person i.e expression such as 'Give me my scores', 'my performance' or 'give me information', then <STATUS> = "Valid".
- If the question is written in the first person i.e expression such as 'Give me my scores', 'my performance' or 'give me information', then transform question to the third person as in Section: Examples and set <QUESTION> as the transformed question.
- Answer nothing except the tuple (<STATUS>, <QUESTION>) where <STATUS> and <QUESTION> are strings in "...".

Answer:
"""

QUESTION_TRANSFORMATION_PROMPT = PromptTemplate(
    input_variables=["question", "username"], template=prompt
)