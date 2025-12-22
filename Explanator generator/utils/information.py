import numpy as np
from langchain.graphs import Neo4jGraph
from utils.utils import calculate_trent, available_metrics, format_time, get_indicator_emoji, get_color_indicator, get_performance_emoji
from utils.translations import terms

def get_activity_metrics(activity_id:str=None, graph: Neo4jGraph = None):
    """
    Retrieve the available grading metrics for a specific activity from a Neo4j graph.

    This function queries the Neo4j graph to find all relationship properties between
    learners and a specified activity. It then checks which predefined grading metrics
    exist for that activity and returns a cleaned list of those metrics.

    Parameters:
        activity_id (str): The unique identifier of the activity to query.
        graph (Neo4jGraph): An instance of a Neo4jGraph connection used to run queries.

    Returns:
        List[str]: A list of metric names (e.g., 'Cognitive', 'Creativity') 
                   that exist for the activity.
    """
    # Get all property names of each activity node
    property_names = graph.query(f"""
    MATCH (l:LEARNER)-[r]->(a:ACTIVITY)
    WHERE a.id = "{activity_id}"
    WITH a.id AS activity_id,
        collect(DISTINCT keys(r)) AS all_keys
    RETURN reduce(props = [], keyList IN all_keys | 
                props + [k IN keyList WHERE NOT k IN props]) AS property_names
    """)[0]['property_names']

    # Define properties to check
    target_properties = [
        "Cognitive_grade",
        "Creativity_grade", 
        "Communication_grade",
        "Critical_thinking_grade",
        "Collaboration_grade"
    ]

    # Check which properties exist
    return [prop.replace("_grade","").replace("_", " ") for prop in target_properties if prop in property_names]


def get_learner_information_per_module(
    graph: Neo4jGraph = None,
    course_id: int = None,
    username: str = None,
    module: str = None,
    requested_metrics: list = None,
    language:str="english"
) -> (str, str):
    """
    Get information about learner's performance on a Module by conducting a series of queries

    Parameters
    ----------
    graph: (Neo4jGraph)
        Neo4j graph
    course_id: (str)
        Course Id
    username: (str)
        Learner's username
    module_ID: (str)
        Module's ID
    requested_metrics: (list)
        List with grades of requested metrics
    language: (str)
        response language
        
    Returns
    -------
    text containing the grades of the learner (str)
    text containing information for the learner (str)
    """
    requested_metrics = requested_metrics or [
        "Cognitive",
        "Creativity",
        "Collaboration",
        "Critical thinking",
        "Communication",
    ]
    
    # Grades
    query = f"""
    MATCH (l:LEARNER)-[]->(c:COURSE)
    MATCH (l)-[r:PARTICIPATE]->(a:ACTIVITY)<-[:HAS_ACTIVITY]-(m:MODULE)<-[:HAS_MODULE]-(c)
    WHERE l.username = "{username}" AND m.code = "{module}" AND c.id = {course_id} 
    RETURN a.id as activity_id, a.type as type, 
    r.Cognitive_grade as Cognitive_grade, r.Creativity_grade as Creativity_grade, r.Collaboration_grade as Collaboration_grade, r.Communication_grade as Communication_grade, r.Critical_thinking_grade as Critical_thinking_grade,
    r.Cognitive_reasoning as Cognitive_reasoning, r.Creativity_reasoning as Creativity_reasoning, r.Collaboration_reasoning as Collaboration_reasoning, r.Communication_reasoning as Communication_reasoning, r.Critical_thinking_reasoning as Critical_thinking_reasoning,
    r.engagement as engagement"""
    
    try:
        grades = graph.query(query)
    except Exception as e:
        print(f"[ERROR] Erron in retrieving Learner's grades from the database ({e})")
        return "", ""
    
    # Re-structure dictionary with grades (only for requested indicators)
    grades = {
        item["activity_id"]: {
            "type": item["type"],
            "Cognitive": item["Cognitive_grade"],
            "Creativity": item["Creativity_grade"],
            "Collaboration": item["Collaboration_grade"],
            "Communication": item["Communication_grade"],
            "Critical thinking": item["Critical_thinking_grade"],
            "Cognitive_reasoning": item["Cognitive_reasoning"],
            "Creativity_reasoning": item["Creativity_reasoning"],
            "Collaboration_reasoning": item["Collaboration_reasoning"],
            "Communication_reasoning": item["Communication_reasoning"],
            "Critical thinking_reasoning": item["Critical_thinking_reasoning"],
            "engagement": item["engagement"]
        }
        for item in grades
    }
    # Exclude metrics
    for metric in available_metrics:
        if metric not in requested_metrics:
            for activity_id in grades:
                del grades[activity_id][metric]
    # Sanity check
    if grades == {}:
        return "", ""
   
    # Get SCORM information
    query = f"""MATCH (c:COURSE)-[:HAS_MODULE]->(m:MODULE)-[:HAS_RESOURCE]->(res:RESOURCE)
WHERE c.id = {course_id} AND m.code = "{module}" AND res.id CONTAINS "SCORM"
MATCH (l:LEARNER)-[]->(c)
WHERE l.username = "{username}"
OPTIONAL MATCH (l)-[r]->(res)
RETURN res.id AS scorm_id, 
       r.number_of_submissions AS number_of_submissions, 
       r.time AS time, 
       r.session_time AS session_time, 
       r.status AS status"""
    material =  graph.query(query)   

    
    # Get resources
    query = f"""MATCH (l:LEARNER)-[]->(c:COURSE)
    MATCH (c)-[:HAS_MODULE]->(m:MODULE)-[:HAS_RESOURCE]->(r:RESOURCE)
    WHERE c.id = {course_id} AND m.code = "{module}" AND l.username = "{username}" AND NOT (l)-[:STUDY]->(r)
    RETURN collect(DISTINCT {{id: r.id}}) as Resources
    """
    not_studied_resources = graph.query(query)[0]['Resources']


    # Create Response (for educator) - ENHANCED VERSION
    # -------------------------------------------------------------------------------------------------
    grades_report = ""
    for activity_id, values in grades.items():
        grades_report += f"## {activity_id}\n\n"            

        # PART I: Include grades on Cognitive and 4Cs
        # -------------------------------------------------------------------------------------------
        activity_report = ""
        for metric in requested_metrics:
            if values[metric]:
                if values[f"{metric}_reasoning"]:
                    reasoning_text = f"*{values[f'{metric}_reasoning'].strip()}*"
                else:
                    reasoning_text = " - "
                activity_report += f"| {get_indicator_emoji(metric)} {terms[metric][language]} | {get_color_indicator(values[metric])} {values[metric]:.1f}% | {reasoning_text} |\n"
        
        if activity_report:
            grades_report += f"### 📊 **{terms['Performance'][language]}**\n"
            grades_report += f"| {terms['Indicator'][language]} | {terms['Score'][language]} | {terms['Reasoning'][language]} |\n"
            grades_report += "|----------|------------|-----------|\n"
            grades_report += activity_report
        else:
            grades_report += f"### 📊 **{terms['Performance'][language]}**\n"
            grades_report += f"| {terms['Indicator'][language]} | {terms['Score'][language]} | {terms['Reasoning'][language]} |\n"
            grades_report += "|----------|------------|-----------|\n"
            for metric in  get_activity_metrics(activity_id=activity_id, graph=graph):
                grades_report += f"| {get_indicator_emoji(metric)} {terms[metric][language]} | - | - |\n"                    
        grades_report+="\n\n"
        
        if grades[activity_id]['engagement'] and len(requested_metrics) == 5:
            grades_report += f"### 📊 **{terms['Participation profile'][language]}**\n"
            grades_report += grades[activity_id]['engagement']

    # PART II: Include information from SCORM
    # -------------------------------------------------------------------------------------------
    if material != []: 
        grades_report += f"\n### 📚 **{terms['Course Material Progress'][language]}**\n\n"
        
        # Create table header with language support
        if language == "greek":
            grades_report += "| Υλικό | Κατάσταση | Υποβολές | Χρόνος Συνεδρίας | Συνολικός Χρόνος |\n"
            grades_report += "|-------|-----------|----------|------------------|------------------|\n"
        elif language == "serbian":
            grades_report += "| Materijal | Status | Prijave | Vreme Sesije | Ukupno Vreme |\n"
            grades_report += "|-----------|--------|---------|--------------|---------------|\n"
        else:  # default to english
            grades_report += "| Material | Status | Submissions | Session Time | Total Time |\n"
            grades_report += "|----------|--------|-------------|--------------|------------|\n"
        
        
            
        for item in material:
            # Handle None values and status indicators
            if item['status'] is None:
                status_text = f"❌ {terms['Not read'][language]}"
            elif item['status'] == "Completed":
                status_text = f"✅ {terms['Completed'][language]}"
            else:  #  or other status
                status_text = f"🔄 {terms['Not completed'][language]}"
                        
            # Format the material name (extract from scorm_id if it contains a link)
            material_name = item['scorm_id']
            if '[' in material_name and ']' in material_name:
                # Extract title from markdown link format
                start = material_name.find('[') + 1
                end = material_name.find(']')
                material_name = material_name[start:end] if start > 0 and end > start else material_name
            
            # Handle None values for numeric fields
            submissions = item['number_of_submissions'] if item['number_of_submissions'] is not None else 0
            session_time = item['session_time'] if item['session_time'] is not None else 0
            total_time = item['time'] if item['time'] is not None else 0
            
            # Build table row
            if not item['status']:
                grades_report += f"| 📄 **{material_name}** | {status_text} | - | - | - |\n"
            else:    
                grades_report += f"| 📄 **{material_name}** | {status_text} | {submissions} | {format_time(session_time, language)} | {format_time(total_time, language)} |\n"
        
        grades_report += "\n\n"

    # PART III: Include information about non-studied resources
    # -------------------------------------------------------------------------------------------
    if len(not_studied_resources) > 0:
        grades_report += f"\n### ⚠️ {terms['Non studied resources'][language]}\n"
        for item in not_studied_resources:
            grades_report += f"- 📋 {item['id']}\n"
    grades_report += "\n"


    # Create Response (for retrieving recommendation)
    # -------------------------------------------------------------------------------------------------
    information_text = ""
    for activity_id, values in grades.items():
        information_text += f"## {activity_id}\n"

        # PART I: Include grades on Cognitive and 4Cs
        # -------------------------------------------------------------------------------------------
        activity_report = ""
        for metric in requested_metrics:
            if grades[activity_id][metric]:
                activity_report += f"  - {metric} grade: {grades[activity_id][metric]:.1f}/100" 
                # Include Rubrics
                if grades[activity_id][f"{metric}_reasoning"]:
                    activity_report += " (Reasoning: " + grades[activity_id][f"{metric}_reasoning"].strip() + ")"
                activity_report += "\n"
                       
        if activity_report: 
            information_text += activity_report
        else:
            for metric in  get_activity_metrics(activity_id=activity_id, graph=graph):
                information_text += f"  - {metric} grade: Learner has not been graded/Not completed the task\n"
        information_text += "\n"
         
        if grades[activity_id]['engagement'] and len(requested_metrics) == 5:
            information_text += "\n" + grades[activity_id]['engagement']
                    
    # Information about course material TODO
    if material != []: 
        information_text += "\nInformation about course material\n"
    for item in material:
        information_text += f"  - {item['scorm_id']}\n"
        if item['status']:
            information_text += f"    Status: {item['status']}\n"
            information_text += f"    Number of submissions: {item['number_of_submissions']}\n"
            information_text += f"    Session time: {format_time(item['session_time'], language)}\n"
            information_text += f"    Total time: {format_time(item['time'], language)}\n"
        else:
            information_text +=  "    Not read\n"
        
    # Get learner's not studied resources for this module
    if len(not_studied_resources) > 0:
        information_text += "\nNon studied resources\n"
        for item in not_studied_resources:
            information_text += f"  - {item['id']}\n"    


    return grades_report + "---\n\n", information_text


def get_profile_information_per_module(
    graph: Neo4jGraph = None,
    course_id: int = None,
    profile: str = None,
    module: str = None,
    requested_metrics: list = None,
    language:str="english"
) -> (str, str):
    """
    Get information about learner's performance on a Module by conducting a series of queries

    Parameters
    ----------
    graph: (Neo4jGraph)
        Neo4j graph
    course_id: (str)
        Course Id
    profile: (str)
        augMENTOR profile
    module_ID: (str)
        Module's ID
    requested_metrics: (list)
        List with grades of requested metrics
    language: (str)
        response language
        
    Returns
    -------
    text containing the grades of the learner (str)
    text containing information for the learner (str)
    """
    requested_metrics = requested_metrics or [
        "Cognitive",
        "Creativity",
        "Collaboration",
        "Critical thinking",
        "Communication",
    ]
    # Grades
    query = f"""
    MATCH (l:LEARNER)-[]->(c:COURSE)
    match (l)-[]->(p:PROFILE)
    MATCH (l)-[r:PARTICIPATE]->(a:ACTIVITY)<-[:HAS_ACTIVITY]-(m:MODULE)<-[:HAS_MODULE]-(c)
    WHERE p.name = "{profile}"  AND m.code = "{module}" AND c.id = {course_id} 
    RETURN a.id as activity_id, apoc.coll.avg(collect(r.Cognitive_grade)) as Cognitive_grade, apoc.coll.avg(collect(r.Creativity_grade)) as Creativity_grade, apoc.coll.avg(collect(r.Collaboration_grade)) as Collaboration_grade, apoc.coll.avg(collect(r.Communication_grade)) as Communication_grade, apoc.coll.avg(collect(r.Critical_thinking_grade)) as Critical_thinking_grade,
    apoc.coll.avg(collect(r.time)) as time, apoc.coll.avg(collect(r.number_of_clicks)) as number_of_clicks, apoc.coll.avg(collect(r.number_of_actions)) as number_of_actions, apoc.coll.avg(collect(r.number_of_submissions)) as number_of_submissions    
    """

    try:
        grades = graph.query(query)
    except Exception as e:
        print(f"[ERROR] Erron in retrieving Learner's grades from the database ({e})")
        return "", ""
    
    # Re-structure dictionary with grades (only for requested indicators)
    grades = {
        item["activity_id"]: {
            "Cognitive": item["Cognitive_grade"],
            "Creativity": item["Creativity_grade"],
            "Collaboration": item["Collaboration_grade"],
            "Communication": item["Communication_grade"],
            "Critical thinking": item["Critical_thinking_grade"]
        }
        for item in grades
    }
    # Exclude metrics
    for metric in available_metrics:
        if metric not in requested_metrics:
            for activity_id in grades:
                del grades[activity_id][metric]
    # Sanity check
    if grades == {}:
        return "", ""

    
    # Retrieve learners avg engagement metrics (for the selected activities)
    query = f"""MATCH (l:LEARNER)-[]->(c:COURSE)
        MATCH (l)-[r:PARTICIPATE]->(a:ACTIVITY)<-[:HAS_ACTIVITY]-(m:MODULE)<-[:HAS_MODULE]-(c)
        WHERE c.id = {course_id} AND a.id IN {list(grades.keys())} AND m.code = "{module}"
        WITH a.id AS activity_id, 
            round(apoc.coll.avg(collect(r.time)),1) AS time, 
            round(apoc.coll.avg(collect(r.number_of_clicks)),1) AS number_of_clicks, 
            round(apoc.coll.avg(collect(r.number_of_actions)),1) AS number_of_actions, 
            round(apoc.coll.avg(collect(r.number_of_submissions)),1) AS number_of_submissions
        WITH collect(apoc.map.fromValues([activity_id, {{
            time: time,
            number_of_clicks: number_of_clicks,
            number_of_actions: number_of_actions,
            number_of_submissions: number_of_submissions
        }}])) AS activity_list
        RETURN apoc.map.mergeList(activity_list) AS data;
        """
    avg_engagement_metrics = {}
    for key, values in graph.query(query)[0]['data'].items():
        avg_engagement_metrics[key] = {"Total time": values["time"], 
                                       "Number of clicks": values["number_of_clicks"], 
                                       "Number of actions": values["number_of_actions"], 
                                       "Number of submissions": values["number_of_submissions"]}
               
    # Get non-studied resources
    query = f"""MATCH (l:LEARNER)-[]->(c:COURSE)
    MATCH (l)-[]->(p:PROFILE)
    MATCH (c)-[:HAS_MODULE]->(m:MODULE)-[:HAS_RESOURCE]->(r:RESOURCE)
    WHERE c.id = {course_id} AND m.code = "{module}" AND p.name = "{profile}" AND NOT (l)-[:STUDY]->(r)
    WITH m.code AS moduleCode, l.username AS username, r.id AS resourceId
    WITH moduleCode, username, collect(resourceId) AS resourceIds
    RETURN collect({{username: username, id: resourceIds}}) AS Resources
    """
    non_studied_resources = {}
    for item in graph.query(query)[0]['Resources']:
        for resource_id in item['id']:
            if resource_id not in non_studied_resources:
                non_studied_resources[resource_id] = 1
            else:
                non_studied_resources[resource_id] += 1
    # Sort dictionary by values (ascending order)
    non_studied_resources = dict(sorted(non_studied_resources.items(), key=lambda item: item[1], reverse=True))

    # Create Response (for educator) - ENHANCED VERSION
    # -------------------------------------------------------------------------------------------------
    grades_report = ""
    # get_performance_emoji
    for activity_id, values in grades.items():
        # Grade
        grades_report += f"## {activity_id}\n\n"
        
        # PART I: Include grades on Cognitive and 4Cs
        # -------------------------------------------------------------------------------------------
        activity_report = ""
        for metric in requested_metrics:
            if values[metric]:                
                score = values[metric]
                activity_report += f"| {get_indicator_emoji(metric)} {terms[metric][language]} | {get_color_indicator(values[metric])} {score:.1f}% |\n"

        if activity_report:
            grades_report += f"### 📊 **{terms['Performance of learners belonging to profile'][language]}: {profile}**\n"
            grades_report += f"| {terms['Indicator'][language]} | {terms['Mean score'][language]} |\n"
            grades_report += "|----------|------------|\n"
            grades_report += activity_report + "\n\n"
        
        # PART II: Include engagement metrics
        # -------------------------------------------------------------------------------------------
        activity_report = ""
        if activity_id in avg_engagement_metrics:
            engagement = avg_engagement_metrics[activity_id]
            
            total_time = format_time(engagement['Total time'], language) if engagement['Total time'] else "-"
            number_of_clicks = f"{engagement['Number of clicks']:.1f}" if engagement['Number of clicks'] else "-"
            number_of_actions = f"{engagement['Number of actions']:.1f}" if engagement['Number of actions'] else "-"
            number_of_submissions = f"{engagement['Number of submissions']:.1f}" if engagement['Number of submissions'] else "-"
            
            # Vertical table layout
            activity_report += f"| **{terms['Engagement metric'][language]}** | **{terms['Mean'][language]}** |\n"
            activity_report += "|------------|--------|\n"
            activity_report += f"| ⏱️ {terms['Total time'][language]} | {total_time} |\n"
            activity_report += f"| 🖱️ {terms['Number of clicks'][language]} | {number_of_clicks} |\n"
            activity_report += f"| 🎯 {terms['Number of actions'][language]} | {number_of_actions} |\n"
            activity_report += f"| 📝 {terms['Number of submissions'][language]} | {number_of_submissions} |\n"

        if activity_report:
            grades_report += f"### 📈 **{terms['Participation profile of learners belonging to profile'][language]}: {profile}**\n\n"
            grades_report += activity_report + "\n\n"       

    # Get learner's not studied resources for this module
    if len(non_studied_resources) > 0:
        grades_report += f"\n### ⚠️ **(Top-5) {terms['Non studied resources'][language]}**\n"
        for item in list(non_studied_resources)[:5]:
            count = non_studied_resources[item]
            grades_report += f"- 📋 {item} ({count} {terms['learners'][language]})\n"
    grades_report += "\n"

    # Create Response (for retrieving feedback) - ENHANCED WITH ENGAGEMENT METRICS
    # -------------------------------------------------------------------------------------------------
    information_text = ""
    for activity_id, values in grades.items():
        # Grades
        information_text += f"## {activity_id}\n"
        no_grade = True        
        for metric in requested_metrics:
            if grades[activity_id][metric]:
                no_grade = False                
                information_text += f"  - {metric} grade: {grades[activity_id][metric]:.1f}/100\n"
        if no_grade: 
            for metric in  get_activity_metrics(activity_id=activity_id, graph=graph):
                grades_report += f"  - {metric} grade: Learners were not grades since they have not completed the task"
        grades_report+="\n\n"
                
        # Add engagement metrics to information_text
        if activity_id in avg_engagement_metrics:
            information_text += "\nEngagement Metrics:\n"
            engagement = avg_engagement_metrics[activity_id]
            if engagement['Total time']:
                information_text += f"  - Total time: {format_time(engagement['Total time'], language)}\n"
            if engagement['Number of clicks']:
                information_text += f"  - Number of clicks: {engagement['Number of clicks']:.1f}\n"
            if engagement['Number of actions']:
                information_text += f"  - Number of actions: {engagement['Number of actions']:.1f}\n"
            if engagement['Number of submissions']:
                information_text += f"  - Number of submissions: {engagement['Number of submissions']:.1f}\n"
        
        information_text += "\n"
    # Get learner's not studied resources for this module
    if len(non_studied_resources) > 0:
        information_text += "\n(Top-5) Non studied resources\n"
        for item in list(non_studied_resources)[:5]:
            information_text += f"  - {item}\n"   

    return grades_report + "---\n\n", information_text

def get_learner_information(
    graph: Neo4jGraph = None,
    course_id: int = None,
    username: str = None,
    modules: list = None,
    requested_metrics: list = None,
    language:str="english"
) -> (str, str):
    """
    Get information about learner's performance on all Modules by conducting a series of queries

    Parameters
    ----------
    graph: (Neo4jGraph)
        Neo4j graph
    course_id: (int)
        Course Id
    username: (str)
        Learner's username
    modules: (list)
        Modules' titles
    requested_metrics: (list)
        requested grades
    language: (str)
        response language

    Returns
    -------
    text containing the grades of the learner (str)
    text containing information for the learner (str)
    """
    requested_metrics = requested_metrics or [
        "Cognitive",
        "Creativity",
        "Collaboration",
        "Critical thinking",
        "Communication",
    ]

    # Check if the query requests for obtaining the grades/performance on specific module IDs
    # If not all modules are considered
    summary = ""
    if modules is None or modules == ["ALL"]:
        # Get all Module IDs
        response = graph.query(
            f"MATCH (c:COURSE)-[]->(m:MODULE) WHERE c.id = {course_id} return m.code as code"
        )
        modules = [item["code"] for item in response]
        # Sort modules
        modules.sort()

        # Retrieve all requested grades for all Modules
        response = graph.query(f"""MATCH (l:LEARNER)-[r:PARTICIPATE]->(a:ACTIVITY)<-[:HAS_ACTIVITY]-(m:MODULE)<-[:HAS_MODULE]-(c:COURSE)
                                MATCH (l)-[]->(c)
                                WHERE l.username = "{username}"  and c.id = {course_id} and a.metric in {requested_metrics}
                                RETURN a.metric as metric, apoc.coll.avg(collect(r.Cognitive)) as grade""")

        d_grades = {}
        for item in response:
            if item["metric"] not in d_grades:
                d_grades[item["metric"]] = [item["grade"]]
            else:
                d_grades[item["metric"]] += [item["grade"]]

        for metric in d_grades:
            if len(d_grades[metric]) > 1:
                if np.std(d_grades[metric]) > 15:
                    summary += (
                        f"- Learner's performance on '{metric}' seems to get unstable\n"
                    )
                else:
                    # Get trent
                    trent = calculate_trent(d_grades[metric])
                    if trent < -15:
                        summary += f"- Learner's performance on '{metric}' seems to get worsen during the last modules.\n"
                    elif trent > 15:
                        summary += f"- Learner's performance on '{metric}' seems to get improved during the last modules.\n"
                    else:
                        summary += f"- Learner's performance on '{metric}' seems to be relative stable during the last modules.\n"
        if len(summary) > 0:
            summary = "Summary\n" + summary + "\n\n"

    # Summary per module
    # --------------------------------------------------------------------------------------------------

    # Retrive feedback per Module
    L_grades_report, L_information_text = [], []
    for module in modules:
        # Retrieve information for a specific module and metric(s)
        grades_report, information_text = get_learner_information_per_module(
            graph=graph,
            course_id=course_id,
            username=username,
            module=module,
            requested_metrics=requested_metrics,
            language=language
        )
        # Check if information were retrieved from the DB
        if grades_report == "":
            continue
        # Store information/feedback for a specific module and metric(s)
        L_grades_report.append(f"# {module}\n" + grades_report)
        L_information_text.append(f"# {module}\n" + information_text)

    if len(L_grades_report) == 0:
            if language == "english":
                return "No information can be provided", "No information can be provided"
            elif language == "greek":
                return "Δεν μπορούν να παρασχεθούν πληροφορίες.", "No information can be provided"
            elif language == "serbian":
                return "Није могуће пружити информације.", "No information can be provided"
    else:
        return summary + "\n".join(L_grades_report), summary + "\n".join(
            L_information_text
        )


def get_profile_information(
    graph: Neo4jGraph = None,
    course_id: int = None,
    profile: str = None,
    modules: list = None,
    requested_metrics: list = None,
    language:str="english"
) -> (str, str):
    """
    Get information about learner's performance on all Modules by conducting a series of queries

    Parameters
    ----------
    graph: (Neo4jGraph)
        Neo4j graph
    course_id: (int)
        Course Id
    profile: (str)
        augMENTOR profile
    modules: (list)
        Modules' titles
    requested_metrics: (list)
        requested grades
    language: (str)
        response language

    Returns
    -------
    text containing the grades of the profile (str)
    text containing information for the profile (str)
    """
    requested_metrics = requested_metrics or [
        "Cognitive",
        "Creativity",
        "Collaboration",
        "Critical thinking",
        "Communication",
    ]

    if not modules or modules == ["ALL"]:
        # Get all Module IDs
        response = graph.query(
            f"MATCH (c:COURSE)-[]->(m:MODULE) WHERE c.id = {course_id} return m.code as code"
        )
        modules = [item["code"] for item in response]
        # Sort modules
        modules.sort()

    # Summary per module
    # --------------------------------------------------------------------------------------------------

    # Retrive feedback per Module
    L_grades_report, L_information_text = [], []
    for module in modules:
        # Retrieve information for a specific module and metric(s)
        grades_report, information_text = get_profile_information_per_module(
            graph=graph,
            course_id=course_id,
            profile=profile,
            module=module,
            requested_metrics=requested_metrics,
            language=language
        )
        # Check if information were retrieved from the DB
        if grades_report == "":
            continue
        # Store information/feedback for a specific module and metric(s)
        L_grades_report.append(f"# {module}\n" + grades_report)
        L_information_text.append(f"# {module}\n" + information_text)

    if len(L_grades_report) == 0:
            if language == "english":
                return "No information can be provided", "No information can be provided"
            elif language == "greek":
                return "Δεν μπορούν να παρασχεθούν πληροφορίες.", "No information can be provided"
            elif language == "serbian":
                return "Није могуће пружити информације.", "No information can be provided"
    else:
        return "\n".join(L_grades_report), "\n".join(L_information_text)


def get_module_information(graph: Neo4jGraph = None, course_id: int = None, modules: list = None, requested_metrics: list = None, language:str="english", include_evaluation:bool=True) -> (str, str):
    """
    Retrieves and compiles a report on module activity statistics and evaluations 
    for a given course from a Neo4j graph database.

    If 'modules' is set to ["ALL"], it queries all modules under the given course ID.
    For each module, it collects associated activity statistics and, optionally, evaluation data.

    Args:
        graph (Neo4jGraph): An instance of the graph database connection.
        course_id (int): The ID of the course to retrieve module information from.
        modules (list): List of module codes to retrieve. Use ["ALL"] to get all modules.
        requested_metrics (list): Currently unused. Can be used for future filtering.
        language (str): Language for fallback error messages. Options: "english", "greek", "serbian".
        include_evaluation (bool): Whether to include module evaluation data in the report.

    Returns:
        tuple[str, str]: A tuple containing the compiled report string twice.
                         If no information is found, a localized message is returned.
    """
    # Request information for ALL Modules (Get Module IDs)
    if modules == ["ALL"]:
        # Get all Module IDs
        response = graph.query(
            f"MATCH (c:COURSE)-[]->(m:MODULE) WHERE c.id = {course_id} return m.code as code"
        )
        modules = [item["code"] for item in response]
        # Sort modules
        modules.sort()    
    
    report = ""
    if requested_metrics:       
        query = f"""MATCH (l:LEARNER)-[]->(c:COURSE)
        MATCH (l)-[r:PARTICIPATE]->(a:ACTIVITY)<-[:HAS_ACTIVITY]-(m:MODULE)<-[:HAS_MODULE]-(c)
        WHERE c.id = {course_id} 
        RETURN m.code as module_id, apoc.coll.avg(collect(r.Cognitive_grade)) as Cognitive_grade, apoc.coll.avg(collect(r.Creativity_grade)) as Creativity_grade, apoc.coll.avg(collect(r.Collaboration_grade)) as Collaboration_grade, apoc.coll.avg(collect(r.Communication_grade)) as Communication_grade, apoc.coll.avg(collect(r.Critical_thinking_grade)) as Critical_thinking_grade order by m.code"""
        response = graph.query(query)

        d = {}
        for item in response:
            d[item['module_id']] = {
                'Cognitive': round(item['Cognitive_grade'], 1) if item['Cognitive_grade'] is not None else None,
                'Creativity': round(item['Creativity_grade'], 1) if item['Creativity_grade'] is not None else None,
                'Collaboration': round(item['Collaboration_grade'], 1) if item['Collaboration_grade'] is not None else None,
                'Communication': round(item['Communication_grade'], 1) if item['Communication_grade'] is not None else None,
                'Critical thinking': round(item['Critical_thinking_grade'], 1) if item['Critical_thinking_grade'] is not None else None
            }
        for module in modules:
            # Sanity check
            if module not in d: continue
            # Get requested metrics for Module
            grades_report = ""
            for metric in requested_metrics:
                if metric in d[module] and d[module][metric]:
                    legend = terms[f"{metric} grade"][language]
                    grades_report += f"- {get_performance_emoji(d[module][metric])}  {legend}: {d[module][metric]}/100\n"
            if grades_report:
                report += f"## {module}\n{grades_report}\n"
                
    else:            
        for module in modules:
            query = f"""match (c:COURSE)-[]->(m:MODULE)-[]->(a:ACTIVITY) where c.id={course_id} and m.code = '{module}' return collect(a.statistics) as statistics, m.evaluation as evaluation"""
            response = graph.query(query)
            # Sanity check
            if not response: continue
            if not response[0]['statistics']: continue
            # Create report for each Module        
            report += f"# {module}\n" + '\n'.join(response[0]['statistics'])
            if include_evaluation:
                report += f"{response[0]['evaluation']}\n\n"

    if not report:
        if language == "english":
            return "No information can be provided", "No information can be provided"
        elif language == "greek":
            return "Δεν μπορούν να παρασχεθούν πληροφορίες.", "No information can be provided"
        elif language == "serbian":
            return "Није могуће пружити информације.", "No information can be provided"
    else:             
        return report, report