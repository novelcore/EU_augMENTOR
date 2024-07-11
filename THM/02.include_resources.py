import os
import json
from utils.neo4j_connection import Neo4jConnection
from utils.google_search import search_videos, search_tutorials

# Neo4j local
neo4j_settings = {
    "connection_url": "bolt://localhost:7687",
    "username": "neo4j",
    "password": "augmentor2024",
}

# Create Graph-Database in Neo4j
graph = Neo4jConnection(
    uri=neo4j_settings["connection_url"],
    user=neo4j_settings["username"],
    pwd=neo4j_settings["password"],
)

resources_file = "Resources/resources.json"

# %%
# Get rooms
query = """MATCH (r:ROOM) return r.code as code, r.description as description, r.videos as videos, r.tutorials as tutorials"""
response = graph.query(query)
print("[INFO] Rooms retrieved from Neo4j")
print("[INFO] Number of rooms: ", len(response))

# %%
# Retrieve resourses if available
if os.path.isfile(resources_file):
    with open(resources_file, 'r', encoding = "utf8") as json_file:
        d = json.load(json_file)
    print("[INFO] Resources were retrieved")
else:
    d = {"code": [], "description": [], "videos": [], "tutorials": []}


for item in response:
    description = item["description"]
    code = item["code"]

    # Check if information exists
    if code in d["code"]: continue

    print("Room description: ", description)
    print("Room code: ", code)
    
    if "videos" in item.keys() and "tutorials" in item.keys():
        if item["videos"] is not None and item["tutorials"] is not None:            
            print("[INFO] Resources have been already uploaded.")
            continue 
    
    # Sanity check
    if len(description) == 0: 
        print("[WARNING] Room description is empty.")
        continue 
    
    try:
        videos = search_videos(query=description, number_of_results=5)
        print("[INFO] Videos retrieved")
        tutorials = search_tutorials(query=description, number_of_results=5)    
        print("[INFO] Tutorials retrieved")
        # documents = search_documents(query=description, number_of_results=5)
        # print("[INFO] Documents retrieved")
        # articles = search_articles(query=description)
        # print("[INFO] Articles retrieved")
        # papers = search_google_scholar(query=description, number_of_results=5)
        # print("[INFO] Research papers retrieved")
        print()
    except Exception as e:
        print("[ERROR] Information were not able to retrieve")
        print(f"> {e}\n")
        continue

    resources_videos =  "\n\n".join([f"Title: {video['Title']}\nURL: {video['URL']}" for video in videos])
    resouces_tutorials =  "\n\n".join([f"Title: {tutorial['Title']}\nURL: {tutorial['URL']}" for tutorial in tutorials])    
    
    # Store retrieved information
    d["code"].append(code)
    d["description"].append(description)    
    d["videos"].append(resources_videos)
    d["tutorials"].append(resouces_tutorials)

    try:
        # Create resources information
        resources_videos =  "\n".join([f"Title: {video['Title']}\nURL: {video['URL']}" for video in videos])
        resouces_tutorials =  "\n".join([f"Title: {tutorial['Title']}\nURL: {tutorial['URL']}" for tutorial in tutorials])
        # Preprocess
        resources_videos = resources_videos.replace('"',"'")
        resouces_tutorials = resouces_tutorials.replace('"',"'")

        query = f"""MATCH (r:ROOM {{code: "{code}"}}) 
        set r.videos="{resources_videos}"
        set r.tutorials="{resouces_tutorials}"
        """
        graph.query(query)
        print("[INFO] Information were uploaded to Knowledge-Graph\n")
    except Exception as e:
        print("[ERROR] Information were NOT uploaded to Knowledge-Graph")
        print(f"> {e}\n")

print('[INFO] Resources for all rooms where retrieved')
with open(resources_file, 'w', encoding = "utf8") as file:
    json.dump(d, file, ensure_ascii = False, separators = (',', ':'))
print(f"[INFO] Resources were saved in file: {resources_file}")


# %%
print('[INFO] Import resources data to Knowledge Graph')
for code, resources_videos, resouces_tutorials in zip(d['code'], d['videos'], d['tutorials']):
    try:
        # Preprocess
        resources_videos = resources_videos.replace('"',"'")
        resouces_tutorials = resouces_tutorials.replace('"',"'")
        
        query = f"""MATCH (r:ROOM {{code: "{code}"}}) 
        set r.videos="{resources_videos}"
        set r.tutorials="{resouces_tutorials}"
        """
        graph.query(query)
    except Exception as e:
        print("[ERROR] Information were NOT uploaded to Knowledge-Graph")
        print(f"> {e}\n")