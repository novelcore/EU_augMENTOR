import pickle
import dill
import numpy as np
import pandas as pd
import mysql.connector
from tqdm import tqdm
from utils.moodle_connection import moodle_connection, retrieve_data_from_MOODLE
from utils.neo4j_connection import Neo4jConnection
from utils.utils import transform_presentation

d = {
    "Demo": {
        "Quiz_Completed_Attempts": [-0.1, 15.8, 17.0, 19.6, float('inf')],
        "Quiz_grade": [-0.1, 59.87, 74.44, 80.0, float('inf')],
        "Forum_number_of_posts": [0.1, 2, 2.26, 2.7, float('inf')],
        "Forum_number_of_discussions": [-0.1, 1.7, 2.24, 2.7, float('inf')],
        "Scorm_number_of_submissions": [-0.1, 0.15, 0.35, 0.55, float('inf')],
    },
}

def encoding(value):
    """
    Encodes a numeric value into a categorical level based on predefined thresholds.

    Parameters:
        value (float): A numeric value in the range [0, 1].

    Returns:
        int: An encoded integer representing the categorical level:
            - 0 for 'Low'
            - 1 for 'Medium'
            - 2 for 'High'
            - 3 for 'Very high'

    Raises:
        ValueError: If the input value is not within the range [0, 1].
    """
    if value <= 0.25:
        return 0
    elif value <= 0.5:
        return 1
    elif value <= 0.75:
        return 2
    elif value <= 1.0:
        return 3
    elif np.isnan(value):
        return value
    else:
        return ValueError(f'Value: {value} is not in range [0,1]')
    
    
    
def retrieve_data_for_profile_assignment(course_id: int = None, pilot:str=None, graph: Neo4jConnection = None, cursor: mysql.connector.cursor.MySQLCursor = None, moodle_settings: dict = None):
    """
    Retrieve data related to profile assignment from both Moodle (for questions and user responses) and Neo4j (for grades).

    Args:
        course_id (int): The ID of the course for which to retrieve the data. Default is None.
        graph (Neo4jConnection): The Neo4j connection object used for querying the graph database.
        cursor (mysql.connector.cursor.MySQLCursor): MySQL cursor for executing SQL queries in Moodle.
        moodle_settings (dict): Moodle connection settings such as host, user, password, etc.

    Returns:
        tuple: 
            - d_questions (dict): Dictionary of questions with position, question text, and choices.
            - user_responses (dict): Dictionary of user responses where key is `userid` and value is a list of responses.
            - d_metrics (dict): Dictionary of user grades where key is `userid` and value is a dictionary of activities and their corresponding grades.

    Steps:
        1. Retrieve questions for the given `course_id` from the Moodle database.
        2. Process questions to keep only the latest records based on course_id and position.
        3. Pre-process questions and format choices using the `transform_presentation` function.
        4. Retrieve user responses for the questions and clean the data.
        5. Ensure all responses are non-categorical and start from 0 for later processing.
        6. Fetch grades for users from the Neo4j graph database based on course participation.
        7. Return the processed questions, user responses, and user grades.
    """
    # Retrieve user responses
    # -------------------------------------------------------------------------------------
    query = f"""SELECT cm.course AS course_id, 
        fi.feedback AS questionnaire,
        fi.id AS feedback_item_id, 
        fi.name AS feedback_item_name, 
        fc.userid, 
        u.email, 
        fv.value AS user_response
    FROM mdl_feedback_item fi
    JOIN mdl_feedback f ON fi.feedback = f.id
    JOIN mdl_course_modules cm ON cm.instance = f.id
    JOIN mdl_feedback_completed fc ON fc.feedback = f.id
    JOIN mdl_feedback_value fv ON fv.completed = fc.id AND fv.item = fi.id
    JOIN mdl_user u ON u.id = fc.userid
    WHERE cm.module = (SELECT id FROM mdl_modules WHERE name = 'feedback') and cm.course = {course_id}
    ORDER BY cm.course, fi.id, fc.userid
    """

    rows, cursor = retrieve_data_from_MOODLE(
        query=query, moodle_settings=moodle_settings, cursor=None
    )
    df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])

    # Exclude the self-assessment questionnaires (requested by UDE) 
    df_temp = df.groupby(['questionnaire', 'course_id']).nunique()
    selected_questionnaries = df_temp[df_temp['feedback_item_id'] > 1].reset_index()['questionnaire'].unique()
    df = df[df['questionnaire'].isin(selected_questionnaries)]
    print("[INFO] Number of questionnaires: ", df['questionnaire'].nunique())
    # Get Questionnaire ID
    questionnaire_id = df['questionnaire'].max()

    # Pre-process and retrieve responses
    # ------------------------------------------------------------------------------------
    df["user_response"] = pd.to_numeric(df['user_response'], errors='coerce').astype('float')
    
    # If the learner have NOT responded to the last questionnaire, retrieve their answers from the last completed questionnaire
    df_responses = df[df['questionnaire'] == questionnaire_id]
    for id in selected_questionnaries:
        if id == questionnaire_id: continue
        user_ids = list(df_responses['userid'].unique())
        df_responses = pd.concat([df_responses, df[(df['questionnaire'] == id) & (~df['userid'].isin(user_ids))]], ignore_index=True)
    # All non-categorical features must start from 0 for proper processing
    df_responses["user_response"] -= 1
    
    # Group user responses by user ID
    user_responses = (
        df_responses.groupby("userid")["user_response"].apply(list).to_dict()
    )
    
    
    # Retrieve questions
    # -------------------------------------------------------------------------------------
    query = f"""SELECT 
    cm.course AS course_id, 
    fi.*
    FROM mdl_feedback_item fi
    JOIN mdl_feedback f ON fi.feedback = f.id
    JOIN mdl_course_modules cm ON cm.instance = f.id
    WHERE cm.module = (SELECT id FROM mdl_modules WHERE name = 'feedback') AND cm.course = {course_id} AND fi.feedback = {questionnaire_id}
    ORDER BY cm.course;
    """

    # Retrieve user responses from the Moodle database
    rows, cursor = retrieve_data_from_MOODLE(
        query=query, moodle_settings=moodle_settings, cursor=cursor
    )
    df_questions = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])

    # Pre-processing of questions and formatting choices
    # -------------------------------------------------------------------------------------
    df_questions = df_questions[df_questions['id'].isin(df['feedback_item_id'].unique())] # Manual-Fix: Exclude questions, which have not been answered by any learner

    df_questions = df_questions.rename(
        columns={"name": "question", "presentation": "choices"}
    )
    df_questions["choices"] = df_questions["choices"].apply(transform_presentation)

    df_questions["position"] -= 1
    # Prepare question dictionary with position as key
    d_questions = (
        df_questions[["position", "question", "choices"]]
        .set_index("position")
        .to_dict(orient="index")
    )

    print("[INFO] Questionnaire and user responses are retrieved")
    print
    # Retrieve grades from Neo4j graph database
    # -------------------------------------------------------------------------------------
    responses = graph.query(f"""MATCH (l:LEARNER)-[]->(c:COURSE)
                            MATCH (c)-[]->(m:MODULE)-[]->(a:ACTIVITY)
                            MATCH (l)-[r:PARTICIPATE]->(a)
                            WHERE c.id = {course_id}
                            WITH l.user_id AS userId, AVG(r.Cognitive_grade) AS Cognitive_grade, AVG(r.Collaboration_grade) AS Collaboration_grade, AVG(r.Communication_grade) AS Communication_grade, AVG(r.Creativity_grade) AS Creativity_grade, AVG(r.Critical_thinking_grade) AS Critical_grade                        
                            RETURN userId, COLLECT({{Cognitive: Cognitive_grade, Collaboration: Collaboration_grade, Communication: Communication_grade, Creativity: Creativity_grade, Critical_thinking: Critical_grade}}) AS metrics""")


    # Organize grades by user ID and activity metric
    d_metrics = dict()
    for item in responses:
        d_metrics[item["userId"]] = {}

        for x in item["metrics"][0]:
            d_metrics[item["userId"]][x.replace("_", " ")] = np.nan if item["metrics"][0][x] is None else round(item["metrics"][0][x], 1) 

    
    
    
    # Engagement metrics
    # -------------------------------------------------------------------------------------
    
    # 1. Get data related to Scorm
    query = f"""match (c:COURSE)-[]->(m:MODULE)-[]->(res:RESOURCE)
            match (l:LEARNER)-[r:STUDY]->(res)
            where c.id = {course_id} and res.id contains "SCORM"
            return c.id, m.title, res.id, l.user_id, r.number_of_submissions
            order by m.title, res.id, l.user_id"""

    response = graph.query(query)

    data = [(record['c.id'], record['m.title'], record['res.id'], record['l.user_id'], record['r.number_of_submissions']) for record in response]
    df1 = pd.DataFrame(data, columns=['Course_ID', 'Module_title', 'Activity_ID', 'User_ID', 'Scorm_number_of_submissions'])
    df1 = df1[['User_ID', 'Scorm_number_of_submissions']].groupby('User_ID').mean()
    df1['Scorm_number_of_submissions'] = pd.cut(df1['Scorm_number_of_submissions'], bins=d[pilot]['Scorm_number_of_submissions'], labels=['Low', 'Medium', 'High', 'Very high'])

    # 2. Get data related to Quiz
    query = f"""match (c:COURSE)-[]->(m:MODULE)-[]->(a:ACTIVITY)
    match (l:LEARNER)-[r]->(a)
    where c.id = {course_id} and a.type="Quiz"
    return c.id, m.title, a.id, l.user_id, r.number_of_completed_attempts, r.Cognitive
    order by m.title, a.id, l.user_id"""

    response = graph.query(query)

    data = [(record['c.id'], record['m.title'], record['a.id'], record['l.user_id'], record['r.number_of_completed_attempts'], record['r.Cognitive']) for record in response]
    df2 = pd.DataFrame(data, columns=['Course_ID', 'Module_title', 'Activity_ID', 'User_ID', 'Quiz_Completed_Attempts', 'Quiz_grade'])
    df2 = df2[['User_ID', 'Quiz_Completed_Attempts', 'Quiz_grade']].groupby('User_ID').mean()
    df2['Quiz_Completed_Attempts'] = pd.cut(df2['Quiz_Completed_Attempts'], bins=d[pilot]['Quiz_Completed_Attempts'], labels=['Low', 'Medium', 'High', 'Very high'])
    df2['Quiz_grade'] = pd.cut(df2['Quiz_grade'], bins=d[pilot]['Quiz_grade'], labels=['Low', 'Medium', 'High', 'Very high'])


    # 3. Get data related to Forum
    query = f"""match (c:COURSE)-[]->(m:MODULE)-[]->(a:ACTIVITY)
        match (l:LEARNER)-[r]->(a)
        where c.id = {course_id} and a.type="Forum"
        return c.id, m.title, a.id, l.user_id, r.number_of_posts, r.number_of_discussions
        order by m.title, a.id, l.user_id"""

    response = graph.query(query)

    data = [(record['c.id'], record['m.title'], record['a.id'], record['l.user_id'], record['r.number_of_posts'], record['r.number_of_discussions']) for record in response]
    df3 = pd.DataFrame(data, columns=['Course_ID', 'Module_title', 'Activity_ID', 'User_ID', 'Forum_number_of_posts', 'Forum_number_of_discussions'])
    df3 = df3[['User_ID', 'Forum_number_of_posts', 'Forum_number_of_discussions']].groupby('User_ID').mean()

    df3['Forum_number_of_discussions'] = pd.cut(df3['Forum_number_of_discussions'], bins=d[pilot]['Forum_number_of_discussions'], labels=['Low', 'Medium', 'High', 'Very high'])
    df3['Forum_number_of_posts'] = pd.cut(df3['Forum_number_of_posts'], bins=d[pilot]['Forum_number_of_posts'], labels=['Low', 'Medium', 'High', 'Very high'])


    # 4. Calculate engagement metrics
    df = pd.concat([df1, df2, df3], axis=1)
    # > Missing values handling
    for feature in df.columns:
        if df[feature].isna().sum() / df.shape[0] < 0.4:
            df[feature].fillna('Very high', inplace=True)
    # > One-hot encoder (0) 'Low', (1) 'Medium', (2) 'High', (3) 'Very high'
    for value, code in zip(['Low', 'Medium', 'High', 'Very high'], [0.25, 0.5, 0.75, 1.0]):
        df.replace(value, code, inplace=True)
        

    # Merge engagement metrics with learners grades
    # -------------------------------------------------------------------------------------    
    d_engagement = df.to_dict(orient='index')
    for user_id in d_metrics:
        if user_id not in d_engagement:
            print(f'[WARNING] No engagement records for User ID: {user_id}')
            d_metrics[user_id]['Autonomy'], d_metrics[user_id]['Competence'], d_metrics[user_id]['Relatedness'] = np.NaN, np.NaN, np.NaN
        else:
            d_metrics[user_id]['Autonomy'] = np.nanmean([d_engagement[user_id]['Scorm_number_of_submissions'], d_engagement[user_id]['Quiz_Completed_Attempts'], d_engagement[user_id]['Forum_number_of_posts'], d_engagement[user_id]['Forum_number_of_discussions']])
            d_metrics[user_id]['Competence'] = np.nanmean([d_engagement[user_id]['Quiz_grade'], d_engagement[user_id]['Forum_number_of_discussions']])           
            for feature in ['Autonomy', 'Competence']:
                d_metrics[user_id][feature] = encoding(d_metrics[user_id][feature])            

            # Manual-Fix: For Pilot: EASD set 'Relatedness' = -1 for all users, since forum is not utilized
            if pilot != "EASD":
                d_metrics[user_id]['Relatedness'] = np.nanmean([d_engagement[user_id]['Forum_number_of_discussions'], d_engagement[user_id]['Forum_number_of_posts'], d_engagement[user_id]['Forum_number_of_discussions']])
                d_metrics[user_id]['Relatedness'] = encoding(d_metrics[user_id]['Relatedness'])  

            
    return d_questions, user_responses, d_metrics



def profile_assignment(graph, cursor=None, configuration: dict = None, verbose=False):
    """
    Assigns learners to predefined profiles based on questionnaire responses, academic metrics, and engagement data.

    This function integrates data from Moodle and a local knowledge graph to create a dataset that combines
    questionnaire responses with engagement metrics and grades. It then uses a pre-trained machine learning 
    model to assign learners to specific profiles (IASIS, EASD, or UPAT), and generates personalized explanations 
    for each assignment using a LIME explainer.

    Parameters:
    -----------
    graph : neo4j.Graph
        A connection to the Neo4j graph database for querying learner-course relationships.
        
    cursor : pymysql.cursors.Cursor, optional
        A MySQL database cursor for querying Moodle. If None, a new connection is established using
        `configuration["moodle_settings"]`.

    configuration : dict
        A dictionary containing the following required keys:
            - "course_id": int, Moodle course ID
            - "pilot": str, one of {"IASIS", "EASD", "UPAT"}
            - "metrics": list of str, academic metric names to include in the dataset
            - "path": str, path to directory containing pre-trained `model.pkl`, `imputer.pkl`, and `explainer.dill`
            - "profiles": list of str, names of the predefined profiles (indexed by model output)
            - "moodle_settings": dict, connection settings for Moodle DB

    verbose : bool, default=False
        If True, print detailed log messages throughout execution.

    Returns:
    --------
    d_profiles : dict
        A dictionary mapping learner user IDs to their assigned profile and a generated explanation.
        Format:
        {
            user_id_1: {
                "profile": "IASIS_A",
                "explanation": "Learner belongs to profile IASIS_A with probability 91.3% due to\n - 'X' = 'Y'\n ..."
            },
            ...
        }
    """    
    # 1. Connection with Moodle
    # ------------------------------------------------------------------------------
    if cursor is None:
        connection = moodle_connection(configuration["moodle_settings"])
        cursor = connection.cursor()

    # 2. Data retrieval (Questionnaire, grades, engagement metrics)
    # ------------------------------------------------------------------------------
    d_questions, user_responses, d_metrics = retrieve_data_for_profile_assignment(
        course_id=configuration["course_id"],
        pilot=configuration['pilot'],
        graph=graph,
        cursor=cursor,
        moodle_settings=configuration["moodle_settings"],
    )
    if verbose:
        print("[INFO] Data were retrieved")


    # 3. Create dataset
    # ------------------------------------------------------------------------------
    # Identify the learners which have not performed the questionnaire
    L_learners_with_no_questionnaire = [
        user_id for user_id in d_metrics if user_id not in user_responses
    ]
    # Remove them from further processing
    for user_id in L_learners_with_no_questionnaire:
        print(f"User ID: {user_id} has not attempted to complete the questionnaire")
        del d_metrics[user_id]

    records = list()
    for user_id in user_responses:
        # Sanity check
        if user_id not in d_metrics:
            continue
        # Sanity check (remove the learners which have partially answered the questionnaire)
        if len(user_responses[user_id]) != len(d_questions):
            print(f"User ID: {user_id} has not completed the questionnaire")
            continue
        # Get questionnaire responses
        record = user_responses[user_id].copy()
        # Include engagement metrics
        record.append(d_metrics[user_id]["Autonomy"])
        record.append(d_metrics[user_id]["Competence"])
        if configuration["pilot"] != "EASD":
            record.append(d_metrics[user_id]["Relatedness"])
            
        # Add all grades per metric
        for metric in configuration['metrics']:
            if metric not in d_metrics[user_id]:
                record.append(np.nan)
            else:
                record.append(d_metrics[user_id][metric])
        # Include instance
        records.append(record)


    # Feature names
    features = [items["question"] for _, items in d_questions.items()] + [f"{metric}" for metric in configuration["metrics"]]
                                    
    # Records (questionnaire + grades)
    records = np.asarray(records)
    # Deal with missing values
    with open(f"{configuration['path']}/imputer.pkl", "rb") as handle:
        imputer = pickle.load(handle)
    records = imputer.transform(records)
    del imputer
    
    if verbose:
        print("[INFO] Dataset is created")

    # 4. Assign learners to pilot's (IASIS, EASD or UPAT) profiles
    # ------------------------------------------------------------------------------

    # Load model for assigning a learner to the pre-defined profiles
    with open(f"{configuration['path']}/model.pkl", "rb") as handle:
        model = pickle.load(handle)
    # Get predictions/assignments
    clusters = model.predict(records)
    
    if verbose:
        print("[INFO] Learner were assigned to the pre-defined profiles")
        
        
    # Load LIME-explainer
    with open(f"{configuration['path']}/explainer.dill", "rb") as file:
        explainer = dill.load(file)
    if verbose:
        print('[INFO] Explanator is loaded')
    
    d_profiles = dict()
    for cluster, record, user_id in zip(clusters, records, tqdm(d_metrics)):
        exp = explainer.explain_instance(
            data_row=record, num_features=len(features), predict_fn=model.predict_proba
        )

        # if configuration["pilot"] in ["UPAT", "IASIS"]:
        #     explanation = f"Ο μαθητής ανατέθηκε στο augMENTOR προφιλ: {configuration['profiles'][cluster]} με πιθανότητα: {np.round(100 * np.max(model.predict_proba(record.reshape(1, -1))), 2)} επειδή\n"
        # elif configuration["pilot"] == "EASD":
        #     explanation = f"Učenik pripada augMENTOR profilu: {configuration['profiles'][cluster]} sa verovatnoćom: {np.round(100 * np.max(model.predict_proba(record.reshape(1, -1))), 2)} zbog\n" 
        # else:
        #     explanation = f"Learner belongs to profile: {configuration['profiles'][cluster]} with probability: {np.round(100 * np.max(model.predict_proba(record.reshape(1, -1))), 2)} due to\n"
        
        explanation = ""
        for item, score in exp.as_list():
            if score < 0.0:
                continue

            if "<" in item or ">" in item:
                explanation += f"- {item}\n".strip()
            else:
                question, answer = item.split("=")
                explanation += f"""- '{question}' = '{answer}'""".strip() + '\n'

            if explanation.count("\n") == 5:
                break
        
        d_profiles[user_id] = {'profile': configuration['profiles'][cluster],
                               'probability': np.round(100 * np.max(model.predict_proba(record.reshape(1, -1))), 2),
                               'explanation': explanation}

    if verbose:
        print('[INFO] Explanations about the learners\' assignment to profiles were provided')
        
    # Sanity check: Identify the learners, which were not included to an augMENTOR profile
    result = graph.query(f"""match (l:LEARNER)-[]->(c:COURSE) where c.id = {configuration['course_id']} return l.user_id as user_id, l.username as username """)

    for item in result:
        if item['user_id'] not in d_profiles:
            print(f"[WARNING] Learner {item['username']} (Moodle user id:{item['user_id']}) is not assigned to an augMENTOR profile")

    return d_profiles