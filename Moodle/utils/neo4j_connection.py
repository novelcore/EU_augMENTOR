from neo4j import GraphDatabase

class Neo4jConnection:

    def __init__(self, uri, user, pwd)->None:
        '''
            Connection with Neo4j

            Parameters
            ----------
            uri: (str) 
                URL
            user: (str)
                username 
            pwd: (str)
                password
        '''
        self.__uri = uri
        self.__user = user
        self.__pwd = pwd
        self.__driver = None

        self.node_properties_query = """
            CALL apoc.meta.data()
            YIELD label, other, elementType, type, property
            WHERE NOT type = "RELATIONSHIP" AND elementType = "node"
            WITH label AS nodeLabels, collect({property:property, type:type}) AS properties
            RETURN {labels: nodeLabels, properties: properties} AS output
            """

        self.rel_properties_query = """
            CALL apoc.meta.data()
            YIELD label, other, elementType, type, property
            WHERE NOT type = "RELATIONSHIP" AND elementType = "relationship"
            WITH label AS nodeLabels, collect({property:property, type:type}) AS properties
            RETURN {type: nodeLabels, properties: properties} AS output
            """

        self.rel_query = """
            CALL apoc.meta.data()
            YIELD label, other, elementType, type, property
            WHERE type = "RELATIONSHIP" AND elementType = "node"
            UNWIND other AS other_node
            RETURN {start: label, type: property, end: toString(other_node)} AS output
            """

        try:
            self.__driver = GraphDatabase.driver(self.__uri, auth=(self.__user, self.__pwd))
            print('[INFO] Connection established')
        except Exception as e:
            print("Failed to create the driver:", e)

    def close(self)->None:
        '''
            Close connection with Neo4j
        '''
        if self.__driver is not None:
            self.__driver.close()

    def query(self, query=None, parameters=None, db=None)->str:
        '''
            Conduct a query to the database

            Parameters
            ----------
            query: (str)
                user query
            parameters: (str)
                parameters

            Returns
            -------
            Response from the query (str)
        '''
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None
        try: 
            session = self.__driver.session(database=db) if db is not None else self.__driver.session() 
            response = list(session.run(query, parameters))
        except Exception as e:
            print(f'[ERROR] Query failed: {e}"')
            print(f'Query: {query}')
            print(f"Query failed: {e}")
            print(f'Query: {query}')
        finally: 
            if session is not None:
                session.close()
        return response

    def clean_base(self)->None:
        '''
            Remove all nodes/relationships from the database
        '''
        self.query("MATCH (n) DETACH DELETE n")
        print('All items of DB were deleted')


    def get_schema(self)->str:
        """
        Refreshes the Neo4j graph schema information

        Returns
        -------
        DB schema (str)
        """
        node_properties = [el["output"] for el in self.query(self.node_properties_query)]
        rel_properties = [el["output"] for el in self.query(self.rel_properties_query)]
        relationships = [el["output"] for el in self.query(self.rel_query)]

        # self.structured_schema = {
        #     "node_props": {el["labels"]: el["properties"] for el in node_properties},
        #     "rel_props": {el["type"]: el["properties"] for el in rel_properties},
        #     "relationships": relationships,
        # }

        self.schema = f"""
        Node properties are the following:
        {node_properties}
        Relationship properties are the following:
        {rel_properties}
        The relationships are the following:
        {[f"(:{el['start']})-[:{el['type']}]->(:{el['end']})" for el in relationships]}
        """

        return self.schema
    
    
    
def neo4j_connection(neo4j_settings: dict = None, clean_graph: bool = True):
    """
    Establishes a connection to a Neo4j database and optionally cleans the graph.

    Parameters:
    neo4j_settings (dict): A dictionary containing the connection settings for Neo4j.
                           Expected keys: "connection_url", "username", "password".
    clean_graph (bool): A flag indicating whether to clean the graph after establishing the connection.

    Returns:
    Neo4jConnection: An instance of the Neo4jConnection class.

    Raises:
    Exception: If there is an error while connecting to Neo4j.
    """
    try:
        graph = Neo4jConnection(
            uri=neo4j_settings["connection_url"],
            user=neo4j_settings["username"],
            pwd=neo4j_settings["password"],
        )
        print("[INFO] Connected to Neo4j established")
        
        if clean_graph: 
            graph.clean_base()
        
        return graph
    except Exception as e:
        print("[ERROR] Connection with Neo4j was not established")
        print("> ", e)
        raise e