from utils.retrieve_data import retrieve_rooms, retrieve_modules_paths
from utils.neo4j_connection import Neo4jConnection

# Configuration
headers = {"THM-API-KEY": "..."}

neo4j_settings = {
    "connection_url": "...",
    "username": "...",
    "password": "...",
}

# Create Graph-Database in Neo4j
graph = Neo4jConnection(
    uri=neo4j_settings["connection_url"],
    user=neo4j_settings["username"],
    pwd=neo4j_settings["password"],
)
graph.clean_base()

# %% Rooms

# Retrieves information about rooms from TryHackMe API.
d_rooms = retrieve_rooms(headers=headers) 

    
# Include retrieve information to Knowledge-Graph
for key in d_rooms:
    # TODO: Check if the condition should be applied or not
    # if "roomId" in d_rooms[key]: continue
    # # Check if information about this room were retrieved # TODO: Check if this is needed
    # if d_rooms[key]["public"] is False:
    #     continue
    
    # Sanity check
    if 'AugMentor Osint' == d_rooms[key]["title"]: continue
    
    description = d_rooms[key]["description"].replace('"','').replace("'","").replace("<p>","").replace("</p>","").replace('\\','/')
    title = d_rooms[key]["title"].replace('"','').replace("'","").replace("<p>","").replace("</p>","").replace('\\','/')
    if "roomId" not in d_rooms[key]: 
        roomId = key
    else:
        roomId = d_rooms[key]["roomId"]
    if "type" not in d_rooms[key]: 
        type = ""
    else:
        type = d_rooms[key]["type"]
    if "difficulty" not in d_rooms[key]: 
        difficulty = ""
    else:        
        difficulty = d_rooms[key]["difficulty"]
    if "timeToComplete" not in d_rooms[key]:         
        timeToComplete = ""
    else:
        timeToComplete = d_rooms[key]["timeToComplete"]
    
    query = f"""MERGE (r:ROOM {{description: "{description}", title: "{title}", type: "{type}", difficulty: "{difficulty}", timeToComplete: "{timeToComplete}", ID: "{roomId}", code: "{key}"}})"""
    graph.query(query)

    # For each room assign tasks & questions
    for taskNo in d_rooms[key]["tasks"]:
        taskId = f"RoomId:{roomId}|No:{taskNo}"
        for item in d_rooms[key]["tasks"][taskNo]:
            questionNo = item["questionNo"]
            question = item["question"].replace('"','').replace("'","").replace("<p>","").replace("</p>","").replace('\\','/')
            answer = item["answer"].replace('"','').replace("'","").replace("<p>","").replace("</p>","").replace('\\','/')
            hint = item["hint"].replace('"','').replace("'","").replace("<p>","").replace("</p>","").replace('\\','/')
            extraPoints = item["extraPoints"]

            query = f"""MATCH (r:ROOM {{ID: "{roomId}"}})
            MERGE (t:TASK {{ID: "{taskId}"}})
            MERGE (q:QUESTION {{questionNo: "{questionNo}", answer: "{answer}", hint: "{hint}", extraPoints: "{extraPoints}", question: '{str(question)}'}}) 
            MERGE (r)-[:HAS_TASK]->(t)
            MERGE (t)-[:HAS_QUESTION]->(q)"""
            graph.query(query)

# %% Modules & Paths

# Retrieve modules' and paths' data from TryHackMe.
d_paths, d_modules = retrieve_modules_paths(headers=headers)


# Include retrieve information to Knowledge-Graph
for moduleURL, item in d_modules.items():
    title = item["title"].replace('"','').replace("'","").replace("<p>","").replace("</p>","").replace('\\','/')
    summary = item["summary"].replace('"','').replace("'","").replace("<p>","").replace("</p>","").replace('\\','/')

    query = f"""MERGE (m:MODULE {{title: "{title}", summary: "{summary}", moduleURL: "{moduleURL}"}})"""
    graph.query(query)
    
    
    
# Merge each module with the default next one
for moduleURL, item in d_modules.items():
    if "next" not in item: continue
    
    for next_module in item["next"]:
        query = f"""MATCH (m1:MODULE {{moduleURL: "{moduleURL}"}})
        MATCH (m2:MODULE {{moduleURL: "{next_module}"}})
        MERGE (m1)-[:NEXT_MODULE]->(m2)"""
        graph.query(query)
        
    for i, roomcode in enumerate(item["rooms"]):
        query = f"""MATCH (m:MODULE {{moduleURL: "{moduleURL}"}})
        MATCH (r:ROOM {{code: "{roomcode}"}})
        MERGE (m)-[:HAS_ROOM {{order: {i}}}]->(r)"""
        graph.query(query)   

# Create PATH nodes
for path_code in d_paths:
    intro = d_paths[path_code]["intro"].replace('"','').replace("'","").replace("<p>","").replace("</p>","").replace('\\','/')
    summary = d_paths[path_code]["summary"].replace('"','').replace("'","").replace("<p>","").replace("</p>","").replace('\\','/')
    title = d_paths[path_code]["title"].replace('"','').replace("'","").replace("<p>","").replace("</p>","").replace('\\','/')
    difficulty = d_paths[path_code]["difficulty"].replace('"','').replace("'","").replace("<p>","").replace("</p>","").replace('\\','/')  
    
    query = f"""MERGE (p:PATH {{intro: "{intro}", summary: "{summary}", title: "{title}", difficulty: "{difficulty}", code: "{path_code}"}})"""         
    graph.query(query) 
    
    
# Link PATH nodes with their component MODULE nodes
for path_code in d_paths:
    for i, moduleURL in enumerate(d_paths[path_code]["tasks"]):
        query = f"""MATCH (p:PATH {{code: "{path_code}"}})
        MATCH (m:MODULE {{moduleURL: "{moduleURL}"}})
        MERGE (p)-[:HAS_MODULE {{order: {i}}}]->(m)"""         
        graph.query(query)


