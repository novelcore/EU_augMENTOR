import time
import requests

# Variable for defining the maximum number of iterations for attempting
# to download data from THM
n_iterations = 5


def retrieve_data(url: str = None, headers:dict={}, payload:dict={},) -> dict:
    """
    Retrieve data from a given URL using GET request.

    Args:
        url (str): The URL to retrieve data from.
        headers (dict): Additional headers to include in the request.
        payload (dict): Payload to send along with the request.

    Returns:
        dict: Response data in JSON format.

    Raises:
        requests.exceptions.RequestException: If an error occurs during the request.
    """
    for iter in range(n_iterations):
        try:
            response = requests.get(url, headers=headers, data=payload, timeout=30)
            response.raise_for_status()

            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Data from {url} were not retrieved (Attempt: #{iter+1})")
            print("> ", e)
            print("Re-attempting...\n")
            time.sleep(3)
        
    return None
    
    
    
def retrieve_users(headers:dict={}):
    """
    Retrieve information about users from TryHackMe API.

    Args:
        headers (dict, optional): Headers to be sent with the HTTP request. Defaults to {}.

    Returns:
        dict: A dictionary containing user information with usernames as keys.
              Each value in the dictionary is another dictionary with keys:
              - dateSignedUp: The date when the user signed up.
              - totalPoints: The total points earned by the user.
              - monthlyPoints: The points earned by the user in the current month.
              - userId: The ID of the user.
              - completed_rooms: A list of codes for rooms completed by the user.
    """
    url = "https://tryhackme.com/external/api/users"
    data = retrieve_data(url=url, headers=headers)

    # Get users and basic information
    d_users = dict()
    for item in data["users"]:
        d_users[item["username"]] = {
            # "email": item["email"],
            "dateSignedUp": item["dateSignedUp"],
            "totalPoints": item["totalPoint"],
            "monthlyPoints": item["monthlyPoints"],
        }
    print('[INFO] Users\' basic descriptions were retrieved')        


    for username in d_users:
        # # GET userID
        # url = f"https://tryhackme.com/api/similar-users/{username}"
        # data = retrieve_data(url=url, headers=headers)
        # d_users[username]["userId"] = data[0]["userId"]
        
        # GET completed Rooms
        url = f"https://tryhackme.com/api/all-completed-rooms?username={username}"
        data = retrieve_data(url=url, headers=headers)
        d_users[username]["completed_rooms"] = []
        for item in data:
            d_users[username]["completed_rooms"].append(item["code"])
    print('[INFO] Users\' IDs and completed rooms were retrieved')        
            
    return d_users


def retrieve_rooms(headers:dict={})->dict:
    """
    Retrieves information about rooms from TryHackMe API.

    Args:
    headers (dict, optional): Headers for API requests. Defaults to {}.

    Returns:
    dict: Dictionary containing room information.
    """
    url = "https://tryhackme.com/external/api/rooms"
    data = retrieve_data(url=url, headers=headers)

    # Get Rooms basic description
    d_rooms = dict()
    for item in data["roomInfo"]:
        d_rooms[item["code"]] = {
            "description": item["description"],
            "title": item["title"],
            "public": item["public"],
        }
    print('[INFO] Rooms\' basic descriptions were retrieved')        
                
    for room_code in d_rooms:
        # GET votes
        url = f"https://tryhackme.com/api/room/votes?code={room_code}"
        response = retrieve_data(url=url, headers=headers)    
        # Sanity check
        if response is None: continue

        d_rooms[room_code]["upvotes"] = response["upvotes"]
        d_rooms[room_code]["userVote"] = response["userVote"]
    print('[INFO] Rooms\' votes were retrieved')        
        

    for room_code in d_rooms:
        # GET details for each room
        url = f"https://tryhackme.com/api/room/details?codes={room_code}&loadWriteUps=false&loadCreators=false&loadUser=true"
        response = retrieve_data(url=url, headers=headers)
        # Sanity check
        if response is None: continue
         
        if response[room_code]["success"]:
            d_rooms[room_code]["roomId"] = response[room_code]["roomId"]
            d_rooms[room_code]["type"] = response[room_code]["type"]
            d_rooms[room_code]["difficulty"] = response[room_code]["difficulty"]
            d_rooms[room_code]["tags"] = response[room_code]["tags"]
            d_rooms[room_code]["video"] = response[room_code]["video"]
            d_rooms[room_code]["timeToComplete"] = response[room_code]["timeToComplete"]
    print('[INFO] Rooms\' details were retrieved')        

    for room_code in d_rooms:
        # Room Questions
        url = f"https://tryhackme.com/external/api/questions?roomCode={room_code}"
        response = retrieve_data(url=url, headers=headers)

        if response is None: 
            print(f"[WARNING] No data were processed for room: '{room_code}'")
            continue

        d = dict()
        for item in response["questions"]:
            d[item["taskNo"]] = item["infoList"]
        d_rooms[room_code]["tasks"] = d
    print('[INFO] Questions for each room were retrieved')
    
    return d_rooms



def retrieve_modules(headers:dict={})->dict:
    """
    Retrieve modules data from TryHackMe.

    Args:
        headers (dict, optional): Headers for HTTP request. Defaults to {}.

    Returns:
        tuple: A tuple containing two dictionaries:
            - d_modules: A dictionary containing module data with module URL as keys and corresponding details as values.
            - d_modules_id: A dictionary containing module IDs as keys and module URLs as values.
    """
    url = "https://tryhackme.com/modules/summary"
    modules = retrieve_data(url=url, headers=headers)

    d_modules, d_modules_id = dict(), dict()
    for item in modules:    
        # Retrieve data   
        url = f"https://tryhackme.com/modules/data/{item['moduleURL']}"
        response = retrieve_data(url=url, headers=headers)
    
        d_modules[response["moduleURL"]] = {"title": response["title"], "summary": response["summary"], "rooms": [x["code"] for x in response["rooms"]]}  
        
        for item in response["prerequisites"]:
            # Sanity check: In case moduleURL = '' then we manually assign it
            if item["moduleURL"] == "": 
                item["moduleURL"] = item["title"].replace(" ","_").lower()                
            if item["id"] not in d_modules_id:
                    d_modules_id[item["id"]] = item["moduleURL"]
    print('[INFO] Modules\' URLs were retrieved')        
                    
    return d_modules, d_modules_id


def retrieve_modules_paths(headers:dict=None)->dict:
    """
    Retrieve modules' and paths' data from TryHackMe.

    Args:
        headers (dict, optional): Headers for HTTP request. Defaults to {}.

    Returns:
        - d_paths: A dictionary containing path data with path codes as keys and corresponding details as values.
        - d_modules: A dictionary containing module data with module URL as keys and corresponding details as values.
    """    
    # Retrieves module data from TryHackMe API.
    d_modules, d_modules_id = retrieve_modules(headers=headers)
        
    url = "https://tryhackme.com/paths/summary"
    response = retrieve_data(url=url, headers=headers)

    # Get users and basic information
    d_paths = dict()
    for item in response:
        d_paths[item["code"]] = {
            "intro": item["intro"].replace("<p>", "").replace("<li>"," ").replace("</li>","").replace("</ul>",""),
            "summary": item["summary"],
            "title": item["title"],
            "difficulty": item["difficulty"]["text"].lower()
        }
    print('[INFO] Paths\' basic information were retrieved')        
        
        
    # Update Module IDs
    for path_code in d_paths:
        url = f"https://tryhackme.com/paths/single/{path_code}"
        data = retrieve_data(url=url, headers=headers)

        # Include additional Module IDs
        for i, item in enumerate(data["tasks"]):
            if item["id"] not in d_modules_id and item["id"] != "":
                # Sanity check: In case moduleURL = '' then we manually assign it
                if item["moduleURL"] == "": 
                    item["moduleURL"] = item["title"].replace(" ","_").lower()
                d_modules_id[item["id"]] = item["moduleURL"]
            
    for path_code in d_paths:
        d_paths[path_code]["tasks"] = []
        url = f"https://tryhackme.com/paths/single/{path_code}"
        data = retrieve_data(url=url, headers=headers)
        
        for i, item in enumerate(data["tasks"]):
            # Sanity check: In case moduleURL = '' then we manually assign it
            if item["moduleURL"] == "": 
                item["moduleURL"] = item["title"].replace(" ","_").lower()
            # Update d_modules_id
            if item["id"] in d_modules_id: item["moduleURL"] = d_modules_id[item["id"]]
            # Include information about the module in d_modules (if it has not been included)
            if item["moduleURL"] not in d_modules:
                d_modules[item["moduleURL"]] = {"title": item["title"], "summary": item["overview"], "rooms": [x["code"] for x in item["rooms"]]}  
                            
            d_paths[path_code]["tasks"].append(item["moduleURL"])
        # # This implementation includes ALL information about each moduleURL
        #     d[str(i)] = {"moduleURL": item["moduleURL"], "overview": item["overview"], "id": item["id"], "rooms": {room["order"]:room["code"] for room in item["rooms"]}}
        # d_paths[path_code]["tasks"] = d
    print('[INFO] Information connecting Paths and Modules was retrieved')        
        
        
    # Calculate next module for each module
    for path_code in d_paths:
        L = d_paths[path_code]["tasks"]
        
        # Sanity check
        if '' in L:
            print("[ERROR] Empty moduleURL") 
            break    
            
        for i in range(len(L)-1):            
            if "next" not in d_modules[L[i]]:
                d_modules[L[i]]["next"] = []
            if L[i+1] not in d_modules[L[i]]["next"]:
                d_modules[L[i]]["next"].append(L[i+1])
                
                
    return d_paths, d_modules


def retrieve_scoreboard(headers:dict={})->dict:
    """
    Retrieve scoreboard data for TryHackMe rooms.

    Parameters:
    - headers (dict): Optional. Headers for API requests. Defaults to an empty dictionary.

    Returns:
    - scoreboard (dict): A dictionary containing scoreboard data for each room.
                        Keys are room codes, and values are lists of dictionaries containing
                        usernames, scores, and tasks completed.
    """                        
    url = "https://tryhackme.com/external/api/rooms"
    data = retrieve_data(url=url, headers=headers)

    # Get Rooms basic description
    scoreboard = dict()
    for item in data["roomInfo"]:
        room_code = item["code"]
        
        # Room scoreboard
        url = f"https://tryhackme.com/api/v2/external/scoreboard?roomCode={room_code}"
        response = retrieve_data(url=url, headers=headers)
        
        # Sanity check
        if response is None: continue
        if response["status"] != "success": continue
        # Check for empty data
        if len(response['data']) == 0: continue

        # Retrieve data
        scoreboard[room_code] = list()
        for item in response["data"]:
            scoreboard[room_code].append({"username": item["username"], "score": item["score"], "tasks": item["tasks"]}) 
            
    return scoreboard