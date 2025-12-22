import ast
import json
import openai
from utils.neo4j_connection import Neo4jConnection
from utils.utils import tesa_framework

with open("Resources/profiles_description.json", "r", encoding="utf-8") as file:
    d_profiles_description = json.load(file)

def get_grades(
    course_id: int = None, graph: Neo4jConnection = None, metric: str = None
):
    """
        Retrieves the grades of learners for a given course based on a specified metric.

        Args:
            course_id (int, optional): The ID of the course for which grades are retrieved.
            graph (Neo4jConnection, optional): The Neo4j database connection.
            metric (str, optional): The specific metric to be used for grading.

        Returns:
            dict: A dictionary containing profiles as keys and lists of grades for each module.
    """
    profiles = graph.query(f"""MATCH (l:LEARNER)-[r]->(p:PROFILE)
                where r.course_id = {course_id}
                return collect(distinct p.name) as profiles""")[0]["profiles"]
    profiles.sort()

    response = graph.query(f"""MATCH (l:LEARNER)-[]->(p:PROFILE)
                MATCH (l)-[]->(c:COURSE)-[]->(m:MODULE)-[]->(a:ACTIVITY)
                MATCH (l)-[r]->(a)
                where c.id = {course_id}
                return m.id as module_id, m.code as module_code, m.title as module_title, p.name as profile, round(apoc.coll.avg(collect(r.{metric}_grade)),1) as grade
                order by m.id, p.name""")

    d = {}
    for item in response:
        if item["module_id"] not in d:
            d[item["module_id"]] = {
                "code": item["module_code"],
                "title": item["module_title"],
            }
        d[item["module_id"]][item["profile"]] = item["grade"]

    for key in d:
        for profile in profiles:
            if profile not in d[key]:
                d[key][profile] = None

    # Get grades
    xticks = []
    grades = {}
    for profile in profiles:
        grades[profile] = []
    for key, value in d.items():
        xticks.append(f"{value['code']}\n {value['title']}")
        for profile in profiles:
            grades[profile].append(value[profile])
    return grades




def generate_policy_recommendations(
    information: str = None, profiles_description: str=None, course_description: str = None, openai_settings: dict = None, language: str = "English"
):
    """
        Generates policy recommendations for improving the educational process based on learner performance 
        and augMENTOR profile characteristics.

        Args:
            information (str): The grades and performance data of learners categorized by augMENTOR profiles.
            profiles_description (str): augMENTOR profiles description.
            openai_settings (dict): A dictionary containing OpenAI API settings, including model name and temperature.
            language (str, optional): The language in which the response should be generated. Defaults to "English".

        Returns:
            str: A structured policy recommendation report based on the provided information.
    """


    prompt = """You are an intelligent assistant that assists a policy maker to generate policies about an educational institution. 
The learners are classified in categories called "augMENTOR profiles" based on their characteristics and skills. 
- Section: Information provides the grades of each augMENTOR profile at skill: Cognitive, and 21st century skills: Critical Thinking, Communication, Collaboration and Creativity
- Section: augMENTOR profiles characteristics provides the characteristics and skills of each profile.
Your task is to generate policy recommendations for improving the educational process, outcomes and learners' skills based on the information according to TESA Framework.

# Information
{information}

# augMENTOR profiles characteristics
{profiles_description}

# Template
{
"Section1": {
    "<augMENTOR profile1>": "- **Analysis**: <findings based their performance>\n- **Key Observations**:\n  - Strengths: <strengths>\n  - Weaknesses: <weaknesses>",
    "<augMENTOR profile2>": "- **Analysis**: <findings based their performance>\n- **Key Observations**:\n  - Strengths: <strengths>\n  - Weaknesses: <weaknesses>", ...
},
"Section2": {
    "<augMENTOR profile1>": "🟢 <Introductory paragraph highlighting that the recommendations aim to guide the design of future learning experiences for learners with similar characteristics, start with 'Policy recommendation: Future courses should ...'>\n\n**Guidelines on the recommendation:**\n- **<policy title>**: <policy recommendation tailored to the augMENTOR profile and aligned with course based on TESA framework>\n- **<policy title>**: <policy recommendation tailored to the augMENTOR profile and aligned with course>\n- **<policy title>**: <policy recommendation tailored to the augMENTOR profile and aligned with course> ...",
    "<augMENTOR profile2>": "🟢 <Introductory paragraph highlighting that the recommendations aim to guide the design of future learning experiences for learners with similar characteristics, start with 'Policy recommendation: Future courses should ...'>\n\n**Guidelines on the recommendation:**\n- **<policy title>**: <policy recommendation tailored to the augMENTOR profile and aligned with course based on TESA framework>\n- **<policy title>**: <policy recommendation tailored to the augMENTOR profile and aligned with course>\n- **<policy title>**: <policy recommendation tailored to the augMENTOR profile and aligned with course> ...", ...
},
"Section3": {
    "<augMENTOR profile1>": "🟢 <Introductory paragraph highlighting that the recommendations aim to guide educators in structuring future courses to support learners with similar characteristics, start with 'Policy recommendation: Educators should be ...'>\n\n**Guidelines on the recommendation:**\n- **<policy title>**: <educator-focused course-aligned recommendation>\n- **<policy title>**: <educator-focused course-aligned recommendation based on TESA framework>\n- **<policy title>**: <educator-focused course-aligned recommendation> ...",
    "<augMENTOR profile2>": "🟢 <Introductory paragraph highlighting that the recommendations aim to guide educators in structuring future courses to support learners with similar characteristics, start with 'Policy recommendation: Educators should be ...'>\n\n**Guidelines on the recommendation:**\n- **<policy title>**: <educator-focused course-aligned recommendation>\n- **<policy title>**: <educator-focused course-aligned recommendation based on TESA framework>\n- **<policy title>**: <educator-focused course-aligned recommendation> ...", ...
},
"Section4": "<Summarize the findings from the data analysis, the implemented policies, and their outcomes in two paragraphs>"
}

{course_description}

{tesa_framework}

# Instructions
- Use Section: Template to structure your reply.
- [IMPORTANT] Your response must be a valid Python dictionary, with no extra text, explanations, or formatting outside the dictionary itself.
- [IMPORTANT] Detailed reference to the TESA framework about the reasoning behind the recommendations.
- Follow the steps described in Section: Strategy for making your reply.
- Use 'learner' and 'educator' instead of 'student' and 'teacher'.
- Tailor all recommendations to the actual course described.
- Reply in {language}.

# Strategy
1. **Analyze Skill Performance**:
   - Examine each augMENTOR profile's performance across Cognitive and 21st Century Skills to identify strengths and weaknesses.

2. **Profile Characteristic Matching**:
   - Align performance results with the characteristics and inherent tendencies of each profile to diagnose causes behind high or low performance.

3. **Contextualize Within Course Design**:
   - Carefully analyze the course description (learning outcomes, content, delivery mode, assessment, tools) to understand what it demands from the learner and the educator.

4. **Study TESA framework**
   - Read carefully the tesa framework to learn guidelines about educational process.

5. **Section1 – Needs Assessment**:
   - Identify which specific course demands may challenge each profile based on their weaknesses and traits.
   - Document key performance patterns and translate them into actionable educational needs.
   - [IMPORTANT] Use passive voice
   
6. **Section2 – Learner-Focused Policy Recommendations**:
    - For each augMENTOR profile, recommend 3–5 **targeted, forward-looking interventions** that:
     - Address profile-specific weaknesses.
     - Can inform the **design of future courses** (e.g., activities, tools, peer work, scaffolding).
     - Promote skill development (Cognitive, Critical Thinking, etc.) in the context of similar future learning environments.
   - All policies must:
     - be **concrete, contextual, and measurable**.
     - Based on TESA framework with detailed reference to the corresponding section of TESA framework.
     - 🟢Precede the list of policy recommendations with a large introductory paragraph, starting with 'Policy recommendation: Future courses should ...', that emphasizes how the policies aim to guide future course design for learners with similar characteristics and provides a summary of the bullet points
     - [IMPORTANT] Use passive voice
     
7. **Section3 – Educator-Focused Policy Recommendations**:
     - Generate 7 highly specific, **forward-looking strategies** for educators to support each profile in the design and facilitation of future courses.
     - Examples: Adjust lesson plans, introduce formative micro-assessments, create peer-learning loops, change timing/sequencing, use rubrics or tools, modify communication patterns.
   - All policies must:
     - Be **realistic and implementable** in comparable future courses.
     - Include clear **actions**, **timing** (e.g., weekly, per module), and **methods**.
     - Explicitly target the **profile's weak skills** and leverage strengths.
     - Based on TESA framework with detailed reference to the corresponding section of TESA framework in the form eg: (TESA Phase E: Activities for Implementation in the Classroom)
     - 🟢Precede the list of recommendations with a large introductory paragraph, start with 'Policy recommendation: Educators should be ...', that emphasizes how the strategies aim to guide educators in structuring future courses for learners with similar characteristics and provides a summary of the bullet points
     - [IMPORTANT] Use passive voice
     
8. **Section4 – Summary**:
   - Provide two-paragraph synthesis of:
     - What the performance data reveals about learning needs.
     - How the proposed policies address those needs within the course structure.
     - Projected positive impact on learner engagement, skill acquisition, and overall outcomes.
"""
    prompt = prompt.replace("{language}", language)
    prompt = prompt.replace("{information}", information)
    prompt = prompt.replace("{profiles_description}", profiles_description)
    prompt = prompt.replace("{course_description}", course_description)
    prompt = prompt.replace("{tesa_framework}", tesa_framework)

    # Define the messages to send to the model
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
    ]

    # Make a request to the OpenAI API
    response = openai.ChatCompletion.create(
        model=openai_settings["model_name"],
        messages=messages,
        max_tokens=4*4096,
        temperature=openai_settings["temperature"],
    )

    return response.choices[0].message["content"].strip()


def get_policy_recommendations(graph:Neo4jConnection=None, pilot:str=None, course_id:int=None, openai_settings:dict=None, language:str="English")->str:
    """
        Generates policy recommendations based on student performance in cognitive and 21st-century skills.

        Args:
            graph (Neo4jConnection, optional): The Neo4j database connection.    
            pilot (str, optional): The pilot program identifier (e.g., "UPAT"). Defaults to None.
            course_id (int, optional): The course identifier for retrieving grade data. Defaults to None.
            openai_settings (dict): A dictionary containing OpenAI API settings, including model name and temperature.
            language (str, optional): The language in which the response should be generated. Defaults to "English".

        Returns:
            str: A detailed policy recommendation report including general feedback, learner profile discussions, 
                insights about performance, and recommendations for learners, educators, and course providers.

        Steps:
            1. Retrieves student grades for various skills (Cognitive, Creativity, Collaboration, Critical Thinking, Communication).
            2. Gathers profile descriptions for learners.
            3. Uses AI to generate policy recommendations based on the gathered data.
            4. Formats and returns a structured response with insights and recommendations.
    """
    # Step 1: Retrieve information about grades on 4Cs and Cognitive
    # ------------------------------------------------------------
    print("[INFO] Step 1: Retrieve information about grades on 4Cs and Cognitive")
    information = ""
    for metric in ["Cognitive", "Creativity", "Collaboration", "Critical_thinking", "Communication"]:
        
        if pilot == "UPAT" and metric in ["Collaboration", "Communication"]: continue
        grades = get_grades(course_id=course_id, graph=graph, metric=metric)

        information += f"For skill: {metric}, the grades of each augMENTOR profile are\n"
        information += str(grades) + "\n"

    # Step 2: Retrieve information about grades on 4Cs and Cognitive
    # ------------------------------------------------------------
    print("[INFO] Step 2: Retrieve course description")
    course_description = graph.query(f"MATCH (c:COURSE) where c.id = {course_id} return c.description as description")[0]['description']
    if course_description:
        course_description += f"# Course Description\n{course_description}\n"
    else:
        print("[WARNING] Course description is not available")
        
    # Step 3: Retrive profiles descriptions
    # ------------------------------------------------------------
    print("[INFO] Step 3: Retrive profiles descriptions")
    profiles_description = "\n".join([f"{profile}: {values['short_description']}" for profile, values in d_profiles_description[pilot].items()])

    # Step 4: Get policy recommendation
    # ------------------------------------------------------------
    print("[INFO] Step 4: Get policy recommendation")
    response = generate_policy_recommendations(information=information, profiles_description=profiles_description, course_description=course_description, openai_settings=openai_settings, language=language)
    response = ast.literal_eval(response)
    
    # Step 5: Generate response
    # ------------------------------------------------------------
    structure_response = []
    print("[INFO] Step 5: Generate response")
    # Part 1: General feedback
    information = "## General feedback\n"
    content = f"In summary, the analysis of the augMENTOR profiles reveals distinct strengths and weaknesses across cognitive and 21st-century skills. {response['Section4']}\n\n"
    information += content
    structure_response += [{"title": "General feedback", "content": content.strip()}]
    # Part 2: Discussion about learners' profiles
    information += "## Discussion about learners' profiles\n"
    content = ""
    for profile, values in d_profiles_description[pilot].items():
        content += f"### augMENTOR profile: {profile}\n"
        content += f"**Characteristics:** {values['short_description']}\n\n"
        content += f"**Description:** {values['description']}\n"
    information += content + "\n"
    structure_response += [{"title": "Discussion about learners' profiles", "content": content.strip()}]
    # Part 3: Insights about performance
    information += "## Insights about performance\n"
    content = ""
    for i, profile in enumerate(response['Section1']):
        content += f"### #{i+1} Learners with {d_profiles_description[pilot][profile]['short_description'].lower()}\n"
        content += f"(augMENTOR profile: {profile})\n\n"
        content += f"{response['Section1'][profile]}\n"
    information += content + "\n"
    structure_response += [{"title": "Insights about performance", "content": content.strip()}]
    # Part 4: Policy recommendations for supporting learners
    information += "## Policy recommendations for supporting learners\n"
    content = ""
    for i, profile in enumerate(response['Section2']):
        content += f"#### #{i+1} Supporting learners with {d_profiles_description[pilot][profile]['short_description'].lower()}\n"
        content += f"{response['Section2'][profile]}\n"
    information += content + "\n"
    structure_response += [{"title": "Policy recommendations for supporting learners", "content": content.strip()}]    
    # Part 5: Policy recommendations for supporting educators and course providers
    information += "## Policy recommendations for supporting educators and course providers\n"
    content = ""
    for i, profile in enumerate(response['Section3']):
        content += f"### #{i+1} Supporting learners with {d_profiles_description[pilot][profile]['short_description'].lower()}\n"
        # information += f"(augMENTOR profile: {profile})\n\n"
        content += f"{response['Section3'][profile]}\n"        
    information += content + "\n"
    structure_response += [{"title": "Policy recommendations for supporting educators and course providers", "content": content.strip()}]    

    return information, structure_response