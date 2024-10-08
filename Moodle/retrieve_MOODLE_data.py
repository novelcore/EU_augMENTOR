# %%
import pandas as pd
from tqdm import tqdm
from utils.html2text import html2text
from utils.moodle_connection import moodle_connection, retrieve_data_from_MOODLE
from utils.neo4j_connection import neo4j_connection

# Neo4j credentials
neo4j_settings = {
    "connection_url": "...",
    "username": "...",
    "password": "...",
}

# MOODLE credentials
moodle_settings = {
    "host": "...",
    "user": "...",
    "password": "...",
    "port": "...",
    "database": "...",
}

# Selected course id
course_ids = (4,5,6)

# Connection with Neo4j and SQL server
graph = neo4j_connection(neo4j_settings=neo4j_settings, clean_graph=True)
connection = moodle_connection(moodle_settings)
cursor = connection.cursor()

# %%
# ### Courses

query = f"""SELECT 
    c.id AS course_id,
    c.shortname AS course_shortname,
    c.fullname AS course_fullname,   
    u.id AS user_id,
    u.username AS username,
    u.institution AS institution,
    u.country AS country
FROM 
    mdl_course c
LEFT JOIN 
    mdl_logstore_standard_log l ON l.courseid = c.id AND l.action = 'created' AND l.target = 'course'
LEFT JOIN 
    mdl_user u ON l.userid = u.id
GROUP BY 
    c.id, u.id;"""
        
# Fetch records
rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
# Convert records to DataFrame
df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])


# Get course Ids
if course_ids is not None:
    df = df[df['course_id'].isin(course_ids)]
else:
    course_ids = tuple(df['course_id'].unique())

for idx in df.index:
    course_id = df.loc[idx]["course_id"]
    course_name = df.loc[idx]["course_shortname"]
    course_description = df.loc[idx]["course_fullname"].replace('"',"'")
    user_id = df.loc[idx]["user_id"]
    username = df.loc[idx]["username"]
    institution = df.loc[idx]["institution"]
    country = df.loc[idx]["country"]

    if username is not None:
        query = f"""MERGE (c:COURSE {{id:{course_id}, title:"{course_name}", description:"{course_description}"}})
                    MERGE (t:TEACHER {{user_id:{user_id}, username:"{username}", institution:"{institution}", country:"{country}"}})
                    MERGE (t)-[:CREATED]->(c)"""
        graph.query(query)
    else:
        query = f"""MERGE (c:COURSE {{id:{course_id}, title:"{course_name}", description:"{course_description}"}})"""
        graph.query(query)
        
print("[INFO] Teacher were assigned to their created courses")

# %%
# ### Learners


query = f"""SELECT 
    u.id AS id,
    u.username AS username,
    u.institution AS institution,
    u.country AS country,
    u.confirmed AS confirmed,
    r.shortname AS role,
    cse.id AS course_id
FROM 
    mdl_user u
JOIN 
    mdl_role_assignments ra ON u.id = ra.userid
JOIN 
    mdl_context c ON ra.contextid = c.id
JOIN 
    mdl_role r ON ra.roleid = r.id
JOIN 
    mdl_course cse ON c.instanceid = cse.id AND c.contextlevel = 50
"""

# Fetch records
rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
# Convert records to DataFrame
df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])



# Sanity check
df = df[df["confirmed"] == 1]
# Processing
df_roles = (
    df.groupby(["id", "username"]).agg(lambda x: list(set(x))).reset_index()[["id", "username", "role"]]
)
df_roles["role"] = df_roles["role"].apply(
    lambda x: "student" if x == ["student"] else "teacher"
)
# Correlate "id, username" with "role"
df_roles = pd.merge(
    df_roles,
    df[["id", "username","institution", "country"]].drop_duplicates(),
    on=["id", "username"],
    how="left",
)
# Correlate "id, username, course_id" with "role"
df = pd.merge(
    df[["id", "username","course_id"]].drop_duplicates(),
    df_roles[["id", "username", "role"]],
    on=["id", "username"],
    how="left",
)

# Include data to Neo4j
for idx in df_roles.index:
    user_id = df_roles.iloc[idx]["id"]
    username = df_roles.iloc[idx]["username"]
    institution = df_roles.iloc[idx]["institution"] 
    country = df_roles.iloc[idx]["country"]

    if df_roles.iloc[idx]["role"] == "student":
        graph.query(
            f"""MERGE (l:LEARNER {{user_id:{user_id}, username:"{username}", institution:"{institution}", country:"{country}"}})"""
        )
    else:
        graph.query(
            f"""MERGE (t:TEACHER {{user_id:{user_id}, username:"{username}", institution:"{institution}", country:"{country}"}})"""
        )
print("[INFO] Learners and Teachers imported")



# Include data to Neo4j
for idx in df.index:
    username = df.loc[idx]["username"]
    course_id = df.loc[idx]["course_id"]
    role = "LEARNER" if df.loc[idx]["role"] == "student" else "TEACHER"
    
    query = f"""MATCH (c:COURSE)
            MATCH (u:{role})
            WHERE c.id = {course_id} AND u.username = "{username}"
            MERGE (u)-[:REGISTERED]->(c)"""
                            
    r = graph.query(query)
    
print("[INFO] Learners and Teachers were registed to the corresponding courses")


# %%
# ### Courses and Modules


# In Moodle, activities and resources are distinct types of elements used to structure courses and provide learning content.
# Here's a breakdown of both activities and resources:


# "Activities in Moodle": Activities typically involve interactive elements where students engage directly with course content or participate in collaborative exercises.
# Here are some common activities found in Moodle:
#
# - Assign: Allows students to submit work online, which instructors can then grade and provide feedback on.
# - Quiz: Provides online quizzes with various question types, automated grading, and immediate feedback to students.
# - Forum: Facilitates asynchronous discussions among course participants, promoting interaction and knowledge sharing.
#
# - Chat: Offers real-time synchronous communication among course participants.
# - Choice: Allows instructors to create polls or surveys for students to respond to.
# - Glossary: Enables participants to create and maintain a list of definitions, like a collaborative dictionary.
# - Database: Allows participants to create, maintain, and search a bank of record entries.
# - Workshop: Facilitates peer assessment where students can submit work and review submissions of their peers.
# - Lesson: Provides a way of structuring content and questions to guide students through learning materials.
# - SCORM Package: Allows integration of external learning content packaged in SCORM format.


# "Resources in Moodle": Resources in Moodle typically refer to static content or files that provide information and support learning.
# They are used to deliver content to students rather than interactive engagement. Here are common types of resources in Moodle:
#
# - URL: Link to an external website or resource.
# - File: Upload and display a file (e.g., PDF, Word document, PowerPoint presentation).
# - Label: Add text or multimedia content directly onto a course page.
# - SCORM Package: Import and deliver external learning content packaged in SCORM format.
# - Page: Create a standalone web page within the course.
#
# - Folder: Organize and display a collection of files.
# - IMS Content Package: Import content from IMS-compliant packages.
# - Book: Organize content into chapters and subchapters, making it easier for learners to navigate.


# Conclusion:
# Understanding the distinction between activities and resources is crucial for organizing and structuring content
# within Moodle courses effectively. Activities promote engagement and interaction, while resources deliver content
# and information to support learning objectives. By utilizing these elements appropriately, instructors can create
# engaging and effective online learning experiences for their students.


for course_id in course_ids:
    query = f"""SELECT 
        id AS section_id,
        course AS course_id,
        section AS section_name,
        sequence
    FROM 
        mdl_course_sections
    WHERE 
        course = {course_id}
    ORDER BY 
        sequence;
    """


    # Fetch records
    rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
    # Convert records to DataFrame    
    df = pd.DataFrame(
        rows, columns=["section_id", "course_id", "section_name", "sequence"]
    )
    # Processing
    df = df.drop('sequence', axis=1).drop_duplicates()
    df['section_name'] += 1

    for idx in df.index:
        section_id = df.loc[idx]["section_id"]
        section_name = f"MODULE:{df.loc[idx]['section_name']}"
        course_id = df.loc[idx]["course_id"]

        query = f"""MATCH (c:COURSE)
                    WHERE c.id = {course_id}
                    MERGE (m:MODULE {{id:{section_id}, title:"{section_name}"}})
                    MERGE (c)-[:HAS_MODULE]->(m)"""

        graph.query(query)

print("[INFO] Modules of each course were created")  

# %%
# ### Activities

# %%
# For each module include its activities


for course_id in course_ids:
    query = f"""SELECT 
        cs.id AS section_id,
        cs.course AS course_id,
        cs.section AS section_name,
        cs.sequence,
        'Forum' AS activity_type,
        f.id AS activity_id
    FROM 
        mdl_course_sections cs
    LEFT JOIN 
        mdl_course_modules cm ON cm.section = cs.id
    LEFT JOIN 
        mdl_forum f ON f.course = cs.course AND cm.instance = f.id AND cm.module = (SELECT id FROM mdl_modules WHERE name = 'forum')
    WHERE 
        cs.course = {course_id}

    UNION ALL

    SELECT 
        cs.id AS section_id,
        cs.course AS course_id,
        cs.section AS section_name,
        cs.sequence,
        'Quiz' AS activity_type,
        q.id AS activity_id
    FROM 
        mdl_course_sections cs
    LEFT JOIN 
        mdl_course_modules cm ON cm.section = cs.id
    LEFT JOIN 
        mdl_quiz q ON q.course = cs.course AND cm.instance = q.id AND cm.module = (SELECT id FROM mdl_modules WHERE name = 'quiz')
    WHERE 
        cs.course = {course_id}

    UNION ALL

    SELECT 
        cs.id AS section_id,
        cs.course AS course_id,
        cs.section AS section_name,
        cs.sequence,
        'Assign' AS activity_type,
        a.id AS activity_id
    FROM 
        mdl_course_sections cs
    LEFT JOIN 
        mdl_course_modules cm ON cm.section = cs.id
    LEFT JOIN 
        mdl_assign a ON a.course = cs.course AND cm.instance = a.id AND cm.module = (SELECT id FROM mdl_modules WHERE name = 'assign')
    WHERE 
        cs.course = {course_id}
        
    UNION ALL

    SELECT 
        cs.id AS section_id,
        cs.course AS course_id,
        cs.section AS section_name,
        cs.sequence,
        'Scorm' AS activity_type,
        s.id AS activity_id
    FROM 
        mdl_course_sections cs
    LEFT JOIN 
        mdl_course_modules cm ON cm.section = cs.id
    LEFT JOIN 
        mdl_scorm s ON s.course = cs.course AND cm.instance = s.id AND cm.module = (SELECT id FROM mdl_modules WHERE name = 'scorm')
    WHERE 
        cs.course = {course_id}

    ORDER BY 
        section_id, activity_type, activity_id;
    """

    # Fetch records
    rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
    # Convert records to DataFrame
    df = pd.DataFrame(
        rows,
        columns=[
            "section_id",
            "course_id",
            "section_name",
            "sequence",
            "activity_type",
            "activity_id",
        ],
    )
    # Processing
    df.dropna(inplace=True, ignore_index=True)

    for idx in df.index:
        section_id = df.loc[idx]["section_id"]
        activity_type = df.loc[idx]["activity_type"]
        activity_id = int(df.loc[idx]["activity_id"])
        id = f"{activity_type}:{activity_id}"

        query = f"""MATCH (m:MODULE)
                    WHERE m.id = {section_id}
                    MERGE (a:ACTIVITY {{id:"{id}", type:"{activity_type}"}})
                    MERGE (m)-[:HAS_ACTIVITY]->(a)"""

        graph.query(query)

print("[INFO] Activities of each Module were created")

# %%
# #### Activity: FORUM
# - update its properties


query = f"""SELECT 
    f.id AS forum_id,
    f.course AS course_id,
    f.type AS forum_type,
    f.name AS forum_name,
    f.intro AS forum_intro
FROM 
    mdl_forum f
WHERE
    f.course in {course_ids};"""

# Fetch records
rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
# Convert records to DataFrame
df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])

# Processing
df["forum_intro"] = df["forum_intro"].apply(html2text)

for idx in df.index:
    forum_id = df.loc[idx]["forum_id"]
    forum_type = df.loc[idx]["forum_type"].replace('"', "'")
    forum_name = df.loc[idx]["forum_name"].replace('"', "'")
    forum_intro = df.loc[idx]["forum_intro"].replace('"', "'")

    query = f"""MATCH (a:ACTIVITY)
                WHERE a.id = "Forum:{forum_id}"
                SET a.forum_type = "{forum_type}", a.title = "{forum_name}", a.description = "{forum_intro}", a.metric = "Basic skills", a.rubric = "{{}}"
            """
    graph.query(query)

print("[INFO] FORUM properties were updated")


# # In 2nd round maybe information about forum discussion should be included (such as title, user who created, )

# query = """SELECT
#     f.id AS forum_id,
#     f.name AS forum_name,
#     COUNT(d.id) AS number_of_discussions
# FROM
#     mdl_forum f
# LEFT JOIN
#     mdl_forum_discussions d ON f.id = d.forum
# GROUP BY
#     f.id, f.name
# ORDER BY
#     f.id;
# """


# cursor.execute(query)
# rows = cursor.fetchall()

# # Create a pandas DataFrame
# df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])
# df


# query = f"""SELECT 
#     p.userid AS user_id,
#     f.id AS forum_id,
#     f.course AS course_id,
#     COUNT(p.id) AS number_of_posts,
#     fg.grade AS user_grade,
#     (MAX(l.timecreated) - MIN(l.timecreated)) AS time_to_complete
# FROM 
#     mdl_forum_posts p
# JOIN 
#     mdl_forum_discussions d ON p.discussion = d.id
# JOIN 
#     mdl_forum f ON d.forum = f.id
# LEFT JOIN 
#     mdl_forum_grades fg ON f.id = fg.forum AND p.userid = fg.userid
# JOIN 
#     mdl_logstore_standard_log l ON l.objectid = p.id AND l.userid = p.userid
# WHERE
#     f.course IN {course_ids}
#     AND l.component = 'mod_forum'
#     AND l.action IN ('created', 'viewed') -- actions indicating activity in the forum
# GROUP BY 
#     p.userid, f.id, fg.grade;
# """

query = f"""SELECT 
    p.userid AS user_id,
    f.id AS forum_id,
    f.course AS course_id,
    GROUP_CONCAT(DISTINCT l.action ORDER BY l.action ASC) AS actions, -- List of distinct actions            
    SUM(CASE WHEN l.action = 'submitted' THEN 1 ELSE 0 END) AS number_of_submissions,
    COUNT(p.id) AS number_of_posts,
    fg.grade AS user_grade,
    (MAX(l.timecreated) - MIN(l.timecreated)) AS time_to_complete,
    COUNT(l.id) AS number_of_clicks,
    MIN(p.created) AS first_post_timestamp,
    MAX(p.created) AS last_post_timestamp,
    COUNT(DISTINCT d.id) AS number_of_discussions,
    (MAX(p.created) - MIN(p.created)) / NULLIF(COUNT(p.id) - 1, 0) AS avg_time_between_posts,
    COUNT(DISTINCT DATE(FROM_UNIXTIME(p.created))) AS active_days
FROM 
    mdl_forum_posts p
JOIN 
    mdl_forum_discussions d ON p.discussion = d.id
JOIN 
    mdl_forum f ON d.forum = f.id
LEFT JOIN 
    mdl_forum_grades fg ON f.id = fg.forum AND p.userid = fg.userid
JOIN 
    mdl_logstore_standard_log l ON l.objectid = p.id AND l.userid = p.userid AND l.component = 'mod_forum'
WHERE
    f.course IN {course_ids}
GROUP BY 
    p.userid, f.id, fg.grade;"""
    
# Fetch records
rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
# Convert records to DataFrame
df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])

# Processing
df["user_grade"] = df["user_grade"].apply(lambda x: 0 if x is None else x) # TODO: Some records are empty

for idx in df.index:
    user_id = df.loc[idx]["user_id"]
    forum_id = df.loc[idx]["forum_id"]
    number_of_submissions = df.loc[idx]["number_of_submissions"]
    number_of_posts = df.loc[idx]["number_of_posts"]
    user_grade = df.loc[idx]["user_grade"]
    number_of_clicks = df.loc[idx]["number_of_clicks"]
    number_of_discussions = df.loc[idx]["number_of_discussions"]
    time = df.loc[idx]['time_to_complete']
    
    query = f"""MATCH (l:LEARNER) 
            WHERE l.user_id={user_id}
            MATCH (a:ACTIVITY) 
            WHERE a.id="Forum:{forum_id}"
            MERGE (l)-[:PARTICIPATE {{number_of_posts:{number_of_posts}, grade:round({user_grade},1), number_of_submissions:{number_of_submissions}, number_of_clicks:{number_of_clicks}, number_of_discussions:{number_of_discussions}, time:{time}}}]->(a)"""
    graph.query(query)

print("[INFO] Learners were assigned to FORUMs")

# %%
# #### Activity: QUIZ
# - update its properties


query = f"""SELECT 
    q.id AS quiz_id,
    q.course AS course_id,
    q.name AS quiz_name,
    q.intro AS quiz_intro,
    q.grade as quiz_max_grade
FROM 
    mdl_quiz q
WHERE
    q.course in {course_ids};"""

# Fetch records
rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
# Convert records to DataFrame
df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])

# Processing
df["quiz_intro"] = df["quiz_intro"].apply(html2text)

for idx in df.index:
    quiz_id = df.loc[idx]["quiz_id"]
    quiz_name = df.loc[idx]["quiz_name"].replace('"', "'")
    quiz_intro = df.loc[idx]["quiz_intro"].replace('"', "'")
    quiz_max_grade = int(df.loc[idx]["quiz_max_grade"])

    query = f"""MATCH (a:ACTIVITY)
                WHERE a.id = "Quiz:{quiz_id}"
                SET a.title = "{quiz_name}", a.description = "{quiz_intro}", a.quiz_max_grade = {quiz_max_grade}, a.metric = "Quiz", a.rubric = "{{}}"
            """

    graph.query(query)

print("[INFO] QUIZ properties were updated")


# query = f"""SELECT 
#     qa.userid AS user_id,
#     q.id AS quiz_id,
#     q.course AS course_id,
#     COUNT(qa.id) AS number_of_attempts,
#     SUM(qa.timefinish - qa.timestart) AS total_time,
#     qg.grade AS user_grade
# FROM 
#     mdl_quiz q
# JOIN 
#     mdl_quiz_attempts qa ON q.id = qa.quiz
# JOIN 
#     mdl_quiz_grades qg ON q.id = qg.quiz AND qa.userid = qg.userid
# WHERE
#     q.course in {course_ids}
# GROUP BY 
#     qa.userid, q.id, qg.grade;"""

query = f"""SELECT 
    qa.userid AS user_id,
    q.id AS quiz_id,
    q.course AS course_id,
    GROUP_CONCAT(DISTINCT l.action ORDER BY l.action ASC) AS actions, -- List of distinct actions            
    SUM(CASE WHEN l.action = 'submitted' THEN 1 ELSE 0 END) AS number_of_submissions,    
    COUNT(qa.id) AS number_of_attempts,
    SUM(qa.timefinish - qa.timestart) AS total_time,
    qg.grade AS user_grade,
    COUNT(l.id) AS number_of_clicks, -- Number of clicks    
    MIN(qa.timestart) AS first_attempt_timestamp,
    MAX(qa.timefinish) AS last_attempt_timestamp,
    AVG(qa.timefinish - qa.timestart) AS avg_time_per_attempt,
    COUNT(CASE WHEN qa.state = 'finished' THEN 1 END) AS number_of_completed_attempts
FROM 
    mdl_quiz q
JOIN 
    mdl_quiz_attempts qa ON q.id = qa.quiz
JOIN 
    mdl_quiz_grades qg ON q.id = qg.quiz AND qa.userid = qg.userid
LEFT JOIN 
    mdl_logstore_standard_log l ON l.objectid = qa.id AND l.userid = qa.userid AND l.component = 'mod_quiz'
WHERE
    q.course IN {course_ids}
GROUP BY 
    qa.userid, q.id, qg.grade;
"""

# Fetch records
rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
# Convert records to DataFrame
df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])

# Processing
df["total_time"] = df["total_time"].apply(lambda x: None if x < 0 else x)

for idx in df.index:
    user_id = df.loc[idx]["user_id"]
    quiz_id = df.loc[idx]["quiz_id"]
    number_of_attempts = df.loc[idx]["number_of_attempts"]
    number_of_submissions = df.loc[idx]["number_of_submissions"]
    total_time = df.loc[idx]["total_time"]
    user_grade = df.loc[idx]["user_grade"]
    number_of_clicks = df.loc[idx]["number_of_clicks"]
    number_of_completed_attempts = df.loc[idx]["number_of_completed_attempts"]

    if total_time is None:
        query = f"""MATCH (l:LEARNER) 
                    WHERE l.user_id={user_id}
                    MATCH (a:ACTIVITY) 
                    WHERE a.id="Quiz:{quiz_id}"
                    MERGE (l)-[:PARTICIPATE {{attempts:{number_of_attempts}, number_of_submissions:{number_of_submissions}, number_of_clicks:{number_of_clicks}, number_of_completed_attempts:{number_of_completed_attempts}, grade:round(100*{user_grade}/a.quiz_max_grade,1)}}]->(a)"""
    else:
        query = f"""MATCH (l:LEARNER) 
                    WHERE l.user_id={user_id}
                    MATCH (a:ACTIVITY) 
                    WHERE a.id="Quiz:{quiz_id}"
                    MERGE (l)-[:PARTICIPATE {{attempts:{number_of_attempts}, number_of_submissions:{number_of_submissions}, number_of_clicks:{number_of_clicks}, number_of_completed_attempts:{number_of_completed_attempts}, time:{total_time}, grade:round(100*{user_grade}/a.quiz_max_grade,1)}}]->(a)"""
    graph.query(query)

print("[INFO] Learners were assigned to QUIZs")

# %%
# #### Activity: ASSIGN
# - update its properties


query = f"""SELECT 
    a.id AS assign_id,
    a.course AS course_id,
    a.name AS assign_name,
    a.intro AS assign_intro,
    a.grade as assign_max_grade
FROM 
    mdl_assign a
WHERE
    a.course in {course_ids}"""

# Fetch records
rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
# Convert records to DataFrame
df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])

# Processing
df["assign_intro"] = df["assign_intro"].apply(html2text)
df["assign_max_grade"] = df["assign_max_grade"].apply(
    lambda x: 1 if x is None else max(x, 1)
)  # TODO: Why negative grades?

# TODO: check quiz_sumgrades and quiz_grade
for idx in df.index:
    assign_id = df.loc[idx]["assign_id"]
    assign_name = df.loc[idx]["assign_name"].replace('"', "'")
    assign_intro = df.loc[idx]["assign_intro"].replace('"', "'")
    assign_max_grade = df.loc[idx]["assign_max_grade"]

    query = f"""MATCH (a:ACTIVITY)
                WHERE a.id = "Assign:{assign_id}"
                SET a.title = "{assign_name}", a.description = "{assign_intro}", a.assign_max_grade = {assign_max_grade}, a.metric = "Basic skills", a.rubric = "{{}}"
            """

    graph.query(query)

print("[INFO] ASSIGN properties were updated")


# query = f"""SELECT 
#     s.userid AS user_id,
#     a.id AS assign_id,
#     a.course AS course_id,
#     CASE WHEN s.id IS NOT NULL THEN 1 ELSE 0 END AS submitted,
#     SUM(s.timemodified - s.timecreated) AS total_time,
#     g.grade AS user_grade
# FROM 
#     mdl_assign_submission s
# JOIN 
#     mdl_assign a ON s.assignment = a.id
# LEFT JOIN 
#     mdl_assign_grades g ON a.id = g.assignment AND s.userid = g.userid
# WHERE
#     a.course in {course_ids}
# GROUP BY 
#     s.userid, a.id, submitted, g.grade;"""



query = f"""SELECT 
    s.userid AS user_id,
    a.id AS assign_id,
    a.course AS course_id,
    GROUP_CONCAT(DISTINCT l.action ORDER BY l.action ASC) AS actions, -- List of distinct actions            
    SUM(CASE WHEN l.action = 'submitted' THEN 1 ELSE 0 END) AS number_of_submissions,    
    CASE WHEN s.id IS NOT NULL THEN 1 ELSE 0 END AS submitted,
    SUM(s.timemodified - s.timecreated) AS total_time,
    g.grade AS user_grade,
    COUNT(l.id) AS number_of_clicks,
    MIN(s.timecreated) AS first_attempt_timestamp,
    MAX(s.timemodified) AS last_attempt_timestamp
FROM 
    mdl_assign_submission s
JOIN 
    mdl_assign a ON s.assignment = a.id
LEFT JOIN 
    mdl_assign_grades g ON a.id = g.assignment AND s.userid = g.userid
LEFT JOIN 
    mdl_logstore_standard_log l ON l.objectid = s.id AND l.userid = s.userid AND l.component = 'mod_assign'
WHERE
    a.course IN {course_ids} AND l.action IN ('submitted', 'viewed', 'updated', 'graded', 'feedback')
GROUP BY 
    s.userid, a.id, submitted, g.grade;
"""

    
# Fetch records
rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
# Convert records to DataFrame
df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])

# Processing
df["total_time"] = df["total_time"].apply(lambda x: None if x < 0 else x)
df["user_grade"] = df["user_grade"].apply(
    lambda x: 0 if x is None else 0 if x < 0 else x
)  # TODO: Why negative grades?

for idx in df.index:
    user_id = df.loc[idx]["user_id"]
    assign_id = df.loc[idx]["assign_id"]
    submitted = df.loc[idx]["submitted"]
    total_time = df.loc[idx]["total_time"]
    user_grade = df.loc[idx]["user_grade"]

    if total_time is None:
        query = f"""MATCH (l:LEARNER) 
                    WHERE l.user_id={user_id}
                    MATCH (a:ACTIVITY) 
                    WHERE a.id="Assign:{assign_id}"
                    MERGE (l)-[:PARTICIPATE {{submitted:{submitted}, number_of_submissions: {number_of_submissions}, number_of_clicks: {number_of_clicks}, grade:round(100.0*{user_grade}/a.assign_max_grade,1)}}]->(a)"""
    else:
        query = f"""MATCH (l:LEARNER) 
                    WHERE l.user_id={user_id}
                    MATCH (a:ACTIVITY) 
                    WHERE a.id="Assign:{assign_id}"
                    MERGE (l)-[:PARTICIPATE {{submitted:{submitted}, time:{total_time}, number_of_submissions: {number_of_submissions}, number_of_clicks: {number_of_clicks}, grade:round(100.0*{user_grade}/a.assign_max_grade,1)}}]->(a)"""
    r = graph.query(query)

print("[INFO] Learners were assigned to ASSIGNs")

# %%
# #### Activity: SCORM
# - update its properties


query = f"""SELECT 
    s.id AS scorm_id,
    s.course AS course_id,
    s.name AS scorm_name,
    s.intro AS scorm_intro
FROM 
    mdl_scorm s
WHERE
    s.course in {course_ids};"""

# Fetch records
rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
# Convert records to DataFrame
df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])

# Processing
df["scorm_intro"] = df["scorm_intro"].apply(html2text)

for idx in df.index:
    scorm_id = df.loc[idx]["scorm_id"]
    scorm_name = df.loc[idx]["scorm_name"].replace('"', "'")
    scorm_intro = df.loc[idx]["scorm_intro"].replace('"', "'")

    query = f"""MATCH (a:ACTIVITY)
                WHERE a.id = "Scorm:{scorm_id}"
                SET a.title = "{scorm_name}", a.description = "{scorm_intro}", a.metric = "Basic skills", a.rubric = "{{}}"
            """

    graph.query(query)

print("[INFO] SCORM properties were updated")


# query = f"""SELECT 
#     sg.userid AS user_id,
#     s.id AS scorm_id,
#     s.course AS course_id,
#     MAX(CASE WHEN sg.element = 'cmi.core.score.raw' THEN sg.value ELSE NULL END) AS user_grade,
#     COUNT(DISTINCT sg.attempt) AS num_attempts,
#     MAX(CASE WHEN sg.element = 'cmi.core.total_time' THEN sg.value ELSE NULL END) AS total_time
# FROM 
#     mdl_scorm s
# LEFT JOIN 
#     mdl_scorm_scoes_track sg ON s.id = sg.scormid
# WHERE 
#     sg.element IN ('cmi.core.score.raw', 'cmi.core.total_time') AND s.course IN {course_ids}
# GROUP BY 
#     sg.userid, s.id
# ORDER BY 
#     sg.userid, s.id;
# """

query = f"""SELECT 
    sg.userid AS user_id,
    s.id AS scorm_id,
    s.course AS course_id,
    MAX(CASE WHEN sg.element = 'cmi.core.score.raw' THEN sg.value ELSE NULL END) AS user_grade,
    GROUP_CONCAT(DISTINCT l.action ORDER BY l.action ASC) AS actions, -- List of distinct actions  
    SUM(CASE WHEN l.action = 'submitted' THEN 1 ELSE 0 END) AS number_of_submissions,              
    COUNT(DISTINCT sg.attempt) AS num_attempts,
    COUNT(l.id) AS number_of_clicks,
    MIN(sg.timemodified) AS first_attempt_timestamp,
    MAX(sg.timemodified) AS last_attempt_timestamp
FROM 
    mdl_scorm s
LEFT JOIN 
    mdl_scorm_scoes_track sg ON s.id = sg.scormid
LEFT JOIN 
    mdl_logstore_standard_log l ON l.objectid = sg.id AND l.component = 'mod_scorm' AND l.action = 'attempt'
WHERE 
    sg.element IN ('cmi.core.score.raw', 'cmi.core.total_time') 
    AND s.course IN {course_ids}
GROUP BY 
    sg.userid, s.id
ORDER BY 
    sg.userid, s.id;
"""

# Fetch records
rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
# Convert records to DataFrame
df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])

# Processing
df["user_grade"] = df["user_grade"].apply(lambda x: 0 if x is None else x)
df["total_time"] = df['last_attempt_timestamp'] - df['first_attempt_timestamp']

for idx in df.index:
    user_id = df.loc[idx]["user_id"]
    scorm_id = df.loc[idx]["scorm_id"]
    user_grade = df.loc[idx]["user_grade"]
    attempts = df.loc[idx]["num_attempts"]
    number_of_submissions = df.loc[idx]["number_of_submissions"]
    number_of_clicks = df.loc[idx]["number_of_clicks"]
    time = df.loc[idx]["total_time"]

    query = f"""MATCH (l:LEARNER) 
                WHERE l.user_id={user_id}
                MATCH (a:ACTIVITY) 
                WHERE a.id="Scorm:{scorm_id}"
                MERGE (l)-[:PARTICIPATE {{grade:round({user_grade},1), number_of_submissions: {number_of_submissions}, number_of_clicks: {number_of_clicks}, attempts:{attempts}, time:{time}}}]->(a)"""
    graph.query(query)

print("[INFO] Learners were assigned to SCORMs")

# %%
# ### Resources

# %%
# #### URL


query = f"""SELECT 
    'Forum' AS activity_type,
    f.id AS activity_id,
    u.id AS url_id,
    f.course AS course_id,
    u.name AS url_name,
    u.externalurl AS url_external_url
FROM 
    mdl_forum f
JOIN 
    mdl_course c ON f.course = c.id
JOIN 
    mdl_url u ON u.course = c.id
WHERE 
    f.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'forum'))
    AND u.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'url'))
    AND f.course in {course_ids}
    
UNION ALL

SELECT 
    'Quiz' AS activity_type,
    q.id AS activity_id,
    u.id AS url_id,
    q.course AS course_id,
    u.name AS url_name,
    u.externalurl AS url_external_url
FROM 
    mdl_quiz q
JOIN 
    mdl_course c ON q.course = c.id
JOIN 
    mdl_url u ON u.course = c.id
WHERE 
    q.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'quiz'))
    AND u.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'url'))
    AND q.course in {course_ids}

UNION ALL

SELECT 
    'Assign' AS activity_type,
    a.id AS activity_id,
    u.id AS url_id,
    a.course AS course_id,
    u.name AS url_name,
    u.externalurl AS url_external_url
FROM 
    mdl_assign a
JOIN 
    mdl_course c ON a.course = c.id
JOIN 
    mdl_url u ON u.course = c.id
WHERE 
    a.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'assign'))
    AND u.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'url'))
    AND a.course in {course_ids}
    
UNION ALL

SELECT 
    'Scorm' AS activity_type,
    s.id AS activity_id,
    u.id AS url_id,
    s.course AS course_id,
    u.name AS url_name,
    u.externalurl AS url_external_url
FROM 
    mdl_scorm s
JOIN 
    mdl_course c ON s.course = c.id
JOIN 
    mdl_url u ON u.course = c.id
WHERE 
    s.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'scorm'))
    AND u.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'url'))
    AND s.course in {course_ids}
    
ORDER BY 
    activity_type, activity_id, url_id;
"""

# Fetch records
rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
# Convert records to DataFrame
df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])


for idx in df.index:
    activity_id = f"{df.loc[idx]['activity_type']}:{df.loc[idx]['activity_id']}"
    url_description = f"Title: {df.loc[idx]['url_name']}\nURL: {df.loc[idx]['url_external_url']}".replace('"',"'")
    url_id = f"URL:{df.loc[idx]['url_id']}"

    query = f"""MATCH (a:ACTIVITY)
    WHERE a.id = "{activity_id}"
    MERGE (r:RESOURCE {{id:"{url_id}", description:"{url_description}"}})
    MERGE (a)-[:HAS_RESOURCE]-(r)
    """
    graph.query(query)

print("[INFO] Resource:URL were imported")


query = f"""SELECT DISTINCT
    u.id AS user_id,
    url.id as url_id,
    url.course AS course_id
FROM
    mdl_logstore_standard_log l
JOIN
    mdl_user u ON l.userid = u.id
JOIN
    mdl_url url ON l.objectid = url.id
WHERE
    l.action = 'viewed'
    AND l.objecttable = 'url'
    AND url.course IN {course_ids};"""

# Fetch records
rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
# Convert records to DataFrame
df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])


for idx in df.index:
    user_id = df.loc[idx]["user_id"]
    url_id = f"URL:{df.loc[idx]['url_id']}"

    query = f"""MATCH (l:LEARNER)
    WHERE l.user_id = {user_id}
    MATCH (r:RESOURCE)
    WHERE r.id = "{url_id}"
    MERGE (l)-[:STUDY]-(r)
    """
    graph.query(query)

print("[INFO] Learners which studied the Resource:URL were mapped")

# %%
# #### Page


query = f"""SELECT 
    'Forum' AS activity_type,
    f.id AS activity_id,
    p.id AS page_id,
    f.course AS course_id,    
    p.name as page_name,
    p.intro as page_intro
FROM 
    mdl_forum f
JOIN 
    mdl_course c ON f.course = c.id
JOIN 
    mdl_page p ON p.course = c.id
WHERE 
    f.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'forum'))
    AND p.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'page'))
    AND f.course in {course_ids}

UNION ALL

SELECT 
    'Quiz' AS activity_type,
    q.id AS activity_id,
    p.id AS page_id,
    q.course AS course_id,
    p.name as page_name,
    p.intro as page_intro
FROM 
    mdl_quiz q
JOIN 
    mdl_course c ON q.course = c.id
JOIN 
    mdl_page p ON p.course = c.id
WHERE 
    q.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'quiz'))
    AND p.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'page'))
    AND q.course in {course_ids}

UNION ALL

SELECT 
    'Assign' AS activity_type,
    a.id AS activity_id,
    p.id AS page_id,
    p.course AS course_id,
    p.name as page_name,
    p.intro as page_intro
FROM 
    mdl_assign a
JOIN 
    mdl_course c ON a.course = c.id
JOIN 
    mdl_page p ON p.course = c.id
WHERE 
    a.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'assign'))
    AND p.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'page'))
    AND a.course in {course_ids}
    
UNION ALL

SELECT 
    'Scorm' AS activity_type,
    s.id AS activity_id,
    p.id AS page_id,
    s.course AS course_id,
    p.name as page_name,
    p.intro as page_intro
FROM 
    mdl_scorm s
JOIN 
    mdl_course c ON s.course = c.id
JOIN 
    mdl_page p ON p.course = c.id
WHERE 
    s.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'scorm'))
    AND p.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'page'))
    AND s.course in {course_ids}    
        
ORDER BY 
    activity_type, activity_id, page_id;
"""

# Fetch records
rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
# Convert records to DataFrame
df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])

# Processing
df["page_intro"] = df["page_intro"].apply(html2text)

for idx in df.index:
    activity_id = f"{df.loc[idx]['activity_type']}:{df.loc[idx]['activity_id']}"
    page_description = f"Title: {df.loc[idx]['page_name']}\nDescription: {df.loc[idx]['page_intro']}".replace('"',"'")
    page_id = f"Page:{df.loc[idx]['page_id']}"

    query = f"""MATCH (a:ACTIVITY)
    WHERE a.id = "{activity_id}"
    MERGE (r:RESOURCE {{id:"{page_id}", description:"{page_description}"}})
    MERGE (a)-[:HAS_RESOURCE]-(r)
    """
    graph.query(query)

print("[INFO] Resource:PAGE were imported")


query = f"""SELECT DISTINCT
    u.id AS user_id,
    p.id AS page_id,
    p.course AS course_id
FROM
    mdl_logstore_standard_log l
JOIN
    mdl_user u ON l.userid = u.id
JOIN
    mdl_page p ON l.objectid = p.id
WHERE
    l.action = 'viewed'
    AND l.objecttable = 'page'
    AND p.course in {course_ids}
    """

# Fetch records
rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
# Convert records to DataFrame
df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])


for idx in df.index:
    user_id = df.loc[idx]["user_id"]
    page_id = f"Page:{df.loc[idx]['page_id']}"

    query = f"""MATCH (l:LEARNER)
    WHERE l.user_id = {user_id}
    MATCH (r:RESOURCE)
    WHERE r.id = "{page_id}"
    MERGE (l)-[:STUDY]-(r)
    """
    graph.query(query)

print("[INFO] Learners which studied the Resources:PAGE were mapped")

# %%
# #### Folder


query = f"""SELECT 
    'Forum' AS activity_type,
    f.id AS activity_id,
    p.id AS folder_id,
    f.course AS course_id,    
    p.name as folder_name,
    p.intro as folder_intro
FROM 
    mdl_forum f
JOIN 
    mdl_course c ON f.course = c.id
JOIN 
    mdl_folder p ON p.course = c.id
WHERE 
    f.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'forum'))
    AND p.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'folder'))
    AND f.course in {course_ids}

UNION ALL

SELECT 
    'Quiz' AS activity_type,
    q.id AS activity_id,
    p.id AS folder_id,
    q.course AS course_id,    
    p.name as folder_name,
    p.intro as folder_intro
FROM 
    mdl_quiz q
JOIN 
    mdl_course c ON q.course = c.id
JOIN 
    mdl_folder p ON p.course = c.id
WHERE 
    q.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'quiz'))
    AND p.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'folder'))
    AND q.course in {course_ids}

UNION ALL

SELECT 
    'Assign' AS activity_type,
    a.id AS activity_id,
    p.id AS folder_id,
    a.course AS course_id,    
    p.name as folder_name,
    p.intro as folder_intro
FROM 
    mdl_assign a
JOIN 
    mdl_course c ON a.course = c.id
JOIN 
    mdl_folder p ON p.course = c.id
WHERE 
    a.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'assign'))
    AND p.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'folder'))
    AND a.course in {course_ids}
    
UNION ALL

SELECT 
    'Scorm' AS activity_type,
    s.id AS activity_id,
    p.id AS folder_id,
    s.course AS course_id,    
    p.name as folder_name,
    p.intro as folder_intro
FROM 
    mdl_scorm s
JOIN 
    mdl_course c ON s.course = c.id
JOIN 
    mdl_folder p ON p.course = c.id
WHERE 
    s.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'scorm'))
    AND p.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'folder'))
    AND s.course in {course_ids}
    
ORDER BY 
    activity_type, activity_id, folder_id;
"""

# Fetch records
rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
# Convert records to DataFrame
df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])

# Processing
df["folder_intro"] = df["folder_intro"].apply(html2text)

for idx in df.index:
    activity_id = f"{df.loc[idx]['activity_type']}:{df.loc[idx]['activity_id']}"
    folder_description = f"Title: {df.loc[idx]['folder_name']}\nDescription: {df.loc[idx]['folder_intro']}".replace('"',"'")
    folder_id = f"Folder:{df.loc[idx]['folder_id']}"

    query = f"""MATCH (a:ACTIVITY)
    WHERE a.id = "{activity_id}"
    MERGE (r:RESOURCE {{id:"{folder_id}", description:"{folder_description}"}})
    MERGE (a)-[:HAS_RESOURCE]-(r)
    """
    graph.query(query)

print("[INFO] Resource:FOLDER were imported")


query = f"""SELECT DISTINCT
    u.id AS user_id,
    u.username AS username,
    f.id AS folder_id,
    f.course AS course_id    
FROM
    mdl_logstore_standard_log l
JOIN
    mdl_user u ON l.userid = u.id
JOIN
    mdl_folder f ON l.objectid = f.id
WHERE
    l.action = 'viewed'
    AND l.objecttable = 'folder'
    AND f.course in {course_ids};
"""


# query = """SELECT
#     l.userid AS user_id,
#     l.objectid AS page_id,
#     MIN(l.timecreated) AS start_time,
#     MAX(l.timecreated) AS end_time
# FROM
#     mdl_logstore_standard_log l
# JOIN
#     mdl_user u ON l.userid = u.id
# WHERE
#     l.objecttable = 'folder'
#     AND l.action = 'viewed'
# GROUP BY
#     l.userid, l.objectid
# ORDER BY
#     l.userid, l.objectid;
# """

# Fetch records
rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
# Convert records to DataFrame
df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])


for idx in df.index:
    user_id = df.loc[idx]["user_id"]
    folder_id = f"Folder:{df.loc[idx]['folder_id']}"

    query = f"""MATCH (l:LEARNER)
    WHERE l.user_id = {user_id}
    MATCH (r:RESOURCE)
    WHERE r.id = "{folder_id}"
    MERGE (l)-[:STUDY]-(r)
    """
    graph.query(query)

print("[INFO] Learners which studied the Resources:FOLDER were mapped")

# %%
# #### Glossary


query = f"""SELECT 
    'Forum' AS activity_type,
    f.id AS activity_id,
    p.id AS glossary_id,
    f.course AS course_id,        
    p.name as glossary_name,
    p.intro as glossary_intro
FROM 
    mdl_forum f
JOIN 
    mdl_course c ON f.course = c.id
JOIN 
    mdl_glossary p ON p.course = c.id
WHERE 
    f.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'forum'))
    AND p.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'glossary'))
    AND f.course in {course_ids}

UNION ALL

SELECT 
    'Quiz' AS activity_type,
    q.id AS activity_id,
    p.id AS glossary_id,
    q.course AS course_id,    
    p.name as glossary_name,
    p.intro as glossary_intro
FROM 
    mdl_quiz q
JOIN 
    mdl_course c ON q.course = c.id
JOIN 
    mdl_glossary p ON p.course = c.id
WHERE 
    q.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'quiz'))
    AND p.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'glossary'))
    AND q.course in {course_ids}

UNION ALL

SELECT 
    'Assign' AS activity_type,
    a.id AS activity_id,
    p.id AS glossary_id,
    a.course AS course_id,
    p.name as glossary_name,
    p.intro as glossary_intro
FROM 
    mdl_assign a
JOIN 
    mdl_course c ON a.course = c.id
JOIN 
    mdl_glossary p ON p.course = c.id
WHERE 
    a.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'assign'))
    AND p.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'glossary'))
    AND a.course in {course_ids}

UNION ALL

SELECT 
    'Scorm' AS activity_type,
    s.id AS activity_id,
    p.id AS glossary_id,
    s.course AS course_id,
    p.name as glossary_name,
    p.intro as glossary_intro
FROM 
    mdl_scorm s
JOIN 
    mdl_course c ON s.course = c.id
JOIN 
    mdl_glossary p ON p.course = c.id
WHERE 
    s.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'scorm'))
    AND p.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'glossary'))
    AND s.course in {course_ids}
    
ORDER BY 
    activity_type, activity_id, glossary_id;
"""

# Fetch records
rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
# Convert records to DataFrame
df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])

# Processing
df["glossary_intro"] = df["glossary_intro"].apply(html2text)

for idx in df.index:
    activity_id = f"{df.loc[idx]['activity_type']}:{df.loc[idx]['activity_id']}"
    glossary_description = f"Title: {df.loc[idx]['glossary_name']}\nDescription: {df.loc[idx]['glossary_intro']}".replace('"',"'")
    glossary_id = f"Glossary:{df.loc[idx]['glossary_id']}"

    query = f"""MATCH (a:ACTIVITY)
    WHERE a.id = "{activity_id}"
    MERGE (r:RESOURCE {{id:"{glossary_id}", description:"{glossary_description}"}})
    MERGE (a)-[:HAS_RESOURCE]-(r)
    """
    graph.query(query)

print("[INFO] Resource:GLOSSARY were imported")


query = f"""SELECT DISTINCT
    u.id AS user_id,
    u.username AS username,
    g.course AS course_id,    
    g.id AS glossary_id
FROM
    mdl_logstore_standard_log l
JOIN
    mdl_user u ON l.userid = u.id
JOIN
    mdl_glossary g ON l.objectid = g.id
WHERE
    l.action = 'viewed'
    AND l.objecttable = 'glossary'
    AND g.course in {course_ids};
"""

# Fetch records
rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
# Convert records to DataFrame
df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])


for idx in df.index:
    user_id = df.loc[idx]["user_id"]
    glossary_id = f"Glossary:{df.loc[idx]['glossary_id']}"

    query = f"""MATCH (l:LEARNER)
    WHERE l.user_id = {user_id}
    MATCH (r:RESOURCE)
    WHERE r.id = "{glossary_id}"
    MERGE (l)-[:STUDY]-(r)
    """
    graph.query(query)
print("[INFO] Learners which studied the Resources:GLOSSARY were mapped")

# %%
# #### H5P


query = f"""SELECT 
    'Forum' AS activity_type,
    f.id AS activity_id,
    p.id AS h5p_id,
    f.course AS course_id,
    p.name as h5p_name,
    p.intro as h5p_intro
FROM 
    mdl_forum f
JOIN 
    mdl_course c ON f.course = c.id
JOIN 
    mdl_h5pactivity p ON p.course = c.id
WHERE 
    f.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'forum'))
    AND p.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'h5pactivity'))
    AND f.course in {course_ids}

UNION ALL

SELECT 
    'Quiz' AS activity_type,
    q.id AS activity_id,
    p.id AS h5p_id,
    q.course AS course_id,
    p.name as h5p_name,
    p.intro as h5p_intro
FROM 
    mdl_quiz q
JOIN 
    mdl_course c ON q.course = c.id
JOIN 
    mdl_h5pactivity p ON p.course = c.id
WHERE 
    q.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'quiz'))
    AND p.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'h5pactivity'))
    AND q.course in {course_ids}

UNION ALL

SELECT 
    'Assign' AS activity_type,
    a.id AS activity_id,
    p.id AS h5p_id,
    a.course AS course_id,
    p.name as h5p_name,
    p.intro as h5p_intro
FROM 
    mdl_assign a
JOIN 
    mdl_course c ON a.course = c.id
JOIN 
    mdl_h5pactivity p ON p.course = c.id
WHERE 
    a.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'assign'))
    AND p.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'h5pactivity'))
    AND a.course in {course_ids}
    
UNION ALL

SELECT 
    'Scorm' AS activity_type,
    s.id AS activity_id,
    p.id AS h5p_id,
    s.course AS course_id,
    p.name as h5p_name,
    p.intro as h5p_intro
FROM 
    mdl_scorm s
JOIN 
    mdl_course c ON s.course = c.id
JOIN 
    mdl_h5pactivity p ON p.course = c.id
WHERE 
    s.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'scorm'))
    AND p.id IN (SELECT DISTINCT instance FROM mdl_course_modules WHERE module = (SELECT id FROM mdl_modules WHERE name = 'h5pactivity'))
    AND s.course in {course_ids}
    
ORDER BY 
    activity_type, activity_id, h5p_id;
"""

# Fetch records
rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
# Convert records to DataFrame
df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])

# Processing
df["h5p_intro"] = df["h5p_intro"].apply(html2text)

for idx in df.index:
    activity_id = f"{df.loc[idx]['activity_type']}:{df.loc[idx]['activity_id']}"
    h5p_intro = df.loc[idx]["h5p_intro"].replace('"',"'") if len(df.loc[idx]["h5p_intro"]) > 0 else "-"
    h5p_description = f"Title: {df.loc[idx]['h5p_name']}\nDescription: {h5p_intro}".replace('"',"'")
    h5p_id = f"H5P:{df.loc[idx]['h5p_id']}"

    query = f"""MATCH (a:ACTIVITY)
    WHERE a.id = "{activity_id}"
    MERGE (r:RESOURCE {{id:"{h5p_id}", description:"{h5p_description}"}})
    MERGE (a)-[:HAS_RESOURCE]-(r)
    """
    graph.query(query)

print("[INFO] Resource:H5P were imported")


query = f"""SELECT DISTINCT
    u.id AS user_id,
    u.username AS username,
    h5p.course as course_id,
    h5p.id AS h5p_id
FROM
    mdl_logstore_standard_log l
JOIN
    mdl_user u ON l.userid = u.id
JOIN
    mdl_h5pactivity h5p ON l.objectid = h5p.id
WHERE
    l.action = 'viewed'
    AND l.objecttable = 'h5pactivity'
    AND h5p.course IN {course_ids};
"""

# Fetch records
rows, cursor = retrieve_data_from_MOODLE(query=query, moodle_settings=moodle_settings, cursor=cursor)
# Convert records to DataFrame
df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])


for idx in df.index:
    user_id = df.loc[idx]["user_id"]
    h5p_id = f"H5P:{df.loc[idx]['h5p_id']}"

    query = f"""MATCH (l:LEARNER)
    WHERE l.user_id = {user_id}
    MATCH (r:RESOURCE)
    WHERE r.id = "{h5p_id}"
    MERGE (l)-[:STUDY]-(r)
    """
    graph.query(query)

print("[INFO] Learners which studied the Resources:H5P were mapped")


if connection.is_connected():
    cursor.close()
    connection.close()
    print("[INFO] MySQL connection is closed")


