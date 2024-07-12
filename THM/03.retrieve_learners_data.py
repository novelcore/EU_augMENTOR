import numpy as np
from utils.retrieve_data import retrieve_users, retrieve_data
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

# %% Users

# Retrieve users' data from TryHackMe API.
d_users = retrieve_users(headers=headers)
print("[INFO] Number of users: ", len(d_users))


# Remove all users interactions
query = """MATCH (u:LEARNER) detach delete u"""
graph.query(query)
    
# Include retrieve information to Knowledge-Graph
for username in d_users:
    dateSignedUp = d_users[username]["dateSignedUp"]
    totalPoints = d_users[username]["totalPoints"]
    completed_rooms = d_users[username]["completed_rooms"]

    query = f"""CREATE (u:LEARNER {{dateSignedUp: "{dateSignedUp}", completed_rooms: "{completed_rooms}", username: "{username}"}})"""
    graph.query(query)
print("[INFO] Learners have been imported")

# # %% Profiles

# # TODO: Remove dummy data for performance profiles   
# import random   
# d_profiles = dict()
# for username in d_users:
#     d_profiles[username] = {'profile': random.sample(population=["A", "B", "C", "D"], k=1)[0], "explanation": f"Learner: {username} was assigned to the profile since\n-its creativity score was greater than 5\n-The response to Q15 was B\n-The response to Q21 was A"}

#     # OPTIONAL: Include learner profile
#     d_profiles[username]['profile']
#     d_profiles[username]['explanation']
#     query = f"""MATCH (u:LEARNER {{username: "{username}"}})
#                 MERGE (p:PROFILE {{value:"{d_profiles[username]['profile']}"}})
#                 MERGE (u)-[:ASSIGNED {{explanation:"{d_profiles[username]['explanation']}"}}]->(p)"""
#     graph.query(query)

# %% Scoreboard

url = "https://tryhackme.com/external/api/rooms"
room_data = retrieve_data(url=url, headers=headers)

# Get Scoreboard for each Room
d_rooms = dict()
for item in room_data["roomInfo"]:
    room_code = item["code"]
    d_rooms[room_code] = {}
    
    # Room scoreboard
    url = f"https://tryhackme.com/api/v2/external/scoreboard?roomCode={item['code']}"
    response = retrieve_data(url=url, headers=headers)
    # Sanity check
    if response is None: continue
    if response["status"] != "success": continue
    
    d_rooms[item['code']]["scoreboard"] = list()
    for item in response["data"]:
        d_rooms[room_code]["scoreboard"].append({"username": item["username"], "score": item["score"], "tasks": item["tasks"]})    
print("[INFO] Scoreboard has been retrieved")

# Upload scoreboard in KG
for room_code in d_rooms:
    # Check for empty scoreboard
    if d_rooms[room_code]["scoreboard"] == []: continue
    
    # Get roomId
    query = f"""MATCH (r:ROOM {{code: "{room_code}"}}) return r.ID as roomId"""
    roomId = graph.query(query)[0]["roomId"]
     

    for item in d_rooms[room_code]["scoreboard"]:
        username = item["username"]       
        score = item["score"]
        
        query = f"""MATCH (u:LEARNER {{username: "{username}"}})
        MATCH (r:ROOM {{ID: "{roomId}"}})
        MERGE (u)-[:REGISTERED {{score:{score}}}]->(r)    
        """
        graph.query(query)
        
        # Assign Learner responses to Questions
        for taskNo in item["tasks"]:
            taskId = f"RoomId:{roomId}|No:{taskNo}"
            for item2 in item["tasks"][taskNo]:
                questionNo = item2["questionNo"]
                correct = item2["correct"]
                score = item2["score"]
                attempts = item2["attempts"]
                                
                query = f"""MATCH (u:LEARNER {{username: "{username}"}})
                MATCH (t:TASK {{ID: "{taskId}"}})-[]->(q:QUESTION {{questionNo: "{questionNo}"}})
                MERGE (u)-[:PERFORMED {{score: {score}, correct: "{correct}", attempts: {attempts}}}]->(q)
                """     
                graph.query(query) 
print("[INFO] Scoreboard has been imported in KG")

# Calculate Module & Path percentage completeness

# Calculate #rooms for each module
d_modules = {}
query = """MATCH (m:MODULE)-[:HAS_ROOM]->(r:ROOM)
return m.moduleURL as moduleURL, count(DISTINCT r) as number_of_rooms"""

for item in graph.query(query):
    d_modules[item['moduleURL']] = item['number_of_rooms']
    
# Calculate #rooms for each path
d_paths = {}
query = """MATCH (p:PATH)-[:HAS_MODULE]->(m:MODULE)-[:HAS_ROOM]->(r:ROOM)
return DISTINCT p.code as path_code, count(DISTINCT r) as number_of_rooms"""

for item in graph.query(query):
    d_paths[item['path_code']] = item['number_of_rooms']

# Calculate module-percentage for each user
for username in d_users:

    query = f"""MATCH (l:LEARNER {{username: '{username}'}})
    MATCH (m:MODULE)-[:HAS_ROOM]->(r:ROOM)
    WHERE (l)-[:REGISTERED]->(r)
    RETURN DISTINCT m.moduleURL as moduleURL, COLLECT(DISTINCT(r.code)) as room_codes"""
    response = graph.query(query)
    
    # Sanity check - Check if the user has not been registered to any rooms of this module
    if response == []: continue

    query = f"""MATCH (l:LEARNER {{username: '{username}'}}) RETURN l.completed_rooms as completed_rooms"""
    completed_rooms = graph.query(query)[0]["completed_rooms"]
    
    for item in response:
        percentage_registered = np.round(100.0 * len(item['room_codes'])/d_modules[item['moduleURL']], 1)
        percentage_completeness = np.round(100.0 * len([room_code for room_code in item['room_codes'] if room_code in completed_rooms])/d_modules[item['moduleURL']], 1)
        
        query = f"""MATCH (m: MODULE {{moduleURL:"{item['moduleURL']}"}})
        MATCH (l:LEARNER {{username: '{username}'}})
        MERGE (l)-[:REGISTERED_MODULE {{percentage_registered: {percentage_registered}, percentage_completeness:{percentage_completeness}}}]->(m)
        """
        
        graph.query(query)
print("[INFO] Information about learners' and modules has been calculated")
        
        
# Calculate path-percentage for each user
for username in d_users:

    query = f"""MATCH (l:LEARNER {{username: '{username}'}})
    MATCH (p:PATH)-[:HAS_MODULE]->(m:MODULE)-[:HAS_ROOM]->(r:ROOM)
    WHERE (l)-[:REGISTERED]->(r)
    RETURN DISTINCT p.code as path_code, COLLECT(DISTINCT(r.code)) as room_codes"""
    response = graph.query(query)
    
    # Sanity check - Check if the user has not been registered to any rooms of this path
    if response == []: continue

    query = f"""MATCH (l:LEARNER {{username: '{username}'}}) RETURN l.completed_rooms as completed_rooms"""
    completed_rooms = graph.query(query)[0]["completed_rooms"]
    
    for item in response:
        percentage_registered = np.round(100.0 * len(item['room_codes'])/d_paths[item['path_code']], 1)
        percentage_completeness = np.round(100.0 * len([room_code for room_code in item['room_codes'] if room_code in completed_rooms])/d_paths[item['path_code']], 1)
        
        
        query = f"""MATCH (p:PATH {{code:"{item['path_code']}"}})
        MATCH (l:LEARNER {{username: '{username}'}})
        MERGE (l)-[:REGISTERED_ROOM {{percentage_registered: {percentage_registered}, percentage_completeness:{percentage_completeness}}}]->(p)
        """
        graph.query(query)
print("[INFO] Information about learners' and learning paths has been calculated")
