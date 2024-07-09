# EU_augMENTOR

This repository contains the implementation of EU project: augMENTOR

**Abstract: ** AUGMENTOR aims to develop a novel pedagogical framework that promotes both basic skills and 21st century competencies by
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

- [EU\_augMENTOR](#eu_augmentor)
  - [Table of contents](#table-of-contents)
  - [Summary](#summary)
  - [How to run](#how-to-run)
    - [Use case: TryHackMe (THM)](#use-case-tryhackme-thm)
    - [Use case: MOODLE](#use-case-moodle)
  - [Next steps](#next-steps)
  - [Contact](#contact)

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

## Next steps


## Contact 
