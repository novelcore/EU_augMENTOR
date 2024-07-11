from langchain.graphs import Neo4jGraph
import ast


def get_learner_information_per_room(graph:Neo4jGraph=None, username:int=None, room_code:str=None, detailed_info:bool=True)->[str, str]:
    """
    Retrieves information about a learner's performance in a specific room.

    Args:
    - graph (Neo4jGraph): A Neo4jGraph object representing the connection to the Neo4j database.
    - username (int): The username of the learner.
    - room_code (str): The code of the room to retrieve information for.

    Returns:
    - tuple: A tuple containing two strings:
        - grades_report (str): A report summarizing the learner's performance in the room.
        - information_text (str): Detailed information about the learner's performance in the room.
    """    
    try:
        query = f"""MATCH (l:LEARNER {{username:"{username}"}}) return l.completed_rooms as completed_rooms"""
        completed_rooms = ast.literal_eval(graph.query(query)[0]["completed_rooms"])
    except Exception as e:
        print(e)
        grades_report = "[ERROR] Data relative to Learner's performance from the database was not retrieved\n"
        return grades_report, grades_report
    
    query = f"""MATCH (l:LEARNER {{username:"{username}"}})-[rl:REGISTERED]->(r:ROOM {{code: "{room_code}"}}) return rl.score as score, r.description as description"""
    response = graph.query(query)
    
    if response == []:
        grades_report = f"### Room: {room_code}\nNo information can be provided for learner: {username}\n"
        return grades_report, grades_report


    # Retrieve Questions & Responses    
    query = f"""MATCH (l:LEARNER {{username:"{username}"}})-[:REGISTERED]->(r:ROOM {{code: "{room_code}"}})
            MATCH (q:QUESTION)<-[]-(t:TASK)<-[]-(r)
            MATCH (l)-[rl:PERFORMED]->(q) 
            return t.ID as task_ID, q.question as question, q.answer as answer, rl.correct as correct, rl.score as score"""
    performance_response = graph.query(query)
    

    # Contruct responses
    grades_report = f"### Room: {room_code}\n"
    if room_code in completed_rooms:
        grades_report += "Status: Completed\n"
        grades_report += f"Score: {response[0]['score']}/560\n" # TODO: Check if for not completed room, the score should or should not be provided
        number_of_correctly_answers = len([item for item in performance_response if item['correct'] != "False"])
        grades_report += f"Number of correctly answered questions: {number_of_correctly_answers}/{len(performance_response)}\n" 
    else:
        grades_report += "Status: Not completed\n"
        grades_report += "Score: -\n" # TODO: Check if for not completed room, the score should or should not be provided
    information_text = grades_report + f"Room description: {response[0]['description']}\n"

    if detailed_info:
        d_questions = {}
        for item in performance_response:
            task = int(item["task_ID"].split(":")[-1])
            if task not in d_questions: d_questions[task] = []
            # Do not consider cases, where the user has responded correctly
            if item["correct"] == "True":
                continue
            d_questions[task] += [{"question": item["question"], "answer": item["question"]}]
            # Sort dictionary based on key values
            d_questions = {k: d_questions[k] for k in sorted(d_questions)}

        report = ""
        for task in d_questions:
            # If no wrong question where detected - skip information about this task
            if d_questions[task] == []: 
                continue
            report += f"\nTask {task}\n"
            for item in d_questions[task]:
                report += f"- Question: {item['question']}\n"
                if room_code not in completed_rooms: # TODO: Check if the correct answers should be provided ONLY for completed questions
                    report += f"  Correct answer: {item['answer']}\n"
        
        if report != "":
            grades_report += "\nThe learner has responded wrong in the following questions for each task:" + report
            information_text += "\nThe learner has responded wrong in the following questions for each task:" + report
        else:
            grades_report += "\nThe learner has correctly responded all questions\n"
            information_text     += "\"\nThe learner has correctly responded all questions\n"
            
    
    return grades_report, information_text


def get_learner_information_rooms(graph:Neo4jGraph=None, username:int=None, room_code:list=[], detailed_info:bool=True)->[str, str]:
    
    grades_report, information_text = "", ""
    for code in room_code:
        module_grades_report, module_information_text = get_learner_information_per_room(graph=graph, username=username, room_code=code, detailed_info=detailed_info)
        if module_grades_report == "": continue
        
        grades_report += module_grades_report + 80*"-" + "\n\n"
        information_text += module_information_text + "\n"
        
    return grades_report, information_text



def get_learner_information_per_module(graph:Neo4jGraph=None, username:int=None, moduleURL:str=None, detailed_info:bool=True)->[str, str]:

    # Retrive ROOMS of selected MODULE
    query = f"""MATCH (m: MODULE {{moduleURL: "{moduleURL}"}})-[rl:HAS_ROOM]->(r:ROOM) return rl.order as order, r.code as code"""
    response = graph.query(query)
    
    d_modules = {}
    for item in response:
        d_modules[int(item["order"])] = item["code"] 
    # Sort dictionary based on key values
    d_modules = {k: d_modules[k] for k in sorted(d_modules)}

    grades_report, information_text = get_learner_information_rooms(graph=graph, username=username, room_code=[d_modules[key] for key in d_modules], detailed_info=detailed_info)
    return grades_report, information_text


def get_learner_information_modules(graph:Neo4jGraph=None, username:int=None, moduleURL:list=[], detailed_info:bool=True)->[str, str]:
    
    grades_report, information_text = "", ""
    for module in moduleURL:
        module_grades_report, module_information_text = get_learner_information_per_module(graph=graph, username=username, moduleURL=module, detailed_info=detailed_info)        
        if module_grades_report == "": continue
        
        grades_report += f"## Module: {module}\n"
        query = f"""MATCH (l:LEARNER {{username:"{username}"}})-[r]->(m:MODULE {{moduleURL:"{module}"}}) return r.percentage_completeness as percentage_completeness, r.percentage_registered as percentage_registered"""
        response = graph.query(query)
        percentage_completeness = "0%" if response == [] else f"{response[0]['percentage_completeness']}%"
        percentage_registered = "0%" if response == [] else f"{response[0]['percentage_registered']}%"
        grades_report += f"Learner: {username} has been registered to {percentage_registered} of rooms of this module and completed {percentage_completeness} of the rooms\n\n"            
        if float(percentage_registered[:-1]) > 0:
            grades_report += module_grades_report + "\n"
        
        information_text += f"## Module: {module}\n"
        information_text += f"Learner: {username} has been registered to {percentage_registered} of rooms of this module and completed {percentage_completeness} of the rooms\n\n"            
        if float(percentage_registered[:-1]) > 0:
            information_text += module_information_text + "\n"
        
    return grades_report, information_text




def get_learner_information_per_path(graph:Neo4jGraph=None, username:int=None, path_code:str=None, detailed_info:bool=True)->[str, str]:

    # Retrive MODULE of selected PATH
    query = f"""MATCH (p:PATH {{code: "{path_code}"}})-[rl:HAS_MODULE]->(m: MODULE) return rl.order as order, m.moduleURL as moduleURL"""
    response = graph.query(query)
    
    d_paths = {}
    for item in response:
        d_paths[int(item["order"])] = item["moduleURL"] 
    # Sort dictionary based on key values
    d_paths = {k: d_paths[k] for k in sorted(d_paths)}
        
    grades_report, information_text = get_learner_information_modules(graph=graph, username=username, moduleURL=[d_paths[key] for key in d_paths], detailed_info=detailed_info)
    return grades_report, information_text


def get_learner_information_paths(graph:Neo4jGraph=None, username:int=None, path_code:list=[], detailed_info:bool=True)->[str, str]:
    
    grades_report, information_text = "", ""
    for code in path_code:
        path_grades_report, path_information_text = get_learner_information_per_path(graph=graph, username=username, path_code=code, detailed_info=detailed_info)        
        if path_grades_report == "": continue
        
        grades_report += f"# Path: {code}\n"
        query = f"""MATCH (l:LEARNER {{username:"{username}"}})-[r]->(p:PATH {{code:"{code}"}}) return r.percentage_completeness as percentage_completeness, r.percentage_registered as percentage_registered"""
        response = graph.query(query)
        percentage_completeness = "0%" if response == [] else f"{response[0]['percentage_completeness']}%"
        percentage_registered = "0%" if response == [] else f"{response[0]['percentage_registered']}%"
        grades_report += f"Learner: {username} has been registered to {percentage_registered} of rooms of this path and completed {percentage_completeness} of the rooms\n\n"
        if float(percentage_registered[:-1]) > 0:
            grades_report += path_grades_report + "\n"
        
        information_text += f"# Path: {code}\n"
        information_text += f"Learner: {username} has been registered to {percentage_registered} of rooms of this path and completed {percentage_completeness} of the rooms\n\n"
        if float(percentage_registered[:-1]) > 0:
            information_text += path_information_text + "\n"
        
    return grades_report, information_text
