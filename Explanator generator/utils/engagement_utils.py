import pandas as pd
from utils.moodle_connection import retrieve_data_from_MOODLE

valid_interactions = ['QUIZ', 'ASSIGN', 'FORUM', 'SCORM', 'BOOK', 'WORKSHOP', 'URL', 'PAGE', 'FOLDER', 'GLOSSARY', 'H5P']

def retrieve_learner_interactions(username, start_time, end_time, course_id, excluded_activies:list=[], graph=None, moodle_settings=None, cursor=None):
    """
    Retrieves studied resources and activities for a learner within a specific time period.

    Parameters:
        username (str): Username of the learner.
        start_time (str): Start of the time range (format: 'YYYY-MM-DD HH:MM:SS').
        end_time (str): End of the time range (format: 'YYYY-MM-DD HH:MM:SS').
        course_id (int): int of course IDs to filter activities.
        excluded_activies (list): list of excluded activities' IDs
        graph: Neo4j graph object (e.g., from py2neo or similar).
        moodle_settings: Configuration/settings for connecting to the Moodle database.
        cursor: Database cursor for executing SQL queries.

    Returns:
        List[str]: Unique activity/resource IDs in the format COMPONENT:objectid (e.g., 'ASSIGN:52').
    """

    # SQL query to fetch learner actions
    query = f"""
        SELECT 
            l.userid AS user_id,
            u.username AS username,
            l.component,
            l.objectid,
            CASE 
                WHEN l.component = 'mod_quiz' THEN qa.quiz
                WHEN l.component = 'mod_forum' THEN l.objectid
                WHEN l.component = 'mod_assign' THEN ma.id
                WHEN l.component = 'mod_scorm' THEN ms.id
                WHEN l.component = 'mod_book' THEN mb.id
                WHEN l.component = 'mod_workshop' THEN mw.id
                WHEN l.component = 'mod_url' THEN mu.id
                WHEN l.component = 'mod_folder' THEN mf.id
                WHEN l.component = 'mod_page' THEN mp.id
                WHEN l.component = 'mod_glossary' THEN mg.id
                WHEN l.component = 'mod_h5pactivity' THEN mh.id
                ELSE NULL
            END AS component_id
        FROM 
            mdl_logstore_standard_log l
        LEFT JOIN 
            mdl_user u ON u.id = l.userid
        LEFT JOIN
            mdl_quiz_attempts qa ON l.objectid = qa.id AND l.component = 'mod_quiz'
--        LEFT JOIN
--            mdl_forum md ON l.objectid = md.id AND l.component = 'mod_forum' and l.courseid = md.course
        LEFT JOIN
            mdl_assign ma ON l.objectid = ma.id AND l.component = 'mod_assign' and l.courseid = ma.course
        LEFT JOIN
            mdl_scorm ms ON l.objecttable = 'scorm' AND l.objectid = ms.id AND l.component = 'mod_scorm'
        LEFT JOIN
            mdl_book mb ON l.objecttable = 'book' AND l.objectid = mb.id AND l.component = 'mod_book'
        LEFT JOIN    
            mdl_workshop mw ON l.objecttable = 'workshop' AND l.objectid = mw.id AND l.component = 'mod_workshop'
        LEFT JOIN
            mdl_url mu ON l.objecttable = 'url' AND l.objectid = mu.id AND l.component = 'mod_url'
        LEFT JOIN
            mdl_folder mf ON l.objecttable = 'folder' AND l.objectid = mf.id AND l.component = 'mod_folder'
        LEFT JOIN
            mdl_page mp ON l.objecttable = 'page' AND l.objectid = mp.id AND l.component = 'mod_page'
        LEFT JOIN
            mdl_glossary mg ON l.objecttable = 'glossary' AND l.objectid = mg.id AND l.component = 'mod_glossary'
        LEFT JOIN
            mdl_h5pactivity mh ON l.objecttable = 'h5pactivity' AND l.objectid = mh.id AND l.component = 'mod_h5pactivity'
        WHERE 
            u.username = '{username}'
            AND l.timecreated BETWEEN UNIX_TIMESTAMP('{start_time}') 
            AND UNIX_TIMESTAMP('{end_time}')
            AND l.courseid = {course_id}
        ORDER BY 
            l.timecreated;
        """

    # Fetch records from Moodle
    rows, cursor = retrieve_data_from_MOODLE(
        query=query, moodle_settings=moodle_settings, cursor=cursor
    )

    # Convert to DataFrame
    df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description]).dropna()

    if df.shape[0] == 0: 
        return []
    df['component_id'] = df['component_id'].astype(int)
    # Construct activity IDs like "QUIZ:45"
    df['component'] = df['component'].apply(lambda x: 'H5P' if 'h5p' in x else x.split("_")[-1].upper())
    df = df[df['component'].isin(valid_interactions)]
    df['id'] = df.apply(lambda x: x['component'] + ":" + str(x['component_id']), axis=1)
    
    # Hot Fix: There is a problem with FORUMs (many of them have been deleted but)
    activities = graph.query(f"""match (c:COURSE)-[]->(m:MODULE)-[]->(a:ACTIVITY) where c.id = {course_id} return collect(DISTINCT a.id) as Activities""")[0]['Activities']
    resources = graph.query(f"""match (c:COURSE)-[]->(m:MODULE)-[]->(r:RESOURCE) where c.id = {course_id} return collect(DISTINCT r.id) as Resources""")[0]['Resources']
    return [item for item in list(df.drop_duplicates()['id'].values) if item in activities+resources and item not in excluded_activies]