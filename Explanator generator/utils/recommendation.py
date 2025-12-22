import ast
from langchain.chat_models import ChatOpenAI
from langchain.graphs import Neo4jGraph
from langchain.chains.llm import LLMChain
from langchain.chains.graph_qa.cypher import construct_schema, extract_cypher
from langchain.chains.graph_qa.cypher_utils import Schema, CypherQueryCorrector
from utils.translations import terms, no_guidelines_response
from utils.utils import color, available_metrics, include_links, strip_accents_and_lowercase, format_time, tesa_framework, clean_KG_query_response
from utils.information import get_learner_information, get_profile_information, get_module_information
from utils.translate_queries import translate
from utils.prompts import guidelines_prompt, learner_recommendation_prompt, educator_recommendation_about_course_prompt, educator_recommendation_about_learners_prompt
from utils.prompts import (
    CYPHER_GENERATION_PROMPT,
    CYPHER_QA_PROMPT,
    ID_IDENTIFICATION_PROMPT,
    RECOMMENDATION_PROMPT,
    REQUEST_INFORMATION_PROMPT,
    SEND_INFORMATION_PROMPT,
    OFFENSIVE_IDENTIFICATION_PROMPT,
    QUESTION_TRANSFORMATION_PROMPT
)

prompts = {
    "offensive_identification": OFFENSIVE_IDENTIFICATION_PROMPT,
    "cypher_generation_prompt": CYPHER_GENERATION_PROMPT,
    "cypher_qa_prompt": CYPHER_QA_PROMPT,
    "id_identification_prompt": ID_IDENTIFICATION_PROMPT,
    "recommendation_prompt": RECOMMENDATION_PROMPT,
    "request_information_prompt": REQUEST_INFORMATION_PROMPT,
    "send_information_prompt": SEND_INFORMATION_PROMPT,
    "question_transformation_prompt": QUESTION_TRANSFORMATION_PROMPT
}

def get_age_range(course_id:int=None):
    if course_id in [2, 4]: # Demo-1
        return "12-15"
    if course_id in [16, 33]: # Demo-2
        return "18-23"
    return "12-30"
    
class Recommendations:
    def __init__(self, neo4j_settings:dict=None, openai_settings:dict=None, cypher_corrector:bool=True,\
                 user_settings:dict=None, course_id:int=None, recommendations_file:dict=None, verbose:bool=False)->None:  
             
        # Neo4j Settings
        self._neo4j_settings = neo4j_settings
        # # Setup embeddings model
        # embeddings = OpenAIEmbeddings(openai_api_key=openai_settings["api_key"], chunk_size=1)        
        # Setup ChatGPT model
        # self._gpt = ChatOpenAI(model_name="gpt-3.5-turbo-0125", temperature=int(openai_settings["temperature"]), openai_api_key=openai_settings['api_key'])
        # self._llm = ChatOpenAI(model_name=openai_settings["model_name"], temperature=int(openai_settings["temperature"]), openai_api_key=openai_settings['api_key'])
        self._llm4 = ChatOpenAI(model_name="gpt-4.1-mini-2025-04-14", max_tokens=32768, temperature=int(openai_settings["temperature"]), openai_api_key=openai_settings['api_key'])
        
        # LLM Chains
        self._offensive_identification_chain = LLMChain(llm=self._llm4, prompt=prompts["offensive_identification"])
        self._question_transformation_chain = LLMChain(llm=self._llm4, prompt=prompts["question_transformation_prompt"])
        self._cypher_generation_chain = LLMChain(llm=self._llm4, prompt=prompts["cypher_generation_prompt"])
        self._qa_chain = LLMChain(llm=self._llm4, prompt=prompts["cypher_qa_prompt"])
        self._id_chain = LLMChain(llm=self._llm4, prompt=prompts["id_identification_prompt"])
        self._request_information_chain = LLMChain(llm=self._llm4, prompt=prompts["request_information_prompt"])
        self._recommendation_chain = LLMChain(llm=self._llm4, prompt=prompts["recommendation_prompt"])
        self._send_information_chain = LLMChain(llm=self._llm4, prompt=prompts["send_information_prompt"])
        # Cypher corrector
        self._cypher_corrector = cypher_corrector
        self._cypher_query_corrector = None
        # Show results
        self._verbose = verbose
        # # Recommendation (provided by the pilots for some use-case scenarios)        
        # self._recommendations_db_path = "Resources/Moodle_db"
        # Connection with Neo4j DB
        self.connection_with_Neo4j()
        # Get links
        self._d_links = self.get_links()
        
          
    def connection_with_Neo4j(self)->int:
        """
        Establishes a connection with the Neo4j database.

        This method initializes the connection to the Neo4j database using the provided connection details
        from the Neo4j settings (URL, username, and password). It also constructs the graph schema from the 
        database and, if required, initializes a Cypher query corrector based on the schema for better query 
        optimization and accuracy.

        If verbose mode is enabled, it prints a message confirming the successful connection.

        Returns:
            int: A status code indicating the success or failure of the connection (e.g., 1 for success, 0 for failure).

        Raises:
            Exception: If an error occurs while attempting to connect to Neo4j or during schema construction.
        """
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
                print("Connection with Neo4j established")

        except Exception as e:
            if self._verbose:
                print(color.RED + "Connection with Neo4j established" + color.END) 
            raise e


    def get_links(self):
        """
        Retrieves and organizes links for courses, modules, activities, and resources 
        from the graph database.

        Returns:
            dict: A dictionary mapping course IDs to their respective modules, activities, 
                and resources, formatted as Markdown links.
        """        
        d_links = {'english': {}, 'greek': {}, 'serbian': {}}
        
        for language in d_links:
            d = {}
            # Include MODULES' links
            query = """match (c:COURSE)-[]->(m:MODULE) return c.id as course_id, m.code as code, m.title as title, m.url as url"""
            for item in self._graph.query(query):
                if item['course_id'] not in d:
                    d[item['course_id']] = {}
                    
                d[item['course_id']][item['code']] = f"[{item['title']}]({item['url']})".replace("|","-")
                
            # Include ACTIVITIES' links
            query = """match (c:COURSE)-[]->(m:MODULE)-[]->(a:ACTIVITY)
                    return c.id as course_id, a.id as activity_id, a.type as type, a.title as title, a.url as url"""
            for item in self._graph.query(query):
                if item['course_id'] not in d:
                    d[item['course_id']] = {}
                    
                activity_type = terms[item['activity_id'].split(':')[0]][language]                
                d[item['course_id']][item['activity_id']] = f"{activity_type}: [{item['title']}]({item['url']})".replace("|","-")
                
            # Include RESOURCES' links
            query = """match (c:COURSE)-[]->(m:MODULE)-[]->(r:RESOURCE)
                    return c.id as course_id, r.id as resource_id, r.title as title, r.url as url"""
            for item in self._graph.query(query):
                if item['course_id'] not in d:
                    d[item['course_id']] = {}

                resource_type = terms[item['resource_id'].split(':')[0]][language]
                d[item['course_id']][item['resource_id']] = f"{resource_type}: [{item['title']}]({item['url']})".replace("|","-")

            # Sorting
            for key in d:
                d[key] = dict(sorted(d[key].items(), key=lambda item: item[0], reverse=True))
            # Include dictionary for the selected language
            d_links[language] = d
            
        return d_links

    
    def query(self, configuration:dict=None, question:str="")->str:
        """
        Handles the querying process for the system.

        This method processes the user's question through several steps:
        1. Checks for offensive content in the question and returns an appropriate response if detected.
        2. Translates the question into English if needed.
        3. Identifies the user profile (e.g., "Learner") and transforms the question based on the user's information.
        4. If the question contains information requests, it retrieves data related to the learner's performance and engagement.
        5. If the question requires querying the knowledge graph, it formulates and sends the query to the graph, retrieving relevant results.
        6. Returns the response, potentially including links, based on the information retrieved.

        Parameters:
            configuration (dict, optional): A dictionary containing settings and user-specific information.
            question (str): The question being asked by the user.

        Returns:
            str: The final response to the user's question, which may include translated content, results from the knowledge graph, or error messages.
            dict: The updated configuration dictionary containing the question and response details.
        """
        configuration['original_question'] = question
        configuration['question'] = question
        configuration['guidelines'] = None
        
        # Step 1. Examine for offensive content
        configuration['response'] = self._offensive_identification_chain.run({"question": configuration['question']})

        if configuration['response'] != "Not offensive content":
            configuration['request_information'] = False
            configuration['information_text'] = "Offensive content"
            configuration['shouldFetchRecommendations'] = False
            if self._verbose:
                print(color.PURPLE + f"[WARNING] {configuration['response']}" + color.END)

            return translate(configuration['response'], language=configuration['language']), configuration
        else:
            print(color.GREEN + f"[INFO] {configuration['response']}" + color.END)
        
        # Step 2. Translate question
        configuration['question'] = translate(text=question, language="english", method='LLM')
        if self._verbose: 
            print(color.GREEN + "Query: " + color.END + configuration['question'])

        # Step 3. Username and Profile identification
        if configuration['user_settings']["title"] == "Learner":               
            # Username and Profile identification
            try:
                response = self._question_transformation_chain.run({"question": configuration['question'], "username": configuration['user_settings']["username"]})
                if "not valid" in response.lower():
                    configuration['information_text'] = "Access denied"
                    configuration['shouldFetchRecommendations'] = False
                    if configuration['language'] == "english":
                        configuration['response'] = f"Access denied. You only have permission to request information about username: {configuration['user_settings']['username']}"
                    elif configuration['language'] == "greek":
                        configuration['response'] = f"Πρόσβαση απορρίφθηκε. Έχετε μόνο την άδεια να ζητήσετε πληροφορίες σχετικά με το όνομα χρήστη: {configuration['user_settings']['username']}"
                    elif configuration['language'] == "serbian":
                        configuration['response'] = f"Приступ је одбијен. Имате само дозволу да затражите информације о корисничком имену: {configuration['user_settings']['username']}"
                    else:
                        raise Exception("Wrong selected language")                
                    return configuration['response'], configuration
                # Valid question
                try:
                    (_, transformed_question) = ast.literal_eval(response)
                except Exception:
                    (_, transformed_question) = response[1:-1].split(",")
                    
                print(color.DARKCYAN + "Transformed Query: " + color.END + transformed_question)
                configuration['question'] = transformed_question                            
            except Exception as e:
                print("ERROR: ", color.RED + str(e) + color.END)
                configuration['information_text'] = "Access denied"
                configuration['shouldFetchRecommendations'] = False
                if configuration['language'] == "english":
                    configuration['response'] = f"Access denied. You only have permission to request information about username: {configuration['user_settings']['username']}"
                elif configuration['language'] == "greek":
                    configuration['response'] = f"Πρόσβαση απορρίφθηκε. Έχετε μόνο την άδεια να ζητήσετε πληροφορίες σχετικά με το όνομα χρήστη: {configuration['user_settings']['username']}"
                elif configuration['language'] == "serbian":
                    configuration['response'] = f"Приступ је одбијен. Имате само дозволу да затражите информације о корисничком имену: {configuration['user_settings']['username']}"
                else:
                    raise Exception("Wrong selected language")
                return configuration['response'], configuration         
        
        # Step 4. Retrieve response 
        configuration['shouldFetchRecommendations'] = True
        if "information" in configuration['question'] or "πληροφορ" in strip_accents_and_lowercase(configuration['original_question']) and "informac" in strip_accents_and_lowercase(configuration['original_question']):
            configuration['request_information'] = True
            # Retrieve information relative to learner's performance and engagement
            configuration = self.get_information(configuration=configuration)
        else:
            configuration['request_information'] = False
            # Send question to KG for
            # (i) creating the cypher query
            # (ii) getting the results from application of the cypher query on the KG
            configuration = self.query_on_KG(configuration=configuration)

        # Step 5. Retrieve guidelines
        if configuration["user_settings"]["title"].lower() in ['educator', 'viewer'] and "include_guidelines" in configuration and configuration["include_guidelines"]:
            print(color.GREEN + "[INFO] Generating guidelines for the educator" + color.END)
            information = f"Question: {configuration['original_question']}\nResponse: {configuration['response']}\n"
            prompt = guidelines_prompt.replace("{information}", information)
            prompt = prompt.replace("{tesa_framework}", tesa_framework)
            prompt = prompt.replace("{language}", configuration['language'])
            configuration['guidelines'] = self._send_information_chain.run({"prompt": prompt})
            # In case no guidelines can be provided
            if "STOP" in configuration['guidelines']:
                print(color.PURPLE + "[WARNING] No guidelines can be generated" + color.END)
                configuration['guidelines'] = no_guidelines_response[configuration['language']]
            configuration['guidelines'] = include_links(input=configuration['guidelines'], d_links=self._d_links[configuration['language']][configuration['course_id']])      
        else:
            print(color.PURPLE + "[WARNING] No guidelines can be provided" + color.END)
            configuration['guidelines'] = None

        # Include links and return response
        return include_links(input=configuration['response'], d_links=self._d_links[configuration['language']][configuration['course_id']]), configuration


    def recommendation(self, configuration:dict=None)->str:
        """
        Handles the generation of recommendations based on the user's input and settings.

        This method processes the user's request for recommendations through various cases:
        1. **Case 1**: If there is no question or response available, it returns a message indicating that no recommendations can be made.
        2. **Case 2**: If no information can be provided (e.g., due to lack of data), it returns a message explaining that no recommendations can be made.
        3. **Case 3**: If access is denied to the requested information, it returns a message explaining the access restrictions.
        4. **Case 4**: If information is available, it generates recommendations based on the learner's performance or queries from the knowledge graph, including relevant links.

        Parameters:
            configuration (dict, optional): A dictionary containing settings, user details, and the current state of the request.

        Returns:
            str: The final recommendation response, potentially including links based on the information retrieved or recommendations made.
        """         
        # Case 1: If no question and/or response are available
        if 'question' not in configuration or configuration['question'] is None or configuration['response'] is None:        
            if configuration['language'] == "english":
                response = f"Dear {configuration['user_settings']['username']},\n\nRegrettably, no recommendations can be made since there are no available data for the question: '{configuration['original_question']}'. Please try to rephrase your question with more details or contact the support team.\n\nBest regards,\naugMENTOR"
            elif configuration['language'] == "greek":
                response = f"Αγαπητέ/ή {configuration['user_settings']['username']},\n\nΔυστυχώς, δεν μπορούν να δοθούν συστάσεις καθώς δεν υπάρχουν διαθέσιμα δεδομένα για την ερώτηση: '{configuration['original_question']}'. Παρακαλώ δοκιμάστε να διατυπώσετε το ερώτημά σας με περισσότερες λεπτομέρειες ή επικοινωνήστε με την ομάδα υποστήριξης.\n\nΜε εκτίμηση,\naugMENTOR"
            elif configuration['language'] == "serbian":
                response = f"Poštovani/a {configuration['user_settings']['username']},\n\nNažalost, ne mogu se dati preporuke jer nema dostupnih podataka za pitanje: '{configuration['original_question']}'. Molimo vas da pokušate da formulišete vaše pitanje sa više detalja ili kontaktirate tim za podršku.\n\nS poštovanjem,\naugMENTOR"
            else:
                raise Exception("Wrong selected language")                
            return {configuration['user_settings']["username"]: response}
        
        # Case 2: If no information can be provided
        if configuration['information_text'] == "No information can be provided":
            if configuration['language'] == "english":
                response = f"Dear {configuration['user_settings']['username']},\n\nRegrettably, no recommendations can be made since there are no available data for the question: '{configuration['original_question']}'. Please try to rephrase your question with more details or contact the support team.\\nnBest regards,\naugMENTOR"
            elif configuration['language'] == "greek":
                response = f"Αγαπητέ/ή {configuration['user_settings']['username']},\n\nΔυστυχώς, δεν μπορούν να δοθούν συστάσεις καθώς δεν υπάρχουν διαθέσιμα δεδομένα για την ερώτηση: '{configuration['original_question']}'. Παρακαλώ δοκιμάστε να διατυπώσετε το ερώτημά σας με περισσότερες λεπτομέρειες ή επικοινωνήστε με την ομάδα υποστήριξης.\n\nΜε εκτίμηση,\naugMENTOR"
            elif configuration['language'] == "serbian":
                response = f"Poštovani/a {configuration['user_settings']['username']},\n\nNažalost, ne mogu se dati preporuke jer nema dostupnih podataka za pitanje: '{configuration['original_question']}'. Molimo vas da pokušate da formulišete vaše pitanje sa više detalja ili kontaktirate tim za podršku.\n\nS poštovanjem,\naugMENTOR"
            else:
                raise Exception("Wrong selected language")                 
            return {configuration['user_settings']["username"]: response}

        # Case 3: If access is denied
        if configuration['information_text'] == "Access denied":
            if configuration['language'] == "english":
                response = f"Dear {configuration['user_settings']['username']},\n\nRegrettably, no recommendations can be made since access to the requested information is currently restricted due to permission limitations for the question: '{configuration['original_question']}'. Please verify your access rights or reach out to the support team for further assistance.\n\nBest regards,\naugMENTOR"
            elif configuration['language'] == "greek":
                response = f"Αγαπητέ/ή {configuration['user_settings']['username']},\n\nΛυπούμαστε που δεν μπορούμε να παρέχουμε συστάσεις, καθώς η πρόσβαση στις ζητούμενες πληροφορίες είναι προς το παρόν περιορισμένη λόγω περιορισμών αδειών για την ερώτηση: '{configuration['original_question']}'. Παρακαλώ επαληθεύστε τα δικαιώματα πρόσβασής σας ή επικοινωνήστε με την ομάδα υποστήριξης για περαιτέρω βοήθεια.\n\nΜε εκτίμηση,\naugMENTOR"
            elif configuration['language'] == "serbian":
                response = f"Poštovani/a {configuration['user_settings']['username']},\n\nNažalost, ne možemo dati preporuke jer je pristup traženim informacijama trenutno ograničen zbog ograničenja dozvola za pitanje: '{configuration['original_question']}'. Molimo vas da proverite svoja prava pristupa ili kontaktirate tim za podršku radi dodatne pomoći.\n\nS poštovanjem,\naugMENTOR"
            else:
                raise Exception("Wrong selected language")                 
            return {configuration['user_settings']["username"]: response}
        
        # Case 4: Generate recommendation(s) 
        if configuration['request_information']:
            # In case information on learner's performance was required
            recommendations = self.send_information(configuration=configuration)
        else:
            # In case a query on the KG was performed and now a recommendation is requested
            recommendations = self.recommendations_from_KG(configuration=configuration)

        # Include links
        recommendations = include_links(input=recommendations, d_links=self._d_links[configuration['language']][configuration['course_id']])
   
        return recommendations


    def query_on_KG(self, configuration:dict=None)->str:
        """
        Executes a Cypher query on the knowledge graph based on the user's question.

        This method performs the following steps:
        1. Transforms the user's question into a Cypher query using the provided schema and course ID.
        2. Performs a sanity check to ensure the question is relevant. If deemed irrelevant, it returns a message indicating so.
        3. Applies a Cypher query corrector (if available) to refine the generated Cypher query.
        4. Executes the Cypher query against the graph and checks if any relevant information is returned.
        5. If no information is returned, it returns a message indicating that no information can be provided.
        6. If valid results are found, it uses a QA chain to generate a response based on the query results.

        Parameters:
            configuration (dict, optional): A dictionary containing settings, the question, course ID, and schema details.

        Returns:
            dict: The updated configuration dictionary containing the Cypher query response and any additional information or error messages.
        """
        # Transform the user's question to Cypher query
        configuration['generated_cypher'] = self._cypher_generation_chain.run({"course_id":configuration['course_id'], "question": configuration['question'], "schema": self._graph_schema})
        # Sanity check
        if configuration['generated_cypher'].lower() == 'irrelevant':
            configuration['shouldFetchRecommendations'] = False
            configuration['information_text'] = "Irrelevant question"
            if configuration['language'] == "english":
                configuration['response'] = "The question is probably irrelevant. Please try again."
            elif configuration['language'] == "greek":
                configuration['response'] = "Η ερώτηση είναι πιθανώς άσχετη. Παρακαλώ δοκιμάστε ξανά."
            elif configuration['language'] == "serbian":
                configuration['response'] = "Питање је вероватно неважно. Молимо покушајте поново."   
            else:
                raise Exception("Wrong selected language")  
            
            return configuration
        
        # Extract cypher
        configuration['generated_cypher'] = extract_cypher(configuration['generated_cypher'])
        # Apply cypher query corrector
        if self._cypher_query_corrector is not None:
            corrected_query = self._cypher_query_corrector(configuration['generated_cypher'])
            if len(corrected_query) > 0:
                configuration['generated_cypher'] = corrected_query
            else:
                print(color.PURPLE + "[WARNING] Query was not corrected" + color.END)

        if self._verbose:
            print("Generated Cypher:" + color.BLUE + configuration['generated_cypher'] + color.END)

        # Apply Cypher query to the graph
        response = self._graph.query(configuration['generated_cypher'])
        if response:
            # Clean None items & keep unique elements
            response = clean_KG_query_response(response)
            # Convert time in d:h:m:s
            configuration['cypher_query_response'] = [{k: format_time(time=v, language=configuration["language"]) if "time" in k else v for k, v in d.items() if v is not None} for d in response]
        else:
            configuration['cypher_query_response'] = []
            
        
        # Check if the query has return any information
        if not configuration['cypher_query_response']:
            if configuration['language'] == "english":
                configuration['response'] = f"There is no available information or information cannot be provided for the query: \"{configuration['question']}\""
            elif configuration['language'] == "greek":
                configuration['response'] = f"Δεν μπορούν να δοθούν ή δεν υπάρχουν πληροφορίες για το ερώτημα: \"{configuration['question']}\""
            elif configuration['language'] == "serbian":
                configuration['response'] =  f"Nema dostupnih informacija ili informacije ne mogu biti date za upit: \"{configuration['question']}\""
            else:
                raise Exception("Wrong selected language")
            configuration['shouldFetchRecommendations'] = False
            configuration['information_text'] = "No information can be provided"
            return configuration
        
        
        if self._verbose:
            print("Response: " + color.GREEN + str(configuration['cypher_query_response']) + "\n" + color.END)

        # Reply to the query
        configuration['response'] = self._qa_chain({"question": configuration['question'], 
                                                    "language": configuration['language'],
                                                    "context": configuration['cypher_query_response']})['text']   
        configuration['information_text'] = None         
        return configuration
  
    
    def recommendations_from_KG(self, configuration):
        """
        Generates recommendations based on the query's response from the knowledge graph.

        This method handles the following scenarios:
        1. **Case 1**: If offensive content is detected in the query's response, it generates a recommendation to improve language and avoid offensive content.
        2. **Case 2**: If the query is deemed irrelevant, it generates a recommendation to update the question and suggests focusing on relevant topics related to the learning process.
        3. **Case 3**: If the learner's username or profile is not identified, it returns an error message indicating that learner information could not be retrieved.
        4. **Case 4**: If a valid learner username/profile is identified, it generates customized recommendations based on the response and instructions, including specific recommendations for each learner.

        Parameters:
            configuration (dict): A dictionary containing settings, the learner's username, the question, and the response.

        Returns:
            dict: A dictionary containing the recommendations for each identified learner, with usernames as keys and the generated recommendation text as values.
        """
        # Case 1: Offensive content is contained in the query's response
        if configuration['information_text'] == "Offensive content":
            prompt_explanations = "The user made a query for retrieving information about the lesson and received the following response."

            instructions = f"- Start the reply with: Dear {configuration['user_settings']['username']},\n"
            instructions += "- Recommend to improve its language and do not use offensive content.\n"
            instructions += "- Use the response to provide detailed explanations about your recommendation.\n"
            instructions += "- Reply in a formal message form. Conclude the reply as Best regards,\naugMENTOR\n"

            response = self._recommendation_chain({"prompt_explanations": prompt_explanations, 
                                                   "question": configuration['question'],
                                                   "response": configuration['response'],
                                                   "characteristics": "",
                                                   "limitations": "",
                                                   "recommendations": "",
                                                   "instructions": instructions,
                                                   "language": configuration['language'],
                                                   })
            if self._verbose:
                print(color.GREEN + response["text"] + color.END)
                print(80*"-" + "\n")  
                
            return {configuration['user_settings']["username"]: response["text"]}

        # Case 2: In case the query is irrelevant
        if configuration['information_text'] == "Irrelevant question":
            prompt_explanations = "The user made a irrelevant query for retrieving information."

            instructions = f"- Start the reply with: Dear {configuration['user_settings']['username']},\n"
            instructions += "- Recommend to update the question.\n"
            instructions += "- Provide a brief reply.\n"
            instructions += "- Highlight the educator the necessity to conduct queries about the learning process and avoid irrelevant queries.\n"
            instructions += "- Reply in a formal message form. Conclude the reply as Best regards,\naugMENTOR\n"
            
            response = self._recommendation_chain({"prompt_explanations":prompt_explanations, 
                                                   "question": configuration['question'], 
                                                   "response": configuration['response'],
                                                   "characteristics": "",
                                                   "limitations": "",
                                                   "recommendations": "",                                             
                                                   "instructions": instructions,
                                                   "language": configuration['language']})

            if self._verbose:
                print(color.GREEN + response["text"] + color.END)
                print(80*"-" + "\n")  

            return {configuration['user_settings']["username"]: response["text"]} 

        # Stage 3: Username and/or Profile identification
        try:
            response = self._id_chain.run({"question": configuration['question'], "response": configuration['response']})
            (learner_username, learner_profile) = ast.literal_eval(response)
        except Exception as e:
            print("ERROR: ", color.RED + str(e) + color.END)
            print("Response: ", response)
            if configuration['language'] == "english":
                return "Learner's usernames/profiles were not identified for providing information"
            elif configuration['language'] == "greek":
                return "Δεν εντοπίστηκαν ονόματα χρηστών/προφίλ για την παροχή πληροφοριών."
            elif configuration['language'] == "serbian":
                return "Нису пронађена корисничка имена/профили за пружање информација."
            else:
                raise Exception("Wrong selected language")
        
        # Convert to list
        if learner_username:
            if type(learner_username) is not list and type(learner_username) is not tuple: 
                learner_username = [learner_username]

        if self._verbose:
            print("Recommendations to username: ", color.GREEN + str(learner_username) + color.END)
            print("Recommendations to profile:  ", color.GREEN + str(learner_profile) + color.END)
                        

        # Setup dictionary with recommendations
        d_recommendations = dict()
        # Stege 4(a): Recommendation to the learner
        if learner_username and len(learner_username) == 1:
            username = learner_username[0]
            # Include prompt in the query to the GPT
            if configuration['user_settings']['title'] == "Educator":
                prompt_explanations = f"The educator made a query for retrieving information about the progress of a learner and received the following response. Based on the instructions, create a message for sending customized recommendation to learner with username: '{username}'"
            else:
                prompt_explanations = f"The learner made a query for retrieving information about his/her progress and received the following response. Based on the instructions, create a message for sending customized recommendation to learner with username: '{username}'"
                
            # Get learner's profile description
            query = f"""MATCH (l:LEARNER)-[r]->(p:PROFILE) where l.username = "{username}" and r.course_id = {configuration['course_id']} return p.description as description"""
            response = self._graph.query(query)
            # Get learner's characteristics
            characteristics = ""
            if response:
                characteristics = "# Learner's characteristics\n"
                characteristics += f"Learner: {username} belongs to the learners with {response[0]['description'].split('Description:')[0].split('Characteristics:')[-1].strip()}\n"
            # Include summary of performance or Not
            limitations = "## Limitations\n<Present to each learner its limitations based on its grades/performance and provided 'Reasoning'>\n"
            # Include recommendation instructions
            recommendations_instructions = "## Recommendations\n"
            recommendations_instructions += "<Recommendations to the learner for addressing the learner's limitations found in 'Reasoning' based on TESA framework (without any reference to the framework)>\n"
            recommendations_instructions += "<Recommendations to the learner for improving its performance on the metrics and not on each activity and learner's characteristics>\n"              
            
            # # Retrieve instructions
            # search_results = self._recommendations_db.similarity_search(configuration['question'], k=1983)
            # for item in search_results:
            #     if item.metadata["receiver"] == "Learner":
            #         instructions = item.metadata["instructions"]
            #         break
            instructions = "- Reply in a formal message form. Conclude the reply as \nBest regards,\n{name}\n"
            instructions += "- [IMPORTANT] Structure your response in Markdown format, but do not wrap the output in a code block. Present the facts and include a last section with the recommendations\n"
            instructions += "- For each activity grade include the corresponding 'Reasoning' IF AVAILABLE in Section: Information.\n"
            instructions += "- [IMPORTANT] The recommendations MUST AIM TO address the learner's limitations found in 'Reasoning'.\n"
            instructions += "- [IMPORTANT] The recommendations focus on improving its performance on the metrics and not on each activity.\n"
            if characteristics:
                instructions += "- [IMPORTANT] The recommendations must be based on learner's characteristics and provide a reference to these characteristics.\n"
            instructions += "- [IMPORTANT] All the recommendation must be based on TESA framework without any reference to the framework.\n"
            instructions += f"- [IMPORTANT] Reply in a friendly, understandable way, while still being formal enough to show guidance, written in a way that is easy for a {get_age_range(course_id=configuration['course_id'])}-year-old to understand.\n"
            # Replace abbreviations
            if configuration['user_settings']['title'] == "Educator":
                instructions = instructions.replace("{name}", configuration['user_settings']['username'])
                instructions = instructions.replace("{title}", configuration['user_settings']['title'])
            else:
                instructions = instructions.replace("{name}", "augMENTOR")
                instructions = instructions.replace("{title}", "")
            instructions = instructions.replace("{username}", str(username))
            
            # Retrieve recommendation for a specific learner
            response = self._recommendation_chain({"prompt_explanations": prompt_explanations, 
                                                    "question": configuration['question'], 
                                                    "response": configuration['response'],
                                                    "characteristics": characteristics,
                                                    "limitations": limitations,
                                                    "recommendations": recommendations_instructions,
                                                    "instructions": instructions,
                                                    "language": configuration['language']})
                        
            if self._verbose:
                print(color.GREEN + response["text"] + color.END)
                print(80*"-" + "\n")   
                
            # Store recommendation
            d_recommendations[username] = response["text"]
            return d_recommendations
        
        
        # Stege 4(b): Recommendation to the Educator about learners' performance
        if learner_username and len(learner_username) > 1:
            prompt_explanations = f"The educator made a query for retrieving information about the progress of {len(learner_username)} learners and received the following response. Based on the instructions, create a message for customized recommendations to the Educator for improving the class and the learners' performance on Cognitive knowledge and 4Cs skills: Creativity, Collaboration, Critical thinking, Communication.\n"
            prompt_explanations += "Your task is to provide recommendations and reasoning to the educator based on the information according to TESA Framework. Study carefully TESA Framework and provide recommendations for improving 4Cs\n"
            prompt_explanations += f"{tesa_framework}\n"
            
            # Get learner's profile description
            query = f"""MATCH (l:LEARNER)-[r]->(p:PROFILE) where l.username in {learner_username} and r.course_id = {configuration['course_id']} return l.username as username, p.description as description"""
            response = self._graph.query(query)
            # Get learner's characteristics
            characteristics = ""
            if response:
                characteristics = "# Learner's characteristics\n"
                for item in response:
                    characteristics += f"Learner's {item['username']} belongs to the learners with {item['description'].split('Description:')[0].split('Characteristics:')[-1].strip()}\n"
            # Include limitations
            limitations = "## Limitations\n<Present to each learner its limitations based on its grades/performance and provided 'Reasoning'>\n"    
            # Include Recommendation template
            recommendations_instructions = "## Recommendations\n"
            if configuration['user_settings']['title'] == "Educator":
                recommendations_instructions += "<Recommendations to the learner for addressing the learner's limitations found in 'Reasoning' based on TESA framework (including a reference)>\n"
                recommendations_instructions += "<Recommendations to the learner for improving its performance on the metrics and not on each activity and learner's characteristics>\n"
            else:
                recommendations_instructions += "<Recommendations to the learner for addressing the learner's limitations found in 'Reasoning' based on TESA framework (without any reference to the framework)>\n"
                recommendations_instructions += "<Recommendations to the learner for improving its performance on the metrics and not on each activity and learner's characteristics>\n"              
                    
            # # Retrieve instructions
            # search_results = self._recommendations_db.similarity_search(configuration['question'], k=1983)
            # for item in search_results:
            #     if item.metadata["receiver"] == "Learner":
            #         instructions = item.metadata["instructions"]
            #         break
            instructions = "- Reply in a formal message form. Conclude the reply as \nBest regards,\n{name}\n"
            instructions += "- [IMPORTANT] Structure your response in Markdown format, but do not wrap the output in a code block. Present the facts and include a last section with the recommendations\n"
            instructions += "- [IMPORTANT] The recommendations MUST AIM TO address the learner's limitations found in 'Reasoning'.\n"
            instructions += "- [IMPORTANT] The recommendations focus on improving the learner's performance on the 4Cs skills.\n"
            if characteristics:
                instructions += "- [IMPORTANT] The recommendations must be based on learner's characteristics\n"
            # Replace abbreviations
            instructions = instructions.replace("{name}", configuration['user_settings']['username'])
            instructions = instructions.replace("{title}", configuration['user_settings']['title'])
            
            # Retrieve recommendation for a specific learner
            response = self._recommendation_chain({"prompt_explanations": prompt_explanations, 
                                                    "question": configuration['question'], 
                                                    "response": configuration['response'],
                                                    "characteristics": characteristics,
                                                    "limitations": limitations,
                                                    "recommendations": recommendations_instructions,
                                                    "instructions": instructions,
                                                    "language": configuration['language']})
                        
            if self._verbose:
                print(color.GREEN + response["text"] + color.END)
                print(80*"-" + "\n")   
                
            # Store recommendation to the educator
            d_recommendations[configuration['user_settings']["username"]] = response["text"]
            return d_recommendations
        
                        
        # Stege 4(c): Recommendation to all learners in a profile
        if learner_profile is not None:
            # Include prompt in the query to the GPT
            prompt_explanations = "The educator made a query for retrieving information about the progress of the learners and received the following response. Based on the instructions, create a message for sending customized recommendation to learner in profile {profile}".replace("{profile}", learner_profile)
            # Include Recommendation template
            recommendations_instructions = "## Recommendations\n"
            if configuration['user_settings']['title'] == "Educator":
                recommendations_instructions += "<Recommendations to the learner for addressing the learner's limitations found in 'Reasoning' based on TESA framework (including a reference)>\n"
                recommendations_instructions += "<Recommendations to the learner for improving its performance on the metrics and not on each activity and learner's characteristics>\n"
            else:
                recommendations_instructions += "<Recommendations to the learner for addressing the learner's limitations found in 'Reasoning' based on TESA framework (without any reference to the framework)>\n"
                recommendations_instructions += "<Recommendations to the learner for improving its performance on the metrics and not on each activity and learner's characteristics>\n"              
            
            # # Retrieve instructions (Updated)
            # search_results = self._recommendations_db.similarity_search(configuration['question'], k=1983)
            # for item in search_results:
            #     if item.metadata["receiver"] == "Profile":
            #         instructions = item.metadata["instructions"]
            #         break
            # Replace abbreviations
            instructions = "- Reply in a formal message form. Conclude the reply as \nBest regards,\n{name}\n"
            instructions += "- Start your answer: Dear Learner in profile {profile}\n"
            instructions += "- [IMPORTANT] Structure your response in Markdown format, but do not wrap the output in a code block. Present the facts and include a last section with the recommendations\n"
            instructions += "- [IMPORTANT] The recommendations MUST AIM TO address the learner's limitations found in 'Reasoning'.\n"
            instructions += "- [IMPORTANT] The recommendations focus on improving the learner's performance on the 4Cs skills.\n"
            instructions += f"- [IMPORTANT] Reply in a friendly, understandable way, while still being formal enough to show guidance, written in a way that is easy for a {get_age_range(course_id=configuration['course_id'])}-year-old to understand.\n"                              
            instructions = instructions.replace("{name}", configuration['user_settings']['username'])
            instructions = instructions.replace("{title}", configuration['user_settings']['title'])
            instructions = instructions.replace("{profile}", learner_profile)
            
            # Retrieve recommendation for a specific learner profile
            response = self._recommendation_chain({"prompt_explanations":prompt_explanations, 
                                                   "question": configuration['question'], 
                                                   "response": configuration['response'],
                                                   "characteristics": "",
                                                   "limitations": "",    
                                                   "recommendations": recommendations_instructions,                                               
                                                   "instructions": instructions,
                                                   "language": configuration['language']})
                        
            
            if self._verbose:
                print(color.GREEN + response["text"] + color.END)
                print(80*"-" + "\n")  
            # Send the recommendation to all learners in the profile
            for item in self._graph.query("MATCH (l:LEARNER) WHERE l.profile = '{profile}' return l.username as username".replace("{profile}", learner_profile)):
                d_recommendations[item['username']] = response["text"]

            return d_recommendations
                
        
        # Stege 4(c): Recommendation to the user
        # Include prompt in the query to the GPT
        if configuration['user_settings']['title'] == "Educator":
            prompt_explanations = "The educator made a query for retrieving information about the lesson and received the following response."
        else:
            prompt_explanations = f"The learner with username: '{configuration['user_settings']['username']}' made a query for retrieving information and received the following response."

        recommendations_instructions = "## Recommendations\n"
        if configuration['user_settings']['title'] == "Educator":
            recommendations_instructions += "<Recommendations to the learner for addressing the learner's limitations found in 'Reasoning' based on TESA framework (including a reference)>\n"
            recommendations_instructions += "<Recommendations to the learner for improving its performance on the metrics and not on each activity and learner's characteristics>\n"
        else:
            recommendations_instructions += "<Recommendations to the learner for addressing the learner's limitations found in 'Reasoning' based on TESA framework (without any reference to the framework)>\n"
            recommendations_instructions += "<Recommendations to the learner for improving its performance on the metrics and not on each activity and learner's characteristics>\n"              
        
        # Retrieve instructions (Updated)
        # search_results = self._recommendations_db.similarity_search(configuration['question'], k=1983)
        # instructions = search_results[0].metadata["instructions"]
        instructions = "- Reply in a formal message form. Conclude the reply as \nBest regards,\n{name}\n"
        instructions += f"- Start with Dear {configuration['user_settings']['username']}\n"
        instructions += "- [IMPORTANT] Structure your response in Markdown format, but do not wrap the output in a code block. Present the facts and include a last section with the recommendations\n"
        instructions += "- [IMPORTANT] The recommendations MUST AIM TO address the learner's limitations found in 'Reasoning'.\n"
        instructions += "- [IMPORTANT] The recommendations focus on improving the learner's performance on the 4Cs skills.\n"           
        if configuration['user_settings']['title'] != "Educator":
            instructions += f"- [IMPORTANT] Reply in a friendly, understandable way, while still being formal enough to show guidance, written in a way that is easy for a {get_age_range(course_id=configuration['course_id'])}-year-old to understand.\n"                             
        # Replace abbreviations
        instructions = instructions.replace("{name}", "augMENTOR")
        instructions = instructions.replace("{title}", "")
        # Retrieve recommendation for a specific learner profile
        response = self._recommendation_chain({"prompt_explanations":prompt_explanations, 
                                               "question": configuration['question'], 
                                               "response": configuration['response'],
                                               "characteristics": "",
                                               "limitations": "",
                                               "recommendations": recommendations_instructions,                                            
                                               "instructions": instructions,
                                               "language": configuration['language']})
                     

        if self._verbose:
            print(color.GREEN + response["text"] + color.END)
            print(80*"-" + "\n")  

        return {configuration['user_settings']["username"]: response["text"]} 


    def get_information(self, configuration:dict=None)->str:
        """
        Extracts information from a user's query, such as learner username, learner profile, metrics, and module IDs.

        This method performs the following tasks:
        1. Extracts the learner's username, profile, requested metrics, and module IDs from the query using a predefined chain.
        2. Preprocesses the extracted information, including sanitizing and validating the extracted values.
        3. Retrieves relevant information from the graph based on the learner's username, profile, and requested metrics.
        4. Constructs and returns a response with the retrieved information or a message indicating that no information is available.

        Parameters:
            configuration (dict): A dictionary containing settings, the question, and relevant user data such as course ID and language.

        Returns:
            dict: A dictionary containing the response, retrieved information, and any relevant error messages if no information could be provided.
        """
        # Extract information from the query: Learner username, Learner profile, Module ID, 
        response = self._request_information_chain.run({"question": configuration['question']})
        if self._verbose:
            print(color.BLUE + "(<username>, <profile>, <Metrics>, <Module IDs>) = " + color.END + response)

        try:
            (learner_username, learner_profile, metrics, module_IDs) = ast.literal_eval(response)
            # Preprocess
            if learner_username and type(learner_username) is not list and learner_username.lower() == "none": learner_username = None
            learner_profile = learner_profile.upper() if learner_profile else None
            module_IDs = None if module_IDs is None else [module_ID.upper() for module_ID in module_IDs]
            if not learner_username and not learner_profile and not module_IDs:
                raise Exception("Learner's username, profile or Module IDs were not identified for providing information")
            if metrics == ["ALL"]:
                metrics = available_metrics
            elif metrics: 
                metrics = [m for m in available_metrics if m in metrics] # Sanity check. Keep only selected metrics
        except Exception as e:
            print(color.RED + f"[ERROR] {e}" + color.END)
            print("LLM response: ", response)
            configuration['shouldFetchRecommendations'] = False
            configuration['information_text'] = "No information can be provided"
            if configuration['language'] == "english":
                configuration['response'] = f"There is no available information or information cannot be provided for the query: \"{configuration['question']}\""
            elif configuration['language'] == "greek":
                configuration['response'] = f"Δεν μπορούν να δοθούν ή δεν υπάρχουν πληροφορίες για το ερώτημα: \"{configuration['question']}\""
            elif configuration['language'] == "serbian":
                configuration['response'] =  f"Nema dostupnih informacija ili informacije ne mogu biti date za upit: \"{configuration['question']}\""
            else:
                raise Exception("Wrong selected language")

            return configuration    

        
        # Reply to the query for a module or for all active module(s)
        if learner_username:
            if learner_username == ["ALL"]:
                grades_report, information_text = get_module_information(graph=self._graph, 
                                                                        course_id=configuration['course_id'], 
                                                                        modules=module_IDs, 
                                                                        requested_metrics=metrics,
                                                                        language=configuration['language'],
                                                                        include_evaluation=False) 
            else:                
                grades_report, information_text = get_learner_information(graph=self._graph, 
                                                                        course_id=configuration['course_id'], 
                                                                        username=learner_username, 
                                                                        modules=module_IDs, 
                                                                        requested_metrics=metrics,
                                                                        language=configuration['language'])
        elif learner_profile:
            grades_report, information_text = get_profile_information(graph=self._graph, 
                                                                     course_id=configuration['course_id'], 
                                                                     profile=learner_profile, 
                                                                     modules=module_IDs, 
                                                                     requested_metrics=metrics,
                                                                     language=configuration['language'])
        elif module_IDs:
            grades_report, information_text = get_module_information(graph=self._graph, 
                                                                     course_id=configuration['course_id'], 
                                                                     modules=module_IDs, 
                                                                     requested_metrics=metrics,
                                                                     language=configuration['language'])   
                                             
        # Identify learners' usernames to send the information message
        if learner_username and type(learner_username) is not list:
            learner_username = [learner_username]
        if learner_profile and type(learner_profile) is not list:
            learner_profile = [learner_profile]
        # Store information
        retrieved_info_from_query = {'username': learner_username, 'profile': learner_profile, 'module_IDs': module_IDs, 'metrics': metrics}

        # Check if an ERROR occurs during the grades retrieval
        if grades_report == "":
            configuration['shouldFetchRecommendations'] = False
            configuration['information_text'] = "No information can be provided"
            if configuration['language'] == "english":
                configuration['response'] = f"There is no available information or information cannot be provided for the query: \"{configuration['question']}\""
            elif configuration['language'] == "greek":
                configuration['response'] = f"Δεν μπορούν να δοθούν ή δεν υπάρχουν πληροφορίες για το ερώτημα: \"{configuration['question']}\""
            elif configuration['language'] == "serbian":
                configuration['response'] =  f"Nema dostupnih informacija ili informacije ne mogu biti date za upit: \"{configuration['question']}\""
            else:
                raise Exception("Wrong selected language")
        else:
            configuration["information_text"] = information_text        
            configuration["response"] = grades_report
            configuration["retrieved_info_from_query"] = retrieved_info_from_query
            
        return configuration


    def send_information(self, configuration:dict=None)->dict:
        """
        Sends information to the learner or educator based on the query and response provided.

        This method performs the following tasks:
        1. If no question or response is provided, it returns an empty dictionary.
        2. If no information is available for the given question, it constructs a response notifying the user that no recommendations can be made.
        3. If information is available, the method extracts relevant metrics from the information text, then generates and sends a recommendation based on the learner's performance or query.

        Parameters:
            configuration (dict): A dictionary containing the question, response, information text, language, user settings (e.g., username and title), and retrieved information.

        Returns:
            dict: A dictionary where the key is the username of the recipient(s), and the value is the response message containing recommendations or information.
        """       
        # Case 1: Provide recommendation based on learners' performance
        if configuration['retrieved_info_from_query']['username']  and configuration['retrieved_info_from_query']['username'] != ["ALL"]:
            # Get performance metrics            
            metrics = [metric for metric in available_metrics if metric.lower() in configuration['information_text'].lower()]
            # Get Learner characteristics
            username = configuration['retrieved_info_from_query']['username'][0]
            # Get information about learner's profile
            query = f"""MATCH (l:LEARNER)-[r]->(p:PROFILE) where l.username = "{username}" and r.course_id = {configuration['course_id']} return p.description as description"""
            response = self._graph.query(query)
            characteristics = ""
            if response:
                characteristics = "# Learner's characteristics\n"
                characteristics += f"Learner: {username} belongs to the learners with {response[0]['description'].split('Description:')[0].split('Characteristics:')[-1].strip()}\n"
            # Create response template
            template = """# Template
    ## <Metric>
    - **Average grade:** <average grade>
    - **Analysis:** <detailed report of key observations about each ACTIVITY to the learner i.e. (1) activity grades, (2) highlight the 'Reasoning' for each grade, and (3) highlight learners difficulties>
    - **Limitations:** <report identified limitations by taking into consideration the learner's characteristics or "-" if none>
    - **Recommendation:** <Provide recommendations based on TESA framework (without explicit reference) how to address the limitations highlighed in 'Reasoning' in bullets.>\n\n"""
            # Create prompt
            prompt = learner_recommendation_prompt.replace("{metrics}", ", ".join(metrics))
            prompt = prompt.replace("{age}", get_age_range(course_id=configuration['course_id']))
            prompt = prompt.replace("{information}", configuration['information_text'])
            prompt = prompt.replace("{template}", template)
            prompt = prompt.replace("{characteristics}", characteristics)
            prompt = prompt.replace("{tesa_framework}", tesa_framework)
            prompt = prompt.replace("{information}", configuration['information_text'])
            prompt = prompt.replace("{language}", configuration['language'])            
            if configuration['user_settings']['title'] == "Educator":
                prompt = prompt.replace("{name}", configuration['user_settings']['username'])
                prompt = prompt.replace("{title}", configuration['user_settings']['title'])            
            else:
                prompt = prompt.replace("{name}", "augMENTOR")
                prompt = prompt.replace("{title}", "")
            # Get recommendation
            response = self._send_information_chain.run({"prompt": prompt})
            if self._verbose:
                print(color.GREEN + response + color.END)
                print(80*"-" + "\n")  

            # Send the recommendation to a learner
            return {username: response}

        # Case 2: Provide recommendation to the educator about learners' performance in a profile
        if configuration['retrieved_info_from_query']['profile']:
            # Get performance metrics            
            metrics = [metric for metric in available_metrics if metric.lower() in configuration['information_text'].lower()]
            # Get the characteristics of the learners belonging to the profile 
            profile = configuration['retrieved_info_from_query']['profile'][0]
            query = f"""MATCH (p:PROFILE) where p.name = "{profile}" return p.description as description"""
            response = self._graph.query(query)                
            characteristics = "# Learners' characteristics\n"
            characteristics += f"Learners belonging to '{profile}' are characterized as {response[0]['description'].split('Description:')[0].split('Characteristics:')[-1].strip()}\n"
            # Create response template
            template = """# Template
    ## <Metric>
    - **Average grade:** <average grade>
    - **Analysis:** <detailed report of key observations about each ACTIVITY to the learner i.e. (1) activity grades, (2) highlight the 'Reasoning' for each grade, and (3) highlight learners difficulties>
    - **Limitations:** <report identified limitations by taking into consideration the learner's characteristics or "-" if none>
    - **Recommendation:** <Provide recommendations based on TESA framework (include reference) how to address the limitations highlighed in 'Reasoning' in bullets.>\n\n"""
            # Create prompt
            prompt = educator_recommendation_about_learners_prompt.replace("{metrics}", ", ".join(metrics))
            prompt = prompt.replace("{information}", configuration['information_text'])
            prompt = prompt.replace("{template}", template)
            prompt = prompt.replace("{characteristics}", characteristics)
            prompt = prompt.replace("{tesa_framework}", tesa_framework)
            prompt = prompt.replace("{information}", configuration['information_text'])
            prompt = prompt.replace("{language}", configuration['language'])            
            if configuration['user_settings']['title'] == "Educator":
                prompt = prompt.replace("{name}", configuration['user_settings']['username'])
                prompt = prompt.replace("{title}", configuration['user_settings']['title'])            
            # Get recommendation
            response = self._send_information_chain.run({"prompt": prompt})
            if self._verbose:
                print(color.GREEN + response + color.END)
                print(80*"-" + "\n")  

            # Send the recommendation to the educator
            return {configuration['user_settings']['username']: response}       
        
        
        # Case 3: Recommendation to the educator about 
        # (i) Learner's performance
        # (ii) Module's structure
        if configuration['retrieved_info_from_query']['username'] == ["ALL"]:
            prompt = educator_recommendation_about_learners_prompt.replace("{information}", configuration['information_text'])
            prompt = prompt.replace("{language}", configuration['language'])
        elif configuration['retrieved_info_from_query']['module_IDs']:
            prompt = educator_recommendation_about_course_prompt.replace("{information}", configuration['information_text'])
            prompt = prompt.replace("{language}", configuration['language'])
        else:
            return {configuration['user_settings']['username']: "[ERROR] No recommendations can be provided"}

        # Get recommendation
        response = self._send_information_chain.run({"prompt": prompt, "tesa_framework": tesa_framework})
        if self._verbose:
            print(color.GREEN + response + color.END)
            print(80*"-" + "\n")      

        return {configuration['user_settings']['username']: response}