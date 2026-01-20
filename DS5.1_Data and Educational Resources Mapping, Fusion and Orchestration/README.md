# Project: augMENTOR
---

An ontology was designed for the development of a Knowledge Graph (KG), which contains information about learners and modules. After the KG is developed and stored in a Graph DB (Neo4j Aura), the user is able to conduct queries in human-understandable text and retrieve replies as well as recommendations.

<br/>

## Table of contents

- [Ontology](#ontology)
    - [Nodes and their properties](#nodes-and-their-properties)
    - [Relationships and their properties](#relationships-and-their-properties)
    - [Summary](#summary)
- [Contact](#contact)

<br/>

## Ontology

This is the ontology used for developing the KG

<p align="center">
<img src=".\Ontology.png" width = "1000" alt="" align=center />
</p>


### Nodes and Their Properties

> Node: TEACHER

- username (STRING): The username of the teacher.
- country (STRING): The country where the teacher is located.
- institution (STRING): The institution the teacher is affiliated with.
- user_id (INTEGER): A unique identifier for the teacher.
- email (STRING): Teacher's email

> Node: LEARNER

- username (STRING): The username of the learner.
- country (STRING): The country where the learner is located.
- institution (STRING): The institution the learner is affiliated with.
- user_id (INTEGER): A unique identifier for the learner.
- email (STRING): Learner's email

> Node: COURSE

- description (STRING): A description of the course.
- title (STRING): The title of the course.
- id (INTEGER): A unique identifier for the course.

> Node: MODULE

- id (INTEGER): A unique identifier for the module.
- title (STRING): The title of the module.
- description (STRING): Module's description
- url(STRING): Moodle URL

> Node: ASSIGN

- id (STRING): A unique identifier for the activity.
- title (STRING): The title of the activity.
- description (STRING): A description of the activity.
- url (STRING): Moodle URL

> Node: FORUM

- id (STRING): A unique identifier for the activity.
- title (STRING): The title of the activity.
- description (STRING): A description of the activity.
- url (STRING): Moodle URL

> Node: QUIZ

- id (STRING): A unique identifier for the activity.
- title (STRING): The title of the activity.
- description (STRING): A description of the activity.
- url (STRING): Moodle URL

> Node: RESOURCE

- description (STRING): A description of the resource.
- title (STRING): The title of the resource.
- id (STRING): A unique identifier for the resource.
- url (STRING): Moodle URL

> Node: PROFILES

- profile_name (STRING): profile name
- description (STRING): A description of the profile.

### Relationships and Their Properties

> Relation: CREATE

- **Description:** Connects a TEACHER node to a COURSE node. Represents the relationship that a teacher has created a course.
- **Properties:** None

> Relation: STUDY

- **Description:** Connects a LEARNER node to a RESOURCE node. Represents the relationship that a learner is studying or using a resource.
- **Properties:** 

- number_of_submissions (INTEGER): Number of submissions
- session_time: Session time devoted for the scorm
- status: Status of scorm: {'complete', 'incomplete'}
- total_time: Total time devoted for the scorm

> Relation: REGISTERED

- **Description:** Connects a LEARNER node to a COURSE node. Represents the relationship that a learner has registered for a course.
- **Properties:** None

> Relation: PARTICIPATE

- **Description:** Connects a LEARNER node to an ACTIVITY (FORUM, QUIZ, ASSIGN, SCORM) node. Represents the relationship that a learner is participating in an activity.

- **Properties:**

    - Cognitive grade (FLOAT): The cognitive grade received by the learner in the activity.
    - Creativity grade (FLOAT): The creativity grade received by the learner in the activity.
    - Collaboration grade (FLOAT): The collaboration grade received by the learner in the activity.
    - Critical thinking grade (FLOAT): The critical thinking grade received by the learner in the activity.
    - Communication grade (FLOAT): The communication grade received by the learner in the activity.
    - Cognitive reasoning (STRING): The rubrics utilized for grading the learner in the activity relative to Cognitive
    - Creativity reasoning (STRING): The rubrics utilized for grading the learner in the activity relative to Creativity
    - Collaboration reasoning (STRING): The rubrics utilized for grading the learner in the activity relative to Collaboration
    - Critical thinking reasoning (STRING): The rubrics utilized for grading the learner in the activity relative to Critical thinking
    - Communication reasoning (STRING): The rubrics utilized for grading the learner in the activity relative to Communication
    - time (INTEGER): The time spent by the learner on the activity.     
    - number_of_attempts (INTEGER): The number of attempts made by the learner in a quiz activity.
    - number_of_completed_attempts (INTEGER): The number of completed attempts made by the learner in a quiz/scorm activity.
    - number_of_posts (INTEGER): The number of posts made by the learner in a forum activity.
    - number_of_clicks (INTEGER): Indicates the number of clicks each learner conducted for an activity
    - number_of_discussions (INTEGER): Indicates the number of discussion each learner created in a forum activity.
    - number_of_submissions (INTEGER): Indicates the number of submissions each learner conducted for an activity


> Relation: HAS_MODULE

- **Description:** Connects a COURSE node to a MODULE node. Represents the relationship that a course contains one or more modules.
- **Properties:** None

> Relation: BELONGS

- **Description:** Connect the learner with the profile he/she belongs
- **Properties:**
    - augMENTOR_profile_explanation (STRING): provide an explanation why a learner has been assign to a augMENTOR profile.
    - course_id (INTEGER): Course ID

> Relation: HAS_ACTIVITY

- **Description:** Connects a MODULE node to an ACTIVITY (SCORM, FORUM, ASSIGN, QUIZ) node. Represents the relationship that a module contains one or more activities.
- **Properties:** None

> Relation: HAS_RESOURCE

- **Description:** Connects an ACTIVITY node to a RESOURCE node. Represents the relationship that an activity includes one or more resources.
- **Properties:** None

### Summary

This ontology represents the relationships and properties within a Moodle-based educational environment. It includes entities like teachers, learners, courses, modules, activities (forum, scorm, assign, quiz), and resources, each with specific properties. Relationships define how these entities interact, such as a teacher creating a course, a learner participating in activities, and the structure of courses into modules and activities. The properties of relationships, particularly for participation in activities, provide detailed data on learner engagement and performance.

<br/>
