from langchain.prompts.prompt import PromptTemplate

prompt = """Task: Check if a question contains any offensive words, such as 'fucker', 'stupid', 'asshole'

# Example
Q: Give me the grade of the fucking Learner with username 'trooper'
A: "Offensive content"
Q: Give me the usernames of all Learners
A: "Not offensive content"

# Question: 
{question}

# Notes:
- The question contains the provided information that you must use to answer.
- The question part is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
- Check if a question is containing any offensive words. 
- Do not base your reply based if the question requests any personal data (such as usernames) of learners. Do not care about privacy boundaries.
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

Examples:
Give the grades of Learner with username 'trooper' for Module 1
MATCH (l:LEARNER)-[r]->(a:ACTIVITY) MATCH (l)-[]->(c:COURSE)-[]->(m:MODULE)-[]->(a) where l.username='trooper' AND m.code = "MODULE:1" AND c.id = {course_id} return m.code as Module, a.id as activity_name, r.Cognitive_grade as Cognitive_grade, r.Cognitive_reasoning as Cognitive_reasoning, r.Creativity_grade as Creativity_grade, r.Creativity_reasoning as Creativity_reasoning, r.Collaboration_grade as Collaboration_grade, r.Collaboration_reasoning as Collaboration_reasoning, r.Communication_grade as Communication_grade, r.Communication_reasoning as Communication_reasoning, r.Critical_thinking_grade as Critical_thinking_grade, r.Critical_thinking_reasoning as Critical_thinking_reasoning

Give all Collaboration grades and their corresponding activities of the Learner with username: 'trooper'
MATCH (l:LEARNER)-[r]->(a:ACTIVITY) MATCH (l)-[]->(c:COURSE)-[]->(m:MODULE)-[]->(a) where l.username='trooper' AND c.id = {course_id} return a.id as activity_name, r.Collaboration as Collaboration_grade, r.Collaboration_reasoning as Collaboration_reasoning

Give me a list of all modules titles
MATCH (c:COURSE)-[]->(m:MODULE) where c.id = {course_id} return m.code as Module, m.title as Module_title

Give me a list of all activity titles and their descriptions.
MATCH (c:COURSE)-[]->(m:MODULE)-[]->(a:ACTIVITY) where c.id = {course_id} return a.id as activity_title, a.description as description

Give me a list of learners
MATCH (l:LEARNER)-[]->(c:COURSE) where c.id = c.id = {course_id} return l.username

Give me the profile of learner with username 'trooper' and an explanation
MATCH (l:LEARNER)-[r]->(p:PROFILE) WHERE l.username = "trooper" AND r.course_id = {course_id} RETURN l.username as learner_username, p.name as profile_name, r.explanation as explanation

Give me the three learners that achieved the greater Critical thinking grade in an Forum activity
MATCH (l:LEARNER)-[r]->(a:ACTIVITY)
MATCH (l)-[]->(c:COURSE)-[]->(m:MODULE)-[]->(a)
WHERE c.id = {course_id} AND a.type = "Forum" AND r.Critical_thinking_grade IS NOT NULL
RETURN l.username AS learner_username,
       a.id AS activity_title,
       r.Critical_thinking_grade AS Critical_thinking_grade,
       r.Critical_thinking_reasoning AS Critical_thinking_reasoning
ORDER BY Critical_thinking_grade ASC
LIMIT 3


Give me the five activities with the lowest mean Creativity grade
MATCH (l:LEARNER)-[r]->(a:ACTIVITY) 
MATCH (l)-[]->(c:COURSE)-[]->(m:MODULE)-[]->(a)
WHERE c.id = {course_id}
WITH a, apoc.coll.avg(collect(r.Creativity_grade)) as Creativity_mean_grade, collect(r.Creativity_reasoning) as collected_Creativity_reasoning
RETURN a.id as activity_title, Creativity_mean_grade, collected_Creativity_reasoning
ORDER BY Creativity_mean_grade ASC 
LIMIT 5

Give the resources of Module 17 that learner with username 'trooper' has not studied
MATCH (l:LEARNER {{username:"trooper"}})-[]->(c:COURSE {{id: {course_id} }})-[]->(m:MODULE)-[]->(r:RESOURCE)
WHERE m.code = "MODULE:17" AND NOT EXISTS {{MATCH (l)-[:STUDY]->(r)}}
RETURN collect(r.id) as not_studied_resources

Give the profile of learner with username 'trooper' and an explanation
match (l:LEARNER)-[r]->(p:PROFILE)
where l.username = 'trooper' and r.course_id = {course_id}
return l.learner_username, p.name as profile_name, r.explanation as explanation

Give me the learners' usernames in profile 'SKALA_A' who have not completed activities in 'MODULE:17'
match (l:LEARNER)-[]->(p:PROFILE)
match (l)-[]->(c:COURSE)-[]->(m:MODULE)-[]->(a:ACTIVITY)
where c.id = {course_id} AND m.code = "MODULE:17" AND NOT EXISTS {{MATCH (l)-[]->(a)}}
return m.code as Module_name, l.username as learner_username, collect(distinct a.id) as not_completed_activities

Give me for each learner in profile 'SKALA_A', its username and the time spend for completing the  activities in MODULE:17
MATCH (l:LEARNER)-[]->(p:PROFILE)
MATCH (l)-[]->(c:COURSE)-[]->(m:MODULE)-[]->(a:ACTIVITY)
MATCH (l)-[r]->(a) 
WHERE p.name="IASIS_A" AND c.id = {course_id} AND m.code = "MODULE:17"
RETURN m.code as module_name, l.username as learner_username, apoc.coll.avg(COLLECT(r.time)) AS avg_time

Give me the number of actions, number of completed attempts, the number of clicks, the time and 'Cognitive' grade that learner with username 'trooper' in Quiz activities
match (l:LEARNER)-[]->(c:COURSE)-[]->(m:MODULE)-[]->(a:ACTIVITY) 
match (l)-[r]->(a)
where c.id=16 and a.type='Quiz' and l.username = "trooper"
return a.id, r.number_of_actions as number_of_actions, r.number_of_completed_attempts AS completed_attempts, r.number_of_clicks AS clicks, r.time AS time, r.Cognitive AS Cognitive_grade, r.Cognitive_reasoning AS Cognitive_reasoning

Give me the evaluation and statistics of MODULE:17
match (c:COURSE)-[]->(m:MODULE)
where c.id = {course_id} AND m.code = "MODULE:17"
return m.evaluation as evaluation and m.statistics as statistics

Give me the performance and engagement analysis of learner 'trooper' in all modules
match (c:COURSE)-[]->(m:MODULE)-[]->(a:ACTIVITY)
match (l:LEARNER)-[r]->(a)
where c.id = {course_id} AND l.username = "trooper"
return l.username as learner_username, m.code as module_id, a.id AS activity_title, r.performance as learner_performance, r.engagement as engagement order by m.code

Give me the engagement analysis of learner 'trooper' in all modules
match (c:COURSE)-[]->(m:MODULE)-[]->(a:ACTIVITY)
match (l:LEARNER)-[r]->(a)
where c.id = {course_id} AND l.username = "trooper"
return l.username as learner_username, m.code as module_id, a.id AS activity_title, r.engagement as engagement order by m.code

Give me the performance of learners 'trooper' and 'mitsos' in MODULE:19 and compare them 
match (c:COURSE)-[]->(m:MODULE)-[]->(a:ACTIVITY)
match (l:LEARNER)-[r]->(a)
where c.id = {course_id} AND m.code = "MODULE:19" AND l.username in ["trooper", "mitsos"]
return l.username as learner_username, a.id AS activity_title, r.performance as learner_performance order by l.username 

Give me the performance and engagement analysis of learner 'trooper' in MODULE:19 and compare it with the class
match (c:COURSE)-[]->(m:MODULE)-[]->(a:ACTIVITY)
match (l:LEARNER)-[r]->(a)
where c.id = {course_id} AND m.code = "MODULE:19" AND l.username in ["trooper", "mitsos"]
return a.id AS activity_title, a.statistics as class_performance, l.username as learner_username, r.performance as learner_performance, r.engagement as learner_engagement
order by a.id

Give me the performance of learners 'trooper' and 'mitsos' in MODULE:19 and compare it with the class
MATCH (c:COURSE)-[]->(m:MODULE)-[]->(a:ACTIVITY)
MATCH (l:LEARNER)-[r]->(a)
WHERE c.id = {course_id} AND m.code = "MODULE:19" AND l.username in ["trooper", "mitsos"]
RETURN l.username AS learner_username, a.statistics as class_performance, a.id AS activity_title, r.performance AS learner_performance
ORDER BY learner_performance

Give me the performance of the class for creativity and collaboration in MODULE:17
MATCH (c:COURSE)-[]->(m:MODULE)-[]->(a:ACTIVITY)
MATCH (l:LEARNER)-[r]->(a)
WHERE c.id = {course_id} and m.code: "MODULE:17"
RETURN a.id AS activity_title, a.statistics AS class_performance, r.performance AS learner_performance
ORDER BY learner_performance

Give me for learner 'grp1050' the percentage of completeness for all Modules
MATCH (l:LEARNER)-[]->(c:COURSE)-[]->(m:MODULE)-[]->(a:ACTIVITY)
where l.username='trooper' and c.id={course_id}
MATCH (l)-[r]->(a)
WITH m, 
     COUNT(a) AS totalActivities,
     COUNT(CASE WHEN r.status = 'complete' THEN 1 END) AS completedActivities
RETURN m.code AS moduleId,
       completedActivities,
       totalActivities,
       (toFloat(completedActivities) / totalActivities) * 100 AS percentComplete
ORDER BY m.id;

Notes:
- Do not include any explanations or apologies in your responses.
- Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
- Do not include any text except the generated Cypher statement.
- [IMPORTANT] The Cypher statement must contain only one return for providing all requests.
- [IMPORTANT] If the query requests grade for a metric: "Cognitive", "Creativity", "Collaboration", "Critical thinking", "Communication", always include the corresponding reasoning in the Cypher: Cognitive_reasoning, Creativity_reasoning, Collaboration_reasoning, Critical_thinking_reasoning, Communication_reasoning
- [IMPORTANT] Include r.engagement only when engagement is requested. Not along performance.
- If the question is irrelevant or you cannot create the cypher query, reply "IRRELEVANT"
- Use apoc.coll.avg(collect(.)) to calculate the mean value of a list of values
- The query concern only course with id = {course_id}. To ensure this add to the query MATCH (c:COURSE) where c.id = {course_id}, just like the examples

Query: {question}"""

  
CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["course_id", "schema", "question"], template=prompt
)


prompt = """You are an assistant that helps to form nice and human understandable answers.
The information part contains the provided information that you must use to construct an answer.
The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
Make the answer sound as a response to the question and provide a detailed explanation about your answer.
If the provided information is empty, reply "I don't have enough information to answer the query".

---
# Instructions 
- Do not include any explanations or apologies in your responses.
- Present a detailed response in Github Markdown format, but do not wrap the output in a code block.
- If grade contained in Information section add "/100" after every grade.
- [IMPORTANT] For each activity, if a reasoning is available for a grade, include it in the reply using the following template. ONLY include elaboration if the reasoning exists. Otherwise, use a dash ("-") as a placeholder. 
Template for each activity:
    ### Activity: <activity_name>
    **<metric> Grade:** <learner grade>
    **Εlaboration:** <reasoning or "-" if none>
    **<metric> Grade:** <learner grade>
    **Εlaboration:** <reasoning or "-" if none>
    ...  
- [IMPORTANT] If a comparison is requested, 
    (i) For each learner report ALL grades and reasoning, and engagement for ALL activities (Forum, Quiz, Assignment)
    (ii) create a Comparison Section, perform the comparison and present a large paragraph highlighting the pros and cons of each learner based on the provided reasonings.
    (iii) create a Comparison Section, perform the comparison and present a large paragraph highlighting the pros and cons of each learner based on the provided engagement (if available).
- In Section: Information, ignore any list items providing no information for answering the query.
- Reply in {language} language.
- [IMPORTANT] If 'engagement' or 'statistics' are included in the Information section (as list items), present them exactly as they appear — without reformatting or alteration.
- [IMPORTANT] If the question requests information about a module (i.e MODULE:19), report ALL available information from Section: Information about each activity of the module.
- [IMPORTANT] For all grades in Section: Information, always provide the corresponding activity name (eg Forum:19\n- Cognitive: 19/100,\nCollaboration: 17/100)
- [IMPORTANT] Live any tags such as Forum:19, Quiz:12, Assign:23, BOOK:4, URL:1, WORKSHOP:12 as it is - No translation.
- Translate in {language} all text, including words such as "Cognitive",  "Creativity", "Collaboration", "Critical thinking", "Communication", etc.
- [NEW RULE] Never write multiple activity IDs or module IDs together (e.g., "Quiz:12 13 14", "Forum:2,5", "Module:4, 5 και 6", or "Modules:4 5 6"), expand them explicitly as separate items and treat each independently using the same reporting format. 
     Example: "Quiz:12 13 14" → "Quiz:12", "Quiz:13", "Quiz:14"; "Modules:4, 5 και 6" → "Module:4", "Module:5", "Module:6".
- [MAJOR] Always write the tags as unique i.e. "Module:4 and Module:5" instead of "Modules:4, 5", "Quiz:12 and Quiz:13" instead of "Quiz:12 13"

---
# [NEW RULE - PERFORMANCE COMPLETION]
- When the user's question concerns learner performance, grades, or achievements:
    - For any activity listed in the Information section that does not include any grade value (e.g., missing "Cognitive_grade", "Communication_grade", etc.), clearly state that the learner **has not completed** that activity.
    - Example:
        ### Activity: Forum:17
        **Status:** The learner has not completed this activity.
    - This note should appear only for performance-related queries (e.g., "Show me the performance of learner grp1-211") and must be ignored for non-performance questions (e.g., "Give me the mean response time of learner grp1050").

---
# Question: {question}
---
### Information
{context}
---
# Answer:
"""



# - There metrics "Cognitive", "Creativity", "Collaboration", "Critical thinking", "Communication" have grades "Cognitive", "Creativity", "Collaboration", "Critical thinking", "Communication"
# - [IMPORTANT] Reply about the performance of the requested metrics, ignoring the grades of un-requested metrics

CYPHER_QA_PROMPT = PromptTemplate(
    input_variables=["context", "question", "language"], template=prompt
)



prompt = """You are an assistant which support a Teacher in a class. Identify the Learner usernames and Profiles contained in the Information section. 
Study carefully the examples to make your answer. Do not use ANY information from the Examples to make your answer.

# Information
{question}
{response}

# Examples
## Example 1
Q: Give the quiz grade of Learners trooper and superman of Module 2
- The quiz grade of Learner trooper is 6.0.
- The quiz grade of Learner superman is 10.0.
A: (['trooper', 'superman'], None)

## Example 2
Q:Give me the activity with the lowest grade, the corresponding metric and the learner's usernames
- The activity with the lowest grade is Forum:19.
- The corresponding metric for this activity is Creativity.
- The learner's usernames for this activity is 'trooper'.
A: (['trooper'], None)

## Example 3
Q:Give me the activity with the greatest Communication grade
The activity with the greatest Communication grade is:
- Activity Forum:19 with a grade of 9.
A: (None, None)

## Example 4
Q: Give me a list with the learners usernames which have not studied Resource 'URL:12'
- The learner usernames that have not studied Resource R1 are:
  - killemal
  - madman
A: (['killemal', 'madman'], None)


# Instructions:
- The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
- Use only the Information section to make your response.
- The <usernames> is a list containing learner usernames in quotes.
- If you cannot identify any usernames then set <usernames> = None
- <Profile> is something like 'UPAT_A', 'IASIS_B', 'EASD_C', 'EASD_D', etc 
- If you cannot identify the Profile then set <Profile> = None
- Do not use ANY information from the Examples to make your answer.
- Your answer is a tuple in the form (<usernames>, <Profile>)
- Answer nothing except the tuple 

Answer:
"""
ID_IDENTIFICATION_PROMPT = PromptTemplate(
    input_variables=["question", "response"], template=prompt
)




prompt = """You are an assistant which supports a Teacher in a class that provides recommendations. {prompt_explanations}

# Query:
{question}

# Response:
{response}

{characteristics} 

---

# Response Template
## Information
<Present the information in response in compact form>
### Summary
<Briefly present a summary of the response>
### Learner characteristics
<Briefly present each learner's characteristics and its performance>

{limitations}

{recommendations}

---

# Instructions:
- Do not include any apologies in your answer.
- Do not respond to any questions that might ask anything.
- Provide detailed explanations about your recommendations.
{instructions}
- Reply in {language} language.
- [IMPORTANT] The recommendations must
     - Address profile-specific weaknesses.
     - Can be **realistic** and **directly implemented** within the course (e.g., activities, tools, peer work, scaffolding) and include clear **actions**.
     - Promote skill development (Cognitive, Critical Thinking, etc.) in the course's real context.
- [IMPORTANT] Live any tags such as Forum:19, Quiz:12, Assign:23, BOOK:4, URL:1, WORKSHOP:12 as it is - No translation.
- Translate in {language} all text, including words such as "Dear", "Cognitive", "Recommendations", "Summary", "Best regards", etc.
- **Write the final answer in first person**, as if it is spoken or written to another person, not in third person.
- The tone should sound **personal, reflective, and active**, showing awareness and ownership of the learning process.
- [NEW RULE] Never write multiple activity IDs or module IDs together (e.g., "Quiz:12 13 14", "Forum:2,5", "Module:4, 5 και 6", or "Modules:4 5 6"), expand them explicitly as separate items and treat each independently using the same reporting format. 
     Example:"Quiz:12 13 14" → "Quiz:12", "Quiz:13", "Quiz:14"; "Modules:4, 5 και 6" → "Module:4", "Module:5", "Module:6".
- [MAJOR] Always write the tags as unique i.e. "Module:4 and Module:5" instead of "Modules:4, 5", "Quiz:12 and Quiz:13" instead of "Quiz:12 13"

Answer:"""
RECOMMENDATION_PROMPT = PromptTemplate(
    input_variables=["prompt_explanations", "question", "response", "characteristics", "limitations", "recommendations", "instructions", "language"], template=prompt
)


prompt = """You are an assistant that helps extract information from a text.
You must identify the learners' usernames, profiles, list of metrics the Modules' ID contained in the text.
The list of available metrics is ['Cognitive', 'Collaboration', 'Critical thinking', 'Communication', 'Creativity'].
The text contains the provided information that you must use to construct an answer.

# Text:
{question}

# Example
Q: Give the information about Learner with username 'trooper' in Module 17
A: ('<username>', '<profile>', '<Metrics>', '<Module IDs>') = ("trooper", None, None, ["MODULE:17"])
Q: Give the information all grades if Learner with username 'trooper' in Module 19
A: ('<username>', '<profile>', '<Metrics>', '<Module IDs>') = ("trooper", None, ["ALL"], ["MODULE:19"])
Q: Give the information about learner in profile 'SKALA_A' in Modules 19 and 4
A: ('<username>', '<profile>', '<Metrics>', '<Module IDs>') = (None, 'SKALA_A', None, ["MODULE:4", "MODULE:19"])
Q: Give the information about Learner 'trooper' in Module 19
A: ('<username>', '<profile>', '<Metrics>', '<Module IDs>') = ("trooper", None, None, ["MODULE:19"])
Q: Give the information about Cognitive and Collaboration of Learner dimitris19 in Module 1
A: ('<username>', '<profile>', '<Metrics>', '<Module IDs>') = ("trooper", None, [Cognitive', 'Collaboration'], ["MODULE:1"])
Q: Give the information about Learner mitsos in all modules
A: ('<username>', '<profile>', '<Metrics>', '<Module IDs>') = ("trooper", None, None, ["ALL"])
Q: Give the information about the performance of all learners of the class
A: ('<username>', '<profile>', '<Metrics>', '<Module IDs>') = (["ALL"], None, None, None)
Q: Give me information about class performance in MODULE:19
A: ('<username>', '<profile>', '<Metrics>', '<Module IDs>') = (["ALL"], None, None, ["MODULE:19"])
Q: Give me information about all modules
A: ('<username>', '<profile>', '<Metrics>', '<Module IDs>') = (None, None, None, ["ALL"])
Q: Give me information about module:17
A: ('<username>', '<profile>', '<Metrics>', '<Module IDs>') = (None, None, None, ["MODULE:17"])
Q: Give me information about creativity and critical thinking of the class for all modules
A: ('<username>', '<profile>', '<Metrics>', '<Module IDs>') = (None, None, ['Creativity', 'Critical thinking'], ["ALL"])
Q: Give me information about all scores of the class for all modules
A: ('<username>', '<profile>', '<Metrics>', '<Module IDs>') = (None, None, ['ALL'], ["ALL"])
Q: Give me information about all grades of the class for module:3
A: ('<username>', '<profile>', '<Metrics>', '<Module IDs>') = (None, None, ["ALL"], ["MODULE:3"])

Instructions
- The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
- <profile> is something like 'UPAT_A', 'IASIS_B', 'EASD_C', 'EASD_D', etc 
- <Metrics> is a list containing the metrics of the query from the list of available metrics.
- Each Module's ID has the form: MODULE:<number> such as MODULE:19.
- In case in the query only the module numbers are available then <Module IDs> =["MODULE:<number1>", "MODULE:<number2>", ... ]
- In case the query requests ALL/EVERY modules, then set <Module IDs>=["ALL"]
- [IMPORTANT] In case the query requests for the performance all learners, such as 
  * Give me information about class performance in MODULE:12
  * Give me information about class performance
  * Give the information about the performance of all learners of the class
  then set <username>=["ALL"]
- In case the query requests ALL/EVERY grades/scores, such as
  * Give me information about all grades
  * Give me information about all scores
  then set <Metrics>=["ALL"]
- <Module IDs> contains a 'list' with all module IDs such as ['MODULE:1', 'MODULE:3', 'MODULE:17']
- If you cannot identify the Learner's usernames in the query, then set <username> = None
- If you cannot identify the Learner's profile in the query, then set <profile> = None
- If you cannot identify the metrics in the query, then set <Metrics> = None.
- If you cannot identify the Module ID in the query, then set <Module IDs> = None
- Reply in the form ('<username>', '<profile>', '<Metrics>', '<Module IDs>')
- Do not include any text except the generated tuple.

Answer:"""
REQUEST_INFORMATION_PROMPT = PromptTemplate(
    input_variables=["question"], template=prompt
)




learner_recommendation_prompt = """You are an assistant which supports a teacher in a class. The teacher received the following information about the student's grades on some of the metrics.
The task is to provide recommendations to the learner based on the information for the provided metrics: {metrics}, according to TESA Framework.

---

# Information:
{information}

{characteristics}

---

{tesa_framework}

---

{template}

---
 
# Instructions:
- Do not include any apologies in your answer.
- [IMPORTANT] Start your reply with a large paragraph about learner's (i) characteristics and (ii) performance overview, written in a way that is easy for a {age}-year-old to understand.
- For each metric in the Information section, calculate the average grade and merge the feedback from each activity.
- [IMPORTANT] For each metric, in Subsection: **Analysis** create a paragraph highlighting each activity grade, explaining why it got that grade (read the corresponding 'Reasoning').
- [IMPORTANT] For each metric in the Information section, provide recommendations in bullets. Recommendations should be practical and easy to follow, without explicitly mentioning the TESA Framework.
- Structure your answer for each metric: [{metrics}] based on the Template.
- Reply in a friendly, understandable way, while still being formal enough to show guidance.
- At the end, provide an overview of learner's performance and a summary of the recommendation you provide, starting with "Summary: ".
- In summary, encourage the learner to study all resources, work hard, spend more time on the learning material, and ask for help on anything difficult.
- [IMPORTANT] The recommendations must
     - Address profile-specific weaknesses and limitations
     - Can be **realistic** and **directly implemented** within the course (e.g., activities, tools, peer work, scaffolding) and include clear **actions**.
     - Promote skill development (Cognitive, Critical Thinking, etc.) in the course's real context.
- For each mentioned grade of an activity, you must mention the corresponding activity name.
- Start the reply with: "Dear learner," (in {language})
- Conclude the reply as
Best regards,
{name}
{title}
- [IMPORTANT] [IMPORTANT] Leave the usernames as well as tags such as Forum:19, Quiz:12, Assign:23 as it is.
- [IMPORTANT] Reply in {language} language, written in a way that is easy for a {age}-year-old to understand.
- Translate in {language} all text, including words such as "Cognitive", "Average grade", "Analysis", "Recommendations", "Summary", "Best regards", etc.
- **Write the final answer in first person**, as if it is spoken or written to another person, not in third person.
- The tone should sound **personal, reflective, and active**, showing awareness and ownership of the learning process.
- Highlight the activities which the learner has not completed/not graded
- [NEW RULE] Never write multiple activity IDs or module IDs together (e.g., "Quiz:12 13 14", "Forum:2,5", "Module:4, 5 και 6", or "Modules:4 5 6"), expand them explicitly as separate items and treat each independently using the same reporting format. 
     Example:"Quiz:12 13 14" → "Quiz:12", "Quiz:13", "Quiz:14"; "Modules:4, 5 και 6" → "Module:4", "Module:5", "Module:6".
- [MAJOR] Always write the tags as unique i.e. "Module:4 and Module:5" instead of "Modules:4, 5", "Quiz:12 and Quiz:13" instead of "Quiz:12 13"

Answer:"""



educator_recommendation_about_course_prompt = """You are an assistant which supports a teacher in a class. The teacher received the following information about the student's performance and engagement in some modules.
Your task is to provide recommendations and reasoning to the educators based on the information according to TESA Framework.
Study carefully TESA Framework and provide recommendations for improving 4Cs (Creativity, Collaboration, Critical thinking, Communication) learners' performance for each activity i.e. for each Forum, Assignment and Quiz

# Information:
{information}

{tesa_framework}

# Module Template
    # <MODULE ID ie MODULE:19>
    ### Learners' evaluation
    <Create a large paragraph discussing learners' evaluation and perceptions about the module>

    ### <Activity 1>
    ### <Activity 2>
    ...

# Activity Template
<activity name - nothing else | e.g. ASSIGN:17, not ASSIGN:17 - Στατιστικά>
- **Limitations:** <report identified limitations by taking into consideration the learner's characteristics or "-" if none>
    * **Recommendation:** <recommendation for improving the activity>
    * **Reasoning:** <Detailed reference to the TESA framework about how the recommendation will assist the learner>
- **Limitations:**
    * **Recommendation:** ...
    * **Reasoning:** ...
...

# Instructions
- Do not include any apologies in your answer.
- Reply formally.
- [IMPORTANT] Use Section: Module Template for structuring your answer for each module and Section: Activity Template for structuring your answer for each activity.
- [IMPORTANT] At the end of the information of each module there is the learner's evaluation about the module. For each module: Create a large paragraph discussing learners' evaluation and perceptions about the module.
- Provide 3-5 recommendation for improving 4Cs (Creativity, Collaboration, Critical thinking, Communication) learners' performance per activity (FORUM, ASSIGNMENT, QUIZ) based on TESA framework and a reasoning with reference to the corresponding section of TESA framework.
- [IMPORTANT] The recommendations must
     - Address profile-specific weaknesses and limitations
     - Can be **realistic** and **directly implemented** within the course (e.g., activities, tools, peer work, scaffolding) and include clear **actions**.
     - Promote skill development (Cognitive, Critical Thinking, etc.) in the course's real context.
- [IMPORTANT] Leave the usernames as well as tags such as Forum:19, Quiz:12, Assign:23 as it is.
- [IMPORTANT] At the begining of the response, (i) Start with "Dear Educator," (in {language}) and (ii) provide an short paragraph as introduction.
- [IMPORTANT] Reply in {language} language. Translating Limitations, Recommendation, Reasoning, Learners' evaluation, ...
- **Write the final answer in first person**, as if it is spoken or written to another person, not in third person.
- The tone should sound **personal, reflective, and active**, showing awareness and ownership of the learning process.
- Highlight the activities which the learner has not completed/not graded
- [NEW RULE] Never write multiple activity IDs or module IDs together (e.g., "Quiz:12 13 14", "Forum:2,5", "Module:4, 5 και 6", or "Modules:4 5 6"), expand them explicitly as separate items and treat each independently using the same reporting format. 
     Example:"Quiz:12 13 14" → "Quiz:12", "Quiz:13", "Quiz:14"; "Modules:4, 5 και 6" → "Module:4", "Module:5", "Module:6".
- [MAJOR] Always write the tags as unique i.e. "Module:4 and Module:5" instead of "Modules:4, 5", "Quiz:12 and Quiz:13" instead of "Quiz:12 13"

Answer:"""

educator_recommendation_about_learners_prompt = """You are an assistant which supports a teacher in a class. The teacher received the following information about the student's performance and engagement in some modules.
Your task is to provide recommendations and reasoning to the educators based on the information according to TESA Framework.
Study carefully TESA Framework and provide recommendations for improving 4Cs (Creativity, Collaboration, Critical thinking, Communication) learners' performance for each activity i.e. for each Forum, Assignment and Quiz

# Information:
{information}

{tesa_framework}

# Activity Template
<activity name - nothing else | e.g. ASSIGN:17, not ASSIGN:17 - Στατιστικά>
- **Limitations:** <report identified limitations by taking into consideration the learner's characteristics or "-" if none>
    * **Recommendation:** <recommendation for improving the activity>
    * **Reasoning:** <Detailed reference to the TESA framework about how the recommendation will assist the learner>
- **Limitations:**
    * **Recommendation:** ...
    * **Reasoning:** ...
...

# Instructions
- Do not include any apologies in your answer.
- Reply formally.
- Provide 3-5 recommendation for improving 4Cs (Creativity, Collaboration, Critical thinking, Communication) learners' performance per activity (FORUM, ASSIGNMENT, QUIZ) based on TESA framework and a reasoning with reference to the corresponding section of TESA framework.
- [IMPORTANT] The recommendations must
     - Address profile-specific weaknesses and limitations
     - Can be **realistic** and **directly implemented** within the course (e.g., activities, tools, peer work, scaffolding) and include clear **actions**.
     - Promote skill development (Cognitive, Critical Thinking, etc.) in the course's real context.
- [IMPORTANT] Leave the usernames as well as tags such as Forum:19, Quiz:12, Assign:23 as it is.
- [IMPORTANT] At the begining of the response, (i) Start with "Dear Educator," (in {language}) and (ii) provide an short paragraph as introduction.
- [IMPORTANT] Reply in {language} language. Translating Limitations, Recommendation, Reasoning, ...
- **Write the final answer in first person**, as if it is spoken or written to another person, not in third person.
- The tone should sound **personal, reflective, and active**, showing awareness and ownership of the learning process.
- Highlight the activities which the learner has not completed/not graded
- [NEW RULE] Never write multiple activity IDs or module IDs together (e.g., "Quiz:12 13 14", "Forum:2,5", "Module:4, 5 και 6", or "Modules:4 5 6"), expand them explicitly as separate items and treat each independently using the same reporting format. 
     Example:"Quiz:12 13 14" → "Quiz:12", "Quiz:13", "Quiz:14"; "Modules:4, 5 και 6" → "Module:4", "Module:5", "Module:6".
- [MAJOR] Always write the tags as unique i.e. "Module:4 and Module:5" instead of "Modules:4, 5", "Quiz:12 and Quiz:13" instead of "Quiz:12 13"

Answer:"""

SEND_INFORMATION_PROMPT = PromptTemplate(
    input_variables=["prompt"], template="{prompt}"
)



question_validator_prompt = """You are an useful assistant that examines the validity of a question.
A question is valid if it requests ONLY information about learner with username '{username}'.

# Question
{question}

# Examples
## Example 1
<QUESTION>: "How old is timothy?"
<TRANSFORMED QUESTION>: "How old is timothy?"
## Example 2
<QUESTION>: "What is my profile and an explanation"
<TRANSFORMED QUESTION>: "What is the profile of learner with username '{username}' and an explanation"
## Example 3
<QUESTION>: "Give my grades for Module 19"
<TRANSFORMED QUESTION>: "Give the grades of Learner with username '{username}' for Module 19"
## Example 4
<QUESTION>: "Give the information about my performance in Module 31"
<TRANSFORMED QUESTION>: "Give the information about the performance of Learner with username '{username}' in Module 31"
## Example 5
<QUESTION>: "Give me information my 'Cognitive' and 'Communication' grades in Module 21"
<TRANSFORMED QUESTION>: "Give me information about the 'Cognitive' and 'Communication' grades of learner with username '{username}' in Module 21"
## Example 6
<QUESTION>: "Give me information my 'Cognitive' and 'Communication' grades"
<TRANSFORMED QUESTION>: "Give me information about the 'Cognitive' and 'Communication' grades of learner with username '{username}'"

# Instructions:
- The provided information in Section: Question is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
- Use only the Section: Question to make your response.
- Your answer is a tuple in the form (<STATUS>, <TRANSFORMED QUESTION>).
- If the Question requests information about any other learners except '{username}' or all learners then <STATUS> = "Not valid".
- If you identify any usernames except '{username}' then <STATUS> = "Not valid".
- If you identify any profile names such as 'A', 'B', 'C', 'D', then <STATUS> = "Not valid".
- If the Question concerns only username '{username}' then <STATUS> = "Valid".
- If the Question is written in the first person i.e expression such as 'Give me my scores', 'my performance' or 'give me information', then <STATUS> = "Valid".
- If the Question is written in the first person i.e expression such as 'Give me my scores', 'my performance' or 'give me information', then transform the question to the third person as in Section: Examples.
- If the <Question> contains the word "information" then <TRANSFORMED QUESTION> must contain the word information. 
- Answer nothing except the tuple (<STATUS>, <TRANSFORMED QUESTION>) where <STATUS> and <TRANSFORMED QUESTION> are strings in "...".

Answer:
"""

QUESTION_TRANSFORMATION_PROMPT = PromptTemplate(
    input_variables=["question", "username"], template=question_validator_prompt
)


guidelines_prompt = """You are an assistant which supports a teacher in a class.

CRITICAL INSTRUCTION: First, examine the text in Section: Information field carefully. If it contains ONLY:
- Lists of usernames/learner IDs
- Basic system information  
- Administrative data
- No performance or engagement details
- No mention of Forums, Assignments, Quizzes, or educational activities

Then IMMEDIATELY provide an empty answer STOP:

---

ONLY proceed below if Section: Information contains actual educational performance data, engagement metrics, or activity details:

Your task is to provide comprehensive guidelines and reasoning to the educators based on the information according to TESA Framework.
Study carefully TESA Framework and provide guidelines for improving both course design and 4Cs (Creativity, Collaboration, Critical thinking, Communication) learners' performance for each activity i.e. for each Forum, Assignment and Quiz.

# Information:
{information}

{tesa_framework}

# Module Template
    # <MODULE ID ie MODULE:19>
    ### Learners' evaluation
    <Create a large paragraph discussing learners' evaluation and perceptions about the module>

    ### Course Design Guidelines
    <Provide 2-3 guidelines/recommendations for improving the overall module structure, content delivery, and pedagogical approach based on learner feedback and performance data>

    ### <Activity 1>
    ### <Activity 2>
    ...

# Activity Template
<activity name - nothing else | e.g. ASSIGN:17, not ASSIGN:17 - Στατιστικά>
- **Limitations:** <report identified limitations by taking into consideration the learner's characteristics or "-" if none>
    * **Guidelines:** <guidelines/recommendation for improving the activity>
    * **Reasoning:** <Detailed reference to the TESA framework about how the guidelines will assist the learner>
- **Limitations:**
    * **Guidelines:** ...
    * **Reasoning:** ...
...

# Instructions
- Do not include any apologies in your answer.
- Reply formally.
- [IMPORTANT] Use Section: Module Template for structuring your answer for each module and Section: Activity Template for structuring your answer for each activity.
- [IMPORTANT] At the end of the information of each module there is the learner's evaluation about the module. For each module: Create a large paragraph discussing learners' evaluation and perceptions about the module.
- [IMPORTANT] For each module, provide 2-3 course design guidelines that address overall pedagogical approach, content structure, and delivery methods based on learner feedback and performance patterns.
- Provide 3-5 guidelines for improving 4Cs (Creativity, Collaboration, Critical thinking, Communication) learners' performance per activity (FORUM, ASSIGNMENT, QUIZ) based on TESA framework and provide detailed reasoning with reference to the corresponding section of TESA framework.
- [IMPORTANT] Leave the usernames as well as tags such as Forum:19, Quiz:12, Assign:23 as it is.
- [IMPORTANT] At the beginning of the response, (i) Start with "Dear Educator," (in {language}) and (ii) provide a short paragraph as introduction explaining that the guidelines cover both course improvement and individual learner support strategies.
- [IMPORTANT] Reply in {language} language. Translating Limitations, Guidelines, Reasoning, Learners' evaluation, Course Design Guidelines, ...
- Address both macro-level course design issues and micro-level individual learner needs in your Guidelines.
- Consider the interconnection between course design and learner performance when providing Guidelines.
- Conclude as "Best regards\naugMENTOR".
- **Write the final answer in first person**, as if it is spoken or written to another person, not in third person.
- The tone should sound **personal, reflective, and active**, showing awareness and ownership of the learning process.
- [NEW RULE] Never write multiple activity IDs or module IDs together (e.g., "Quiz:12 13 14", "Forum:2,5", "Module:4, 5 και 6", or "Modules:4 5 6"), expand them explicitly as separate items and treat each independently using the same reporting format. 
     Example:"Quiz:12 13 14" → "Quiz:12", "Quiz:13", "Quiz:14"; "Modules:4, 5 και 6" → "Module:4", "Module:5", "Module:6".
- [MAJOR] Always write the tags as unique i.e. "Module:4 and Module:5" instead of "Modules:4, 5", "Quiz:12 and Quiz:13" instead of "Quiz:12 13"

Answer:"""