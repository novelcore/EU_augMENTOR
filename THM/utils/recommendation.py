import os
import ast
import json
from langchain.schema.document import Document
from langchain.chat_models import ChatOpenAI
from langchain.graphs import Neo4jGraph
from langchain.chains.llm import LLMChain
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains.graph_qa.cypher import construct_schema, extract_cypher
from langchain.chains.graph_qa.cypher_utils import Schema, CypherQueryCorrector
from utils.utils import color
from utils.get_suggestions import get_suggestion_about_learning
from utils.information import get_learner_information_rooms, get_learner_information_modules, get_learner_information_paths
from utils.translate_queries import abbr_languages, translate
from utils.prompts import (
    OFFENSIVE_IDENTIFICATION_PROMPT,
    CYPHER_GENERATION_PROMPT,
    CYPHER_QA_PROMPT,
    ID_IDENTIFICATION_PROMPT,
    RECOMMENDATION_PROMPT,
    REQUEST_INFORMATION_PROMPT,
    SEND_INFORMATION_PROMPT,
    QUESTION_TRANSFORMATION_PROMPT,
)

prompts = {
    "offensive_identification": OFFENSIVE_IDENTIFICATION_PROMPT,
    "cypher_generation_prompt": CYPHER_GENERATION_PROMPT,
    "cypher_qa_prompt": CYPHER_QA_PROMPT,
    "id_identification_prompt": ID_IDENTIFICATION_PROMPT,
    "recommendation_prompt": RECOMMENDATION_PROMPT,
    "request_information_prompt": REQUEST_INFORMATION_PROMPT,
    "send_information_prompt": SEND_INFORMATION_PROMPT,
    "question_transformation_prompt": QUESTION_TRANSFORMATION_PROMPT,
}


class Recommendations:
    def __init__(self, neo4j_settings:dict=None, openai_settings:dict=None, cypher_corrector:bool=True,
                 user_settings:dict=None, recommendations_file:dict=None, language:str="English",\
                 recommendations_db_path=None, room_descriptions_db_path=None, verbose:bool=False)->None:
        """
            Initialization

            Parameters
            ----------
            neo4j_settings: (dict)
                Neo4j settings (url, username, password), 
            openai_settings: (dict)
                OpenAI settings (username, password),     
            prompts (dict)
                Dictionary containing the required LLM prompts
            cypher_corrector: (bool)
                Cypher correction mechanism
            user_settings: (dict)
                User settings (name, title, etc) 
            recommendations_file: (str)
                Path containing the recommendations for each case                
            verbose: (bool)
                Boolean variable for showing results 
        """
        
        # Neo4j Settings
        self._neo4j_settings = neo4j_settings
        # Setup embeddings model
        embeddings = OpenAIEmbeddings(openai_api_key=openai_settings["api_key"])
        # Setup ChatGPT model
        self._llm = ChatOpenAI(model_name=openai_settings["model_name"], temperature=openai_settings["temperature"], openai_api_key=openai_settings['api_key'])
        # LLM Chains
        self._offensive_identification_chain = LLMChain(llm=self._llm, prompt=prompts["offensive_identification"])
        self._cypher_generation_chain = LLMChain(llm=self._llm, prompt=prompts["cypher_generation_prompt"])
        self._qa_chain = LLMChain(llm=self._llm, prompt=prompts["cypher_qa_prompt"])
        self._id_chain = LLMChain(llm=self._llm, prompt=prompts["id_identification_prompt"])
        self._recommendation_chain = LLMChain(llm=self._llm, prompt=prompts["recommendation_prompt"])
        self._request_information_chain = LLMChain(llm=self._llm, prompt=prompts["request_information_prompt"])
        self._send_information_chain = LLMChain(llm=self._llm, prompt=prompts["send_information_prompt"])
        if user_settings["title"] == "Learner":
            self._question_transformation_chain = LLMChain(llm=self._llm, prompt=prompts["question_transformation_prompt"])                        
        # Cypher corrector
        self._cypher_corrector = cypher_corrector
        self._cypher_query_corrector = None
        # User settings
        self._user_settings = user_settings
        # Language
        self._language = abbr_languages[language]
        # Show results
        self._verbose = verbose
        # Initialization
        self._request_information = None
        self._graph_schema = None
        self._generated_cypher = None 
        self._cypher_query_response = None
        self._question = None
        self._response = None
        self._recommendations_db_path = recommendations_db_path
        self._room_descriptions_db_path = room_descriptions_db_path
        # Connection with Neo4j DB
        self.connection_with_Neo4j()

        # Search Engine for Recommendations
        if self._recommendations_db_path is None or not os.path.isdir(self._recommendations_db_path):
            with open(recommendations_file) as json_file:
                recommendations = json.load(json_file)     
                       
            # Create recommendations VectorDB
            docs = [Document(page_content=recommendations[i]["question"], metadata={"index": i, "user":recommendations[i]["user"], "instructions": recommendations[i]["instructions"]}) for i in recommendations]
            self._recommendations_db = FAISS.from_documents(docs, embeddings)
            # Save index
            self._recommendations_db_path = 'Data/recommendations_db'
            self._recommendations_db.save_local(self._recommendations_db_path)
        else:
            print('[INFO] Loading recommendation DB')
            self._recommendations_db = FAISS.load_local(self._recommendations_db_path, embeddings)

        # Search Engine for Room descriptions
        if self._room_descriptions_db_path is None or not os.path.isdir(self._room_descriptions_db_path):   
            # Get available rooms 
            query = """MATCH (r:ROOM) RETURN r.code as code, r.description as description"""  
            response = self._graph.query(query)

            room_descriptions = [item['description'] for item in response]
            room_descriptions = [Document(page_content=item["description"], metadata={"index": i, "code":item["code"]}) for i, item in enumerate(response)]
            self._room_descriptions_db = FAISS.from_documents(room_descriptions, embeddings)
            # Save index
            self._room_descriptions_db_path = 'Data/room_descriptions_db'
            self._room_descriptions_db.save_local(self._room_descriptions_db_path)        
        else:
            print('[INFO] Loading room-description DB')
            self._room_descriptions_db = FAISS.load_local(self._room_descriptions_db_path, embeddings)            
            
            
            
    def connection_with_Neo4j(self)->int:
        '''
            Connection with database
        '''
        try:
            # Connection with Neo4j
            self._graph = Neo4jGraph(
                url=self._neo4j_settings['connection_url'],
                username=self._neo4j_settings["username"],
                password=self._neo4j_settings["password"]
            )
            # Get graph schema
            self._graph_schema = construct_schema(self._graph.get_structured_schema, exclude_types=[], include_types=[])

            # Cypher corrector
            if self._cypher_corrector:
                corrector_schema = [
                    Schema(el["start"], el["type"], el["end"])
                    for el in self._graph.structured_schema.get("relationships")
                ]
                self._cypher_query_corrector = CypherQueryCorrector(corrector_schema)

            if self._verbose:
                print("[INFO] Connection with Neo4j established")

        except Exception as e:
            if self._verbose:
                print(color.RED + "[ERROR] Connection with Neo4j was not established" + color.END) 
            raise e


    def query(self, question:str="")->str:
        '''
            Get the question of the user and identify if the user wishes
            (i) information about a learner's performance
            (ii) Information from the KG

            After this is identified, the corresponding method/function is called

            Returns
            -------
            Response to query
        '''
        # Store question
        self._question = question
        # Check for offensive query provided by the user
        self._response = self._offensive_identification_chain.run({"question": question})
        
        # Step 1. Examine for offensive content
        if self._response != "Not offensive content":
            self._request_information = False
            self._generated_cypher = None
            self._cypher_query_response = None

            if self._verbose:
                print(color.RED + self._response + color.END)

            self._response = {"question": question, 
                              "text": self._response,
                              "retrieved_info_from_query": None}
            # Return response
            return translate(self._response["text"], language=self._language)
        else:
            print(color.GREEN + self._response + color.END)

        # # Step 2. Translate question
        self._question = translate(text=question, language="en")
        if self._verbose: 
            print(color.GREEN + "Query: " + color.END + self._question)



        # # Step 3. Username and Profile identification
        if self._user_settings["title"] == "Learner":               
            # Username and Profile identification
            try:
                response = self._question_transformation_chain.run({"question": self._question, "username": self._user_settings["username"]})
                print (response)
                if "not valid" in response.lower():
                    self._request_information = False
                    self._response = {
                        "question": question,
                        "text": None,
                        "grades_report": None,
                        "username": self._user_settings["username"],
                        "retrieved_info_from_query": None,
                    }
                    return f'Access denied. You only have permission to request information about username: {self._user_settings["username"]}'
                
                try:
                    (_, transformed_question) = ast.literal_eval(response)
                except Exception:
                    (_, transformed_question) = response[1:-1].split(",")
                    
                print("(Transformed) Query: ", color.GREEN + color.ITALICS + transformed_question + color.END)
                self._question = transformed_question
                            
            except Exception as e:
                print("ERROR: ", color.RED + str(e) + color.END)
                print("Response: ", response)
                
                self._request_information = False
                self._response = {
                    "question": question,
                    "text": None,
                    "grades_report": None,
                    "username": self._user_settings["username"],
                    "retrieved_info_from_query": None,
                }             
                return f'Access denied. You only have permission to request information about username: {self._user_settings["username"]}'
                

                    
                    
        if "information" in self._question:
            self._request_information = True
            # Retrieve information relative to learner's performance and engagement
            return translate(text=self.get_information(question=self._question), language=self._language)
        else:
            self._request_information = False
            # Send question to KG for
            # (i) creating the cypher query
            # (ii) getting the results from application of the cypher query on the KG
            return translate(text=self.query_on_KG(question=self._question), language=self._language)


    def recommendation(self)->str:
        '''
            Get recommendation based on user's query. Notice that two kinds of recommendation are available
            (i) Recommendation about a learner's performance
            (ii) Recommendation based on the retrieved information from the KG

            After this is identified, the corresponding method/function is called

            Returns
            -------
            Recommendation based on user's query
        '''        
        # Sanity check
        if self._request_information is None: 
            return {}
        
        # In case information on learner's performance was required
        if self._request_information:
            recommendations = self.send_information()
        # In case a query on the KG was performed and now a recommendation is requested
        else:
            recommendations = self.recommendations_from_KG()

        # Translate recommendation(s)
        if self._language != "en":
            recommendations = {key:translate(text=recommendations[key], language=self._language) for key in recommendations}

        return recommendations





    def query_on_KG(self, question:str="")->str:
        '''
            Send a query/question to Neo4j KG. The process is based on three main phases:
                1. Transform the user's question to Cypher query
                2. Apply Cypher query to KG
                3. Collect results and transform them in human understandable text

            Parameters
            ----------
            question: (str)
                User's query to be send to KG

            Returns
            -------
            response of the query to KG (str)
        '''
        # Transform the user's question to Cypher query
        self._generated_cypher = self._cypher_generation_chain.run({"question": question, "schema": self._graph_schema})
        # Sanity check
        if self._generated_cypher == 'IRRELEVANT':
            self._response = {"question": question, "text":"The question is probably irrelevant. Please try again."}
            return self._response["text"]
        # Extract cypher
        self._generated_cypher = extract_cypher(self._generated_cypher)
        # Apply cypher query corrector
        if self._cypher_query_corrector is not None:
            self._generated_cypher = self._cypher_query_corrector(self._generated_cypher)

        if self._verbose:
            print("Generated Cypher:\n" + color.GREEN + self._generated_cypher + color.END)

        # Apply Cypher query to the graph
        self._cypher_query_response = self._graph.query(self._generated_cypher)
        # Check if the query has return any information
        if self._cypher_query_response == []:
            return "No information can be provided"

        if self._verbose:
            print("Response:\n")
            print(color.GREEN + str(self._cypher_query_response) + color.END)


        # Reply to the query
        try:
            self._response = self._qa_chain({"question": question, 
                                             "context": self._cypher_query_response,
                                             "information": None})                
        except Exception as e:
            # TODO: raise exception
            if self._verbose:
                print(color.RED + "[ERROR] Response from GPT could not be retrieved" + color.END) 
                print(e)
            self._response = {"question": question, "text": ""}

        return self._response["text"]

      
    
    def recommendations_from_KG(self):
        '''
            Send recommendation to learners. This task has five main stages
                Step 1. Send "No recommendations can be made." in case no question and/or response are available
                Step 2. Send recommendation to the educator/user in case offensive language was used
                Step 3. Send recommendation to the educator/user in case he/she made an irrelevant question
                Step 4. Identify based on the question and the response if the recommendation refers to learners' IDs or profile 
                Step 4(a). Send tailored recommendations to each learner
                Step 4(b). Send recommendation to each learner of a profile
                Step 4(c). Send tailored recommendation to the educator about the activities

            Returns
            -------
            Dictionary with keys: learners' name or 'educator' and values the recommendation(s) (dict)
        '''

        # Case 1: If no question and/or response are available
        if self._question is None or self._response["text"] is None: 
            return {self._user_settings["username"]: "No recommendations can be made."}
        
        # Case 2: Offensive content is contained in the query's response
        if "offensive content" in self._response["text"].lower():
            prompt_explanations = "The teacher made a query for retrieving information about the lesson and received the following response."

            instructions = f"- Start the reply with: Dear {self._user_settings['name']},\n"
            instructions += "- Recommend to improve its language and do not use offensive content.\n"
            instructions += "- Use the response to provide detailed explanations about your recommendation.\n"
            instructions += "- Reply in a formal message form. Conclude the reply as Kind regards,"

            response = self._recommendation_chain({"prompt_explanations": prompt_explanations, 
                                                   "question": self._question, 
                                                   "response": self._response["text"],
                                                   "instructions": instructions})
            # TODO: Remove #
            # if self._verbose:
            #     print(color.GREEN + response["text"] + color.END)
            #     print(80*"-" + "\n")  
                
            return {self._user_settings["username"]: response["text"]}  # TODO: MERGE 2 & 3 

        # Case 3: In case the query is irrelevant
        if "irrelevant" in self._response["text"].lower() or "I don't have the information to answer your question" in self._response["text"]:
            prompt_explanations = "The teacher made a irrelevant query for retrieving information."

            instructions = f"- Start the reply with: Dear {self._user_settings['name']},\n"
            instructions += "- Recommend to update the question.\n"
            instructions += "- Provide a brief reply.\n"
            instructions += "- Highlight the teacher the necessity to conduct queries about the learning process and avoid irrelevant queries.\n"
            instructions += "- Reply in a formal message form. Conclude the reply as Kind regards,"


            response = self._recommendation_chain({"prompt_explanations":prompt_explanations, 
                                                   "question": self._question, 
                                                   "response": self._response["text"],
                                                   "instructions": instructions})

            # TODO: Remove #
            # if self._verbose:
            #     print(color.GREEN + response["text"] + color.END)
            #     print(80*"-" + "\n")  

            return {self._user_settings["username"]: response["text"]} 

        # Stage 4: ID and/or Profile identification
        try:
            response = self._id_chain.run({"question": self._question, "response": self._response["text"]})
            print("response: ", response)
            (learner_username, learner_profile) = ast.literal_eval(response)
        except Exception as e:
            print("ERROR: ", color.RED + str(e) + color.END)
            print("Response: ", response)
            return "Learner's username/profile were not identified for providing information"
            
        if self._verbose:
            print("Recommendations to Learners:", color.GREEN + str(learner_username) + color.END)
            print("Recommendations to Profile: ", color.GREEN + str(learner_profile) + color.END)                
        # Setup dictionary with recommendations
        d_recommendations = dict()     
                   
                   
        # Stage 4(a): Recommendation to the learner
        if learner_username is not None:
            if type(learner_username) != list and type(learner_username) != tuple: learner_username = [learner_username]
            for username in learner_username:
                # Include prompt in the query to the GPT
                prompt_explanations = "The teacher made a query for retrieving information about the progress of the learners and received the following response. Based on the instructions, create a message for sending customized recommendation to learner with username: {username}".replace("{username}", str(username))
                # Retrieve instructions
                search_results = self._recommendations_db.similarity_search(self._question, k=1983)
                for item in search_results:
                    if item.metadata["user"] == "learner":
                        instructions = item.metadata["instructions"]
                        break
                
                # Replace abbreviations
                if self._user_settings['title'] == "Educator":
                    instructions = instructions.replace("{name}", self._user_settings['name'])
                    instructions = instructions.replace("{title}", self._user_settings['title'])
                else:
                    instructions = instructions.replace("{name}", "augMENTOR")
                    instructions = instructions.replace("{title}", "")
                instructions = instructions.replace("{username}", str(username))
                    
                
                # Retrieve recommendation for a specific learner
                response = self._recommendation_chain({"prompt_explanations":prompt_explanations, 
                                                       "question": self._question, 
                                                       "response": self._response["text"],
                                                       "instructions": instructions})
                            
                # TODO: Remove #                
                # if self._verbose:
                #     print(color.GREEN + response["text"] + color.END)
                #     print(80*"-" + "\n")   
                    
                # Store recommendation
                d_recommendations[username] = response["text"]

            return d_recommendations



        # Stage 4(b): Recommendation to all learners in a profile
        if learner_profile is not None:
            # Include prompt in the query to the GPT
            prompt_explanations = "The teacher made a query for retrieving information about the progress of the learners and received the following response. Based on the instructions, create a message for sending customized recommendation to learner in profile {profile}".replace("{profile}", learner_profile)

            # TODO: check
            # Retrieve instructions
            search_results = self._recommendations_db.similarity_search(self._question, k=1983)
            for item in search_results:
                if item.metadata["user"] == "profile":
                    instructions = item.metadata["instructions"]
                    break
            # Replace abbreviations
            instructions = instructions.replace("{name}", self._user_settings['name'])
            instructions = instructions.replace("{title}", self._user_settings['title'])
            instructions = instructions.replace("{profile}", learner_profile)

            # Retrieve recommendation for a specific learner profile
            response = self._recommendation_chain({"prompt_explanations":prompt_explanations, 
                                                   "question": self._question, 
                                                   "response": self._response["text"],
                                                   "instructions": instructions})            
            # TODO: Remove #
            # if self._verbose:
            #     print(color.GREEN + response["text"] + color.END)
            #     print(80*"-" + "\n")  
            
            # Send the recommendation to all learners in the profile
            for item in self._graph.query("MATCH (l:LEARNER) WHERE l.profile = '{profile}' return l.username as ID".replace("{profile}", learner_profile)):
                d_recommendations[item['ID']] = response["text"]

            return d_recommendations
        
        
        # Stage 4(c): Recommendation to the educator
        # Include prompt in the query to the GPT
        prompt_explanations = "The teacher made a query for retrieving information about the lesson and received the following response."

        # Retrieve instructions
        search_results = self._recommendations_db.similarity_search(self._question, k=1983)
        for item in search_results:
            if item.metadata["user"] == "educator":
                instructions = item.metadata["instructions"]
                break            
        # Replace abbreviations
        instructions = instructions.replace("{name}", self._user_settings['name'])

        # Retrieve recommendation for a specific learner profile
        response = self._recommendation_chain({"prompt_explanations":prompt_explanations, 
                                               "question": self._question, 
                                               "response": self._response["text"],
                                               "instructions": instructions})
                    
        
        if self._verbose:
            print(color.GREEN + response["text"] + color.END)
            print(80*"-" + "\n")  

        return {self._user_settings["username"]: response["text"]} 




    def get_information(self, question:str="")->str:
        '''
            Send a query/question to Neo4j KG and request information about learner's performance
            on a room, module and/or path

            Parameters
            ----------
            question: (str)
                User's query

            Returns
            -------
            information about learner's performance (str)
        '''

        # Extract information from the query: Learner ID, profile, Module ID, 
        response = self._request_information_chain.run({"question": question})
        if self._verbose:
            print("(<username>, <profile>, <room_code>, <module_URL>, <path_code>, <suggestion>) = " + color.GREEN + response + color.END)
            print( ast.literal_eval(response))
        try:
            (username, profile, room_code, moduleURL, path_code, suggestion) = ast.literal_eval(response)

            # Pre-processing
            if username != None: username = str(username)
            if profile != None: profile = str(profile)
            if type(room_code) == str: room_code=[room_code]
            if type(moduleURL) == str: moduleURL=[moduleURL]
            if type(path_code) == str: path_code=[path_code]
            retrieved_info_from_query = {'username': username, 'profile': profile, 'room_code': room_code, 'moduleURL': moduleURL, 'path_code': path_code, 'suggestion': suggestion}
            
        except Exception as e:
            print("ERROR: ", color.RED + e + color.END)
            print("Response: ", response)
            return "Username, profile, Rooms' code, Modules' URL and Paths code were not identified for providing information"
            

        if self._verbose:
            print("Username:", color.GREEN + str(username) + color.END)
            print("Profile: ", color.GREEN + str(profile) + color.END)
            print("Room code:", color.GREEN + str(room_code) + color.END)
            print("Module URL:", color.GREEN + str(moduleURL) + color.END)
            print("Path code:", color.GREEN + str(path_code) + color.END)
            print("Suggestion:", color.GREEN + str(suggestion) + color.END)

        # Sanity check        
        if username is None and profile is None and suggestion == False:
            return "Learner's username and/or profile were not identified for providing information"
        
        # Reply to the query for a module or for all active module(s)
        if suggestion == True:
            grades_report, information_text = get_suggestion_about_learning(faiss_index=self._room_descriptions_db, username=username, graph=self._graph, question=question)
        elif room_code is not None:
            # Get information for all selected rooms            
            grades_report, information_text = get_learner_information_rooms(graph=self._graph, username=username, room_code=room_code, detailed_info=True)
        elif moduleURL is not None:
            # Get information for all selected modules            
            grades_report, information_text = get_learner_information_modules(graph=self._graph, username=username, moduleURL=moduleURL, detailed_info=False)
        elif path_code is not None:
            # Get information for all selected paths            
            grades_report, information_text = get_learner_information_paths(graph=self._graph, username=username, path_code=path_code, detailed_info=False) 
        else:
            # Get information for all registered rooms
            query =  f"""MATCH (l:LEARNER {{username:"{username}"}})-[:HAS]->(r:ROOM) return collect(r.code) as room_codes"""
            room_code = self._graph.query(query)[0]["room_codes"]
            grades_report, information_text = get_learner_information_rooms(graph=self._graph, username=username, room_code=room_code)
            

        # Identify learners' IDs to send the information message
        if username is not None:
            username = [username]
        else:
            # TODO: Identify learner belong to the same Profile for sending the recommendations
            username = [username]
            # # Get learners' IDs, which belond to the selected learner profile
            # query = f"""MATCH (l:LEARNER) WHERE l.profile = "{username}" RETURN l.Learner_ID as ID"""
            # learner_ID = [item["ID"] for item in self._graph.query(query)]
            # print("username: ", username)


        # Check if an ERROR occurs during the grades retrieval
        if grades_report == "":
            self._response = {"question": question,
                              "text": "No information can be provided",
                              "retrieved_info_from_query": retrieved_info_from_query}
        else:
            self._response = {"question": question, 
                              "text": information_text,
                              "grades_report": grades_report,
                              "username": username,
                              "retrieved_info_from_query": retrieved_info_from_query}
            
        return grades_report


    def send_information(self)->dict:
        '''
            Send recommendation to the learner based on its retrieved information

            Returns
            -------
            A dictionary with keys the learner IDs and values the recommendation in text form (dict)
        '''
        # Sanity check
        if self._question is None or self._response["text"] is None: return {}
        

        if self._response['retrieved_info_from_query']['suggestion']:
            intro = """A learner made a query to the Teacher for selecting a room for improving its knowledge on a specific subject. The rooms are actually classes that the learner is able to register. Your task is to recommend some rooms to the learner for improving its knowledge and performance on the subject in the query.

            In the Query section, there is the learner's query describing the subject that wishes to improve its knowledge."""
            
            instructions = """- Use the template for presenting each recommended room.
            - The Information section is authoritative, you must never doubt it or try to use your internal knowledge to correct it."""
            
            
            if "no available rooms" not in self._response["text"]:
                intro = """# Template
            Room: <room code>
            Recommendation: <A small paragraph with the recommendation why this room is recommended and highlight its reasoning>
            Relevance: <relevance score in %>"""

                instructions += """- At the end, highlight the learner to study the resources (videos and tutorial of each room) for improving his/her performance and contact with the educator for retrieving assistance."""
        else:
            intro = "The teacher received the following information about the student's scores and the number of correctly answered questions. The task is to provide recommendations to the learner based on the provided information. Notice that the score is independent from the number of correctly answered question. For getting the points from an answer the learner has to answer it correctly, before all other learners.\n"
            intro += """# Template
            Room: <room code>
            Performance: <provide information to the learner about his/her scores and the number of questions answered>
            Recommendation: <recommendation>"""
            
            instructions = """- Βriefly recommend the learner to study the resources (videos and tutorial of each room) for improving his/her performance.
            - If there are information about a room, use the template for presenting the recommendations.
            - Reply formally.
            - Give details and reasoning for the recommendations.
            """            
        
        if self._user_settings['title'] == "Educator":
            instructions += f"""- Start the reply with: "Dear Learner,".
            Conclude the reply as
            Kind regards,
            {self._user_settings['name']}
            Educator
            """
        else:
            instructions += f"""- Start the reply with: "Dear {self._user_settings['name']},".
            Conclude the reply as
            Kind regards,
            augMENTOR
            """            

        response = self._send_information_chain.run({"intro": intro,
                                                     "information": self._response["text"],
                                                     "instructions": instructions,
                                                     "name": self._user_settings['name'], 
                                                     "title": self._user_settings['title']})

        # Get room codes
        rooms = [x.split(": ")[-1] for x in self._response["text"].split("\n") if "Room:" in x]
        # Get status: "Completed", "Not completed", "No information"
        status = [x.split(": ")[-1] if "Status:" in x else "No information" for x in self._response["text"].split("\n") if "Status:" in x or "No information" in x]
        
        # Develop response
        response += "\n\n\n" + 100*"-" + "\n" + self.get_resources(rooms, status)

        # TODO: Remove #
        # if self._verbose:
        #     print(color.GREEN + response + color.END)
        #     print(80*"-" + "\n")  

        return {ID:response for ID in self._response["username"]}


    def get_resources(self, rooms:list=None, status:list=None)->str:
        
        # Get information about rooms which status is "Not completed"
        if status is not None:
            rooms = [room for (room, status) in zip(rooms, status) if status == "Not completed"]

        query = f"""MATCH (r:ROOM)
        WHERE r.code IN {rooms}
        RETURN r.code as code, r.videos as videos, r.tutorials as tutorials"""

        response = self._graph.query(query)
        
        reply = ""
        for item in response:
            reply += f"# Room: {item['code']}\n\n"
            # Sanity check
            if len(item['videos']) + len(item['tutorials']) == 0: continue
            if len(item['videos']) > 0:
                reply += "## Video resources\n"
                reply += f"{item['videos']}"
                reply += "\n\n"
            if len(item['tutorials']) > 0:
                reply += "## Tutorials\n"
                reply += f"{item['tutorials']}"
                reply += "\n\n\n"
                
        return reply
    
    def get_graph_schema(self)->str:
        '''
            Get Neo4j graph schema

            Returns
            -------
            graph schema, i.e. nodes, relationships, types, etc (str)
        '''
        return self._graph_schema


    def get_cypher_query(self)->str:
        '''
            Get last successful cypher query

            Returns
            -------
            Cypher query (str)
        '''
        return self._generated_cypher
    

    def get_cypher_query_response(self)->str:
        '''
            Get response from the last successfully contacted cypher query

            Returns
            -------
            response from cypher query (str)
        '''
        return self._cypher_query_response  
    

    def get_response(self)->dict:
        '''
            Get the response from the last successful query

            Returns
            -------
            The last successful response (str)
        '''
        return self._response
