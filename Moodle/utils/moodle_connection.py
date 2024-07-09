from mysql.connector import Error
import mysql.connector

    
def moodle_connection(moodle_settings: dict = None):
    """
    Establishes a connection to a Moodle database.

    Parameters:
    moodle_settings (dict): A dictionary containing the connection settings for Moodle.
                            Expected keys: "host", "user", "password", "port", "database".

    Returns:
    mysql.connector.connection.MySQLConnection: An instance of the MySQLConnection class.

    Raises:
    Error: If there is an error while connecting to the Moodle database.
    """
    try:
        connection = mysql.connector.connect(
            host=moodle_settings["host"],
            user=moodle_settings["user"],
            password=moodle_settings["password"],
            port=moodle_settings["port"],
            database=moodle_settings["database"],
        )

        if connection.is_connected():
            db_Info = connection.get_server_info()
            print(f"[INFO] Connected to MySQL Server (version: {db_Info})")
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            record = cursor.fetchone()
            print("[INFO] You're connected to database: ", record[0])

            # Fetch and print the list of all tables in the selected database
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            print("[INFO] Number of tables in the database: ", len(tables))

            return connection
        else:
            raise "[ERROR] Connection with MOODLE was not established"
    except Error as e:
        print("[ERROR] Connection with MOODLE was not established")
        print(e)
        raise e
    
def retrieve_data_from_MOODLE(query: str = None, cursor: mysql.connector.cursor.MySQLCursor = None, moodle_settings: dict=None, number_of_attempts: int = 5):
    """
    Retrieves data from the Moodle database by executing the provided SQL query.

    Parameters:
    query (str): The SQL query to execute.
    cursor (mysql.connector.cursor.MySQLCursor): The cursor object to use for executing the query.
    moodle_settings (dict): MOODLE connection settings
    number_of_attempts (int): The number of attempts to retry the query in case of failure.

    Returns:
    list: A list of tuples representing the rows fetched from the database.

    Raises:
    Exception: If the data cannot be retrieved after the specified number of attempts.
    """
    for _ in range(number_of_attempts):
        try:
            # Fetch all records from the mdl_user table
            cursor.execute(query)
            return cursor.fetchall(), cursor
        except Exception as e:
            print("[WARNING] Data from MOODLE were not retrieved")
            print(e)
            print("[INFO] Reconnecting to MOODLE")
            connection = moodle_connection(moodle_settings)
            cursor = connection.cursor()   
            
    raise "[ERROR] Data were not retrieved"