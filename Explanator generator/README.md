# Project: augMENTOR
---

This is folder contains the implementation of **Explanator Generator and reporting engine**.

*Abstract*: Initially, an ontology was designed for the development of a Knowledge Graph (KG), which contains information about learners and modules. After the KG is developed and stored in a Graph DB (Neo4j Aura), the user is able to conduct queries in human-understandable text and retrieve replies as well as recommendations.

<br/>

## Ontology

This is the ontology used for developing the KG

<p align="center">
<img src=".\images\Ontology.png" width = "1000" alt="" align=center />
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
    - engagement (STRING): engagement report


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

## Connection with Moodle

The integration of educational data from Moodle to the augMENTOR platform is executed through a structured database connection protocol that ensures secure and reliable data transfer. The process initiates by establishing a direct connection to Moodle's MySQL database infrastructure using a comprehensive set of authentication parameters. These parameters include

- **Host:** The server address where the Moodle database is hosted
- **User:** The username authorized to access the database
- **Password:** The corresponding password for the database user
- **Port:** The network port used for the connection
- **Database Name:** The specific Moodle database to connect to

Prior to any data extraction, the system performs a multi-stage verification procedure that confirms successful authentication, validates the database server version, and enumerates the available data structures within the Moodle instance. This preliminary assessment phase is critical for ensuring that the connection is stable and that the target database environment is properly configured for data retrieval operations.

Notice that the connection remains active throughout the extraction phase, utilizing cursor-based operations to efficiently retrieve large datasets while maintaining transactional integrity. Each step of the process is monitored and logged, providing full traceability of the connection status, query execution, and data retrieval operations. This methodical approach ensures that the data transfer between Moodle and augMENTOR is conducted with the highest standards of security, reliability, and data governance, forming a robust foundation for the subsequent transformation and loading phases of the integration pipeline.

## Pipeline description in augMENTOR solution

### System Architecture Overview

The augMENTOR solution provides an intelligent educational assistance platform that enables users to obtain contextual feedback and personalized recommendations through a comprehensive dashboard interface. The system architecture integrates multiple specialized components to deliver accurate, relevant, and pedagogically sound responses to user inquiries.

Upon authentication through Zitadel, users can submit queries to the augMENTOR platform. Each query is processed along with contextual parameters including username, user role (learner or educator), and language preferences. The system routes user requests through two primary processing pathways:

**Feedback Processing Pipeline**: User queries are initially processed by the `Feedback generator` component, which provides immediate contextual responses. Subsequently, the generated feedback is forwarded to both the `Guidelines generator` and `Evaluator` components. The `Guidelines generator` produces actionable recommendations for improving course content and learner performance, while the `Evaluator` component assesses response quality across six critical dimensions:

- **Groundedness**: Factual accuracy and evidence-based content
- **Context Relevance**: Appropriateness to the specific educational context
- **Correctness**: Technical and pedagogical accuracy
- **Completeness**: Comprehensive coverage of the query topic
- **Answer Relevancy**: Direct alignment with user requirements
- **Faithfulness**: Consistency with source materials and learning objectives

**Recommendation Processing Pipeline**: For recommendation requests, the system extends the feedback processing by incorporating the `Recommendation engine`, which analyzes the query, user parameters, and generated feedback to produce personalized educational recommendations tailored to the user's specific learning context.

All generated feedback and guidelines are made available through the augMENTOR dashboard interface, while evaluation reports are systematically stored in the SQL database for continuous quality monitoring and system improvement.

<p align="center">
<img src=".\images\Process-overview.png" width = "1000" alt="" align=center />
</p>

### Feedback Generation Pipeline

The feedback generation process implements a sophisticated multi-stage validation and processing workflow designed to ensure content quality, appropriateness, and educational value.

**Initial Processing and Content Validation**
The pipeline initiates when users submit queries along with their contextual settings (username, role, and language preferences) to the `Feedback generator` module. This module serves as the primary entry point, capturing essential user context to ensure personalized response generation.

All user queries undergo mandatory content screening through the `Offensive Content Identification` module, which employs advanced filtering mechanisms to detect inappropriate language or content violations. Queries identified as containing offensive material are immediately flagged, and users receive explanatory feedback regarding the content policy violation, terminating the processing pipeline at this stage.

**Role-Specific Query Processing**
For learner-submitted queries, the system implements an additional validation layer through the `Learner Question Validator & Transformer` module. This component ensures queries comply with educational guidelines by preventing requests for peer information or inappropriate content sharing. Valid learner queries undergo automatic linguistic transformation from first-person to third-person phrasing (e.g., "Give me my grades" becomes "Provide the grades of learner 'trooper'"), standardizing query format for consistent downstream processing.

**Knowledge Retrieval and Response Generation**
Validated queries are processed by the `Query Transformer to Cypher` module, which converts natural language queries into Cypher query syntax for Knowledge Graph (KG) interaction. The generated Cypher queries execute against the KG database to retrieve relevant educational data and contextual information.

Concurrently, the `Instruction Retriever` module accesses the instructional database to gather predefined educational guidelines, procedural instructions, and contextual information relevant to the user's query domain.

The `Context-based Feedback Generator` synthesizes all retrieved information—including KG data, instructional content, and user context—to generate comprehensive, educationally appropriate responses tailored to the user's specific requirements and role within the learning environment.

<p align="center">
<img src=".\images\Feedback-pipeline.png" width = "1000" alt="" align=center />
</p>

### Recommendation Generation Pipeline

The recommendation pipeline extends the feedback generation process by incorporating additional analytical components to provide personalized educational guidance and actionable insights.

**Multi-Stage Processing Architecture**
The recommendation workflow begins with query submission to the `Feedback generator`, which processes user input alongside contextual parameters (username, role, language) to generate initial educational feedback. This preliminary response provides immediate value while serving as input for subsequent recommendation processing stages.

**Instruction Integration and Recipient Analysis**
The system forwards both the original query and generated feedback to the `Instruction Retriever` module, which accesses the instructional database to gather relevant educational guidelines, best practices, and domain-specific content. This retrieved instructional content enriches the recommendation context with pedagogically sound guidance.

Simultaneously, the `Receiver identification` module analyzes the query and initial feedback to determine appropriate recommendation recipients, which may include educators, learners, course administrators, or other stakeholders within the educational ecosystem.

**Comprehensive Recommendation Synthesis**
The `Recommendation Generator` module integrates inputs from all previous components—original user query, initial feedback, retrieved instructions, and identified recipients—to produce comprehensive, personalized recommendations. This synthesis process ensures that recommendations are contextually appropriate, pedagogically sound, and actionable for each identified recipient.

The resulting recommendations provide detailed guidance tailored to user roles and educational contexts, enabling effective decision-making and educational improvement initiatives across the learning environment.

<p align="center">
<img src=".\images\Recommendation-pipeline.png" width = "1000" alt="" align=center />
</p>

### Component Specifications

#### Core Components

**`Feedback generator`**
- **Input**: User query, configuration settings (username, role, language)
- **Output**: Contextual educational feedback and information response

**`Recommendation engine`**
- **Input**: User query, configuration settings (username, role, language)
- **Output**: Personalized educational recommendations and guidance

#### Processing Sub-Components

**`Offensive Content Identification`**
- **Input**: User query
- **Output**: Content appropriateness determination with explanatory feedback for flagged content

**`Learner Question Validator & Transformer`**
- **Input**: User query (learner-specific)
- **Output**: Query validation status and first-person to third-person linguistic transformation

**`Query Transformer to Cypher`**
- **Input**: Validated user query
- **Output**: Cypher query syntax for Knowledge Graph data retrieval

**`Instruction Retriever`**
- **Input**: User query context
- **Output**: Relevant educational instructions and guidelines from database

**`Context-based Feedback Generator`**
- **Input**: User query, retrieved instructions, Knowledge Graph information
- **Output**: Comprehensive contextual educational feedback

**`Receiver Identification`**
- **Input**: User query, generated feedback from `Feedback generator`
- **Output**: Identification of recommendation recipients (educators, learners, administrators)

**`Recommendation Generator`**
- **Input**: User query, database instructions, feedback from `Feedback generator`
- **Output**: Comprehensive personalized recommendations tailored to identified recipients

<br/>

## How to run

1. Create a virtual environment 
```
    python -m  venv .env
```

2. Activate the virtual environment 
```
    source .env/bin/activate
```
3. Install requirements 
```
    pip install -r requirements.txt
```
4. Run notebooks
```
    Moodle_to_Neo4J.ipynb
    Recommendation_engine.ipynb
```

- `Moodle_to_Neo4J.ipynb:` Connect to Moodle DB, retrieves the data for all courses and import them to Neo4j.
- `Recommendation_engine.ipynb:` Connects with Neo4j database and then the user is able to conduct queries on the KG as well as retrieve recommendations.

<br/>




## Feedback evaluation

When a user submits a query to the platform, the system will return a response along with an optional evaluation report. The evaluation report will include detailed reasoning and scoring for the following metrics:

- Groundedness: Is the answer supported by the context?
- Context Relevance: Is the context relevant to the question?
- Correctness: Are the facts accurate?
- Completeness: Does it fully answer the question?
- Answer Relevancy: Is the answer focused on the query?
- Faithfulness: Is it faithful to the context?

```json
{
  "Groundedness": {
    "reasoning": "<step-by-step explanation>",
    "score": "<score>"
  },
  "Context Relevance": {
    "reasoning": "<step-by-step explanation>",
    "score": "<score>"
  },
  "Correctness": {
    "reasoning": "<step-by-step explanation>",
    "score": "<score>"
  },
  "Completeness": {
    "reasoning": "<step-by-step explanation>",
    "score": "<score>"
  },
  "Answer Relevancy": {
    "reasoning": "<step-by-step explanation>",
    "score": "<score>"
  },
  "Faithfulness": {
    "reasoning": "<step-by-step explanation>",
    "score": "<score>"
  },
  "total_score": "<total_score>"
}
```

### Review of component: `Feedback Evaluation`

However, for `Feedback Evaluation` the following limitations/consideration must be taken into account:

- **Model Bias Toward Self-Generated Outputs**  
  Large Language Models (LLMs) tend to favor responses generated by the same or similar models, potentially introducing evaluation bias.

- **Score Distribution Instability**  
  When using numerical rating scales (e.g., 1–5, 1–10), LLMs often default to mid-range values, resulting in *mode collapse*. This limits scoring diversity and reduces evaluation precision.  
  See: [arXiv:2305.17926](https://arxiv.org/abs/2305.17926), [arXiv:2303.16634](https://arxiv.org/abs/2303.16634), [arXiv:2405.07437](https://arxiv.org/abs/2405.07437)

- **Philosophical and Epistemological Concerns**  
  The enduring question "*Who watches the watchmen?*" highlights the difficulty of validating LLM-based judgments in the absence of a trusted ground truth or consistent human baseline.

- **Evaluating references is particularly tricky.** 
    A reference may be technically correct based on outdated knowledge (e.g., an old law), while a newer, more relevant source exists but wasn't retrieved. In such cases, the model may appear to perform well, but actually miss the most up-to-date information.

- **Metrics such as correctness can be inherently subjective**
    - How is correctness defined in ambiguous or open-ended queries? how do we know, which answers are actually true/correct?
    - How are hallucinations detected or accounted for, especially in domains like law, where factual accuracy is critical and nuanced?

**Outcome:** Finally, we also point out that a hybrid approach, which combines LLM evaluation, an MCP server with expert human oversight and possibly the use of reference datasets or legal ontologies to anchor factual accuracy, is the best feasible option.