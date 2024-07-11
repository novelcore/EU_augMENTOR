# EU_augMENTOR

This repository contains the implementation of EU project: augMENTOR

**Abstract:** AUGMENTOR aims to develop a novel pedagogical framework that promotes both basic skills and 21st century competencies by
integrating emerging technologies. This framework will be supported by an open access AI-boosted toolkit that builds on the strengths
of big data and learning analytics to provide different types of stakeholders with explainable recommendations for smart search and
identification of educational resources, as well as for designing personalized learning profiles that take into account individual actors’
characteristics, needs, and preferences. The overall approach foreseen is innovative, based on appropriately structured data that capture
the stakeholders' learning paths, promote informed and well-justified interaction, and advance critical thinking. AUGMENTOR will
leverage advancements in the fields of Pedagogical Design, Creative Pedagogy, Explainable Artificial Intelligence, and Knowledge
Representation and Reasoning for instructional purposes. We will meaningfully integrate pedagogical approaches with AI-based software
solutions to enable a rich collaboration among all chain’s actors from students to teachers and policy makers. Our goal is to provide
guidelines to stakeholders on how to address potential underlying educational difficulties and disabilities, shape individual learning
paths, or identify cases of gifted and talented students, to enable them to reach their full potential. AUGMENTOR will enhance trust and
transparency, and trigger constructive reflection in both tutoring and pedagogical policy making. The project keeps a strategic balance
between the pedagogical and technological dimensions of teaching and learning. At the same time, it contributes equally to the concepts of
individual and organizational learning, considering them as interdependent processes. The foreseen solution will be thoroughly deployed
and validated in a series of real pilots representing diverse educational and training settings to define best practices.

<br/>

## Table of contents

- [Summary](#summary)
- [How to run](#how-to-run)
    - [Use case: TryHackMe (THM)](#use-case-tryhackme-thm)
    - [Use case: MOODLE](#use-case-moodle)

## Summary

Keywords:
- ICT based learning
- Innovation in learning, teaching and assessment practices supported by digital technologies

Project name: Augmented Intelligence for Pedagogically Sustained Training and Education

Project acronym: augMENTOR

Call: HORIZON-CL2-2021-TRANSFORMATIONS-01

Topic: HORIZON-CL2-2021-TRANSFORMATIONS-01-05

Type of action: HORIZON Research and Innovation Actions

Granting authority: European Research Executive Agency

Grant managed through EU Funding & Tenders Portal: Yes (eGrants)

Project starting date: fixed date: 1 January 2023

Project end date: 31 December 2025

Project duration: 36 months

<br/>

## How to run

**Step 1.** Create a virtual environment 
```
    python -m  venv .venv
```

**Step 2.** Activate the virtual environment 
```
    source .venv/bin/activate
```

**Step 3.** Install requirements 
```
    pip install -r requirements.txt
    pip install -U langchain-openai
```

### Use case: TryHackMe (THM)

**Step 4a.** In files ``01.retrieve_THM_data.py`` and ``02.enrich_graph.py`` include TryHackMe API key and Neo4j credentials
```
headers = {"THM-API-KEY": "..."}

neo4j_settings = {
    "connection_url": "...",
    "username": "...",
    "password": "...",
}
```

**Step 4b.** Run
```
    python 01.retrieve_THM_data.py
    python 02.enrich_graph.py
```

### Use case: MOODLE

**Step 4a.** In file ``retrieve_MOODLE_data.py`` include Neo4j credentials and Moodle settings
```
neo4j_settings = {
    "connection_url": "...",
    "username": "...",
    "password": "...",
}

moodle_settings = {
    "host": "...",
    "user": "...",
    "password": "...",
    "port": ...,
    "database": "...",
}
```

**Step 4b.** Run
```
    python retrieve_MOODLE_data.py
```

<br/>

## Ontology description

### Moodle

This is the ontology used for developing the KG 

<p align="center">
<img src=".\images\Moodle.png" width = "1000" alt="" align=center />
</p>


#### Nodes and Their Properties

- TEACHER

    - username (STRING): The username of the teacher.
    - country (STRING): The country where the teacher is located.
    - institution (STRING): The institution the teacher is affiliated with.
    - user_id (INTEGER): A unique identifier for the teacher.

- LEARNER

    - username (STRING): The username of the learner.
    - country (STRING): The country where the learner is located.
    - institution (STRING): The institution the learner is affiliated with.
    - user_id (INTEGER): A unique identifier for the learner.

- COURSE

    - description (STRING): A description of the course.
    - title (STRING): The title of the course.
    - id (INTEGER): A unique identifier for the course.

- MODULE

    - title (STRING): The title of the module.
    - id (INTEGER): A unique identifier for the module.

- ASSIGN

    - description (STRING): A description of the activity.
    - id (STRING): A unique identifier for the activity.
    - title (STRING): The title of the activity.
    - rubrics (STRING): Rubrics of the activity

- SCORM

    - description (STRING): A description of the activity.
    - id (STRING): A unique identifier for the activity.
    - title (STRING): The title of the activity.
    - rubrics (STRING): Rubrics of the activity

- FORUM

    - description (STRING): A description of the activity.
    - id (STRING): A unique identifier for the activity.
    - title (STRING): The title of the activity.
    - forum_type (STRING): The type of forum (e.g., general, Q&A).
    - rubrics (STRING): Rubrics of the activity

- QUIZ

    - description (STRING): A description of the activity.
    - id (STRING): A unique identifier for the activity.
    - title (STRING): The title of the activity.
    - quiz_max_grade (INTEGER): The maximum grade achievable in a quiz activity.
    - rubrics (STRING): Rubrics of the activity

- RESOURCE

    - description (STRING): A description of the resource.
    - id (STRING): A unique identifier for the resource.

- PROFILES
    - profile_name (STRING): profile name

#### Relationships and Their Properties

- Relation: CREATE
    - Description: Connects a TEACHER node to a COURSE node. Represents the relationship that a teacher has created a course.
    - Properties: None

- Relation: STUDY

    - Description: Connects a LEARNER node to a RESOURCE node.
    - Represents the relationship that a learner is studying or using a resource.
    - Properties: None

- Relation: REGISTERED

    - Description: Connects a LEARNER node to a COURSE node. Represents the relationship that a learner has registered for a course.
    - Properties: None

- Relation: PARTICIPATE

    - Description: Connects a LEARNER node to an ACTIVITY node. Represents the relationship that a learner is participating in an activity.
    - Properties:
        - grade (FLOAT): The grade received by the learner in the activity.
        - time (INTEGER): The time spent by the learner on the activity.     - attempts (INTEGER): The number of attempts made by the learner in the activity.
        - number_of_posts (INTEGER): The number of posts made by the learner in a forum activity.
        - submitted (INTEGER): Indicates whether the learner has submitted the activity (1 for yes, 0 for no).

- Relation: HAS_MODULE

    - Description: Connects a COURSE node to a MODULE node. Represents the relationship that a course contains one or more modules.
    - Properties: None

- Relation: BELONGS
    - Description: Connect the learner with the profile he/she belongs
    - Properties:
        - augMENTOR_profile_explanation (STRING): provide an explanation why a learner has been assign to a augMENTOR profile.

- Relation: HAS_ACTIVITY

    - Description: Connects a MODULE node to an ACTIVITY (SCORM, FORUM, ASSIGN, QUIZ) node. Represents the relationship that a module contains one or more activities.
    - Properties: None

- Relation: HAS_RESOURCE

    - Description: Connects an ACTIVITY node to a RESOURCE node.
    - Represents the relationship that an activity includes one or more resources.
    - Properties: None

#### Summary

This ontology represents the relationships and properties within a Moodle-based educational environment. It includes entities like teachers, learners, courses, modules, activities (forum, scorm, assign, quiz), and resources, each with specific properties. Relationships define how these entities interact, such as a teacher creating a course, a learner participating in activities, and the structure of courses into modules and activities. The properties of relationships, particularly for participation in activities, provide detailed data on learner engagement and performance.

### TryHackMe

This is the ontology used for developing the KG

<p align="center">
<img src=".\images\THM.png" width = "1000" alt="" align=center />
</p>

#### Nodes and Their Properties

- ROOM
    - difficulty (STRING): Level of difficulty for the content in the room (e.g., easy, medium, hard).
    - timeToComplete (STRING): Estimated time required to complete the room's content.
    - title (STRING): The title of the room.
    - ID (STRING): Unique identifier for the room.
    - description (STRING): Detailed description of the room.
    - type (STRING): The type or category of the room.
    - code (STRING): Any specific code associated with the room, possibly for access or reference.

- TUTORIAL
    - tutorials (STRING): URLs or identifiers for tutorials available for rooms.

- VIDEO
    - videos (STRING): URLs or identifiers for video content available for rooms.

- TASK

    - ID (STRING): Unique identifier for the task.

- QUESTION
    - questionNo (STRING): The number or identifier of the question within a task.
    - answer (STRING): The correct answer to the question.
    - extraPoints (STRING): Any additional points that can be earned by answering the question.
    - hint (STRING): Hints or tips to help solve the question.
    - question (STRING): The text of the question itself.

- MODULE
    - title (STRING): The title of the module.
    - moduleURL (STRING): URL linking to the module's content.
    - summary (STRING): A brief summary of the module.

- PATH
    - title (STRING): The title of the path.
    - difficulty (STRING): Overall difficulty level of the path.
    - summary (STRING): A brief summary of the path.
    - intro (STRING): An introduction to the path.
    - code (STRING): Specific code associated with the path, possibly for access or reference.

- PROFILES
    - profile_name (STRING): profile name

#### Relationships and their Properties

- Relation: HAS_TASK
    - Description: Connects ROOM nodes to TASK nodes.
    - Meaning: Indicates that a specific room contains a certain task.
    - Properties: None specified for this relationship.

- Relation: HAS_QUESTION
    - Description: Connects TASK nodes to QUESTION nodes.
    - Meaning: Indicates that a specific task contains a certain question.
    - Properties: None specified for this relationship.

- Relation: HAS_ROOM
    - Description: Connects MODULE nodes to ROOM nodes.
    - Meaning: Indicates that a module includes or is associated with a particular room.
    - Properties: order (INTEGER): The order in which the rooms appear within the module.

- Relation: BELONGS
    - Description: Connect the learner with the profile he/she belongs
    - Properties:
        - augMENTOR_profile_explanation (STRING): provide an explanation why a learner has been assign to a augMENTOR profile.
        
- Relation: HAS_MODULE
    - Description: Connects PATH nodes to MODULE nodes.
    - Meaning: Indicates that a specific path includes a certain module.
    - Properties: order (INTEGER): The order in which the modules appear within the path.

#### Summary

The ontology represents a structured framework for organizing educational content, particularly within Moodle. It defines different types of nodes (ROOM, TUTORIAL, VIDEO, TASK, QUESTION, MODULE, PATH) each with specific properties that describe their attributes. Relationships between these nodes indicate how they are connected and organized, with properties on some relationships specifying the sequence or order of the connections. This ontology provides a detailed blueprint for how educational content is structured and navigated, ensuring a coherent and logical flow of information for users.

## Contact 

Dimitris Charalambakis (dcharalampakis@novelcore.eu)
