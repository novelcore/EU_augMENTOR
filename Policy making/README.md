# Educational Policy Recommendations System

## Overview

This system generates tailored educational policy recommendations for institutions based on learner performance data and the augMENTOR profiling framework. The recommendations are designed to help policy makers improve educational processes, outcomes and learners' 21st-century skills using evidence-based insights aligned with the TESA (Technology Enhanced Student Assessment) framework.

## Features

- **Multi-institutional Support**: Generates recommendations for three pilot institutions: IASIS, UPAT and EASD
- **Skills-based Analysis**: Evaluates learner performance across cognitive and 21st-century skills (4Cs: Critical Thinking, Communication, Collaboration and Creativity) as well as Cognitive
- **Profile-driven Insights**: Utilizes augMENTOR learner profiles to provide personalized recommendations
- **TESA Framework Integration**: Ensures recommendations are pedagogically sound and research-backed
- **Multi-language Support**: Generates recommendations in multiple languages (default: English)

## System Architecture

### Core Components

1. **Data Retrieval Module** (`get_grades()`): Extracts learner performance data from Neo4j database
2. **AI-powered Analysis** (`generate_policy_recommendations()`): Uses OpenAI to generate contextual recommendations
3. **Policy Generation** (`get_policy_recommendations()`): Orchestrates the complete recommendation process
4. **Output Formatting**: Structures recommendations into actionable policy documents

### Dependencies

- **Database**: Neo4j for storing learner data and course information
- **AI Service**: OpenAI API for generating intelligent recommendations
- **Python Libraries**:
  - `neo4j`: Database connectivity
  - `openai`: AI-powered text generation
  - `json`: Configuration and data handling
  - `ast`: Safe evaluation of AI responses

## Data Structure

### Learner Profiles (augMENTOR)
The system categorizes learners into distinct profiles based on their characteristics and learning tendencies. Each profile has:
- **Short Description**: Brief characterization of the profile
- **Detailed Description**: Comprehensive explanation of learner traits
- **Performance Patterns**: Historical data on strengths and weaknesses

### Skills Assessment (4Cs + Cognitive)
- **Cognitive**: Core academic and intellectual abilities
- **Critical Thinking**: Analysis, evaluation and reasoning skills
- **Communication**: Expression and information sharing abilities
- **Collaboration**: Teamwork and cooperative learning skills
- **Creativity**: Innovation and creative problem-solving abilities

*Note: UPAT pilot focuses on Cognitive, Critical Thinking and Creativity skills only.*

## Configuration

### Required Configuration Files

1. **`Resources/neo4j_settings.json`**
   ```json
   {
     "uri": "bolt://localhost:7687",
     "user": "neo4j",
     "password": "your_password"
   }
   ```

2. **`Resources/openai_settings.json`**
   ```json
   {
     "api_key": "your_openai_api_key",
     "model_name": "gpt-4",
     "temperature": 0.7
   }
   ```

3. **`Resources/profiles_description.json`**
   Contains detailed descriptions of augMENTOR profiles for each pilot institution.

## Usage

### Basic Usage

```python
# Import required modules
import os
import json
import openai
from utils.neo4j_connection import neo4j_connection
from utils.policy_recommendations import get_policy_recommendations

# Load configurations
with open("Resources/neo4j_settings.json", "r") as file:
    neo4j_settings = json.load(file)
with open("Resources/openai_settings.json", "r") as file:
    openai_settings = json.load(file)

# Initialize connections
openai.api_key = openai_settings["api_key"]
graph = neo4j_connection(neo4j_settings=neo4j_settings, clean_graph=False)

# Generate recommendations
response = get_policy_recommendations(
    graph=graph,
    pilot="IASIS",  # Institution name
    course_id=2,    # Course identifier
    openai_settings=openai_settings,
    language="English"  # Optional: specify output language
)
```

### Batch Processing

The system supports batch processing for multiple institutions and courses:

```python
# Generate recommendations for all configured pilots and courses
pilots_courses = [
    ("IASIS", 2), ("IASIS", 4), ("EASD", 11), 
    ("UPAT", 16), ("UPAT", 33)
]

for pilot, course_id in pilots_courses:
    response, structure_response = get_policy_recommendations(
        graph=graph,
        pilot=pilot,
        course_id=course_id,
        openai_settings=openai_settings
    )
    
    # Save to file
    filename = f"{path}/{pilot}_{course_id}.md"
    print(f"[INFO] Storing policy recommendations in file: {filename}")
    with open(filename, "w", encoding="utf-8") as file:
        file.write(response)
    filename = f"{path}/{pilot}_{course_id}.jsonl"
    with open(filename, "w", encoding="utf-8") as f:
        for record in structure_response:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
```

## Output Structure

Generated recommendations follow a structured format:

### 1. General Feedback
- Executive summary of findings
- Overall performance insights across all profiles

### 2. Discussion about Learners' Profiles
- Detailed characteristics of each augMENTOR profile
- Profile-specific learning tendencies and preferences

### 3. Insights about Performance
- Data-driven analysis of each profile's performance
- Identification of strengths and weaknesses
- Key observations and patterns

### 4. Policy Recommendations for Supporting Learners
- Targeted interventions for each learner profile
- Course-integrated strategies
- Skill development activities aligned with TESA framework

### 5. Policy Recommendations for Supporting Educators and Course Providers
- Educator-focused strategies and tools
- Implementation guidelines with clear timelines
- Methods for supporting different learner profiles

## TESA Framework Integration

The Technology Enhanced Student Assessment (TESA) framework provides the pedagogical foundation for all recommendations. The system ensures that:

- All policies reference specific TESA phases and components
- Recommendations are evidence-based and research-backed
- Implementation strategies are pedagogically sound
- Assessment methods align with modern educational practices

## Supported Institutions

### IASIS
- Courses: 2, 4
- Skills: Full 4Cs + Cognitive assessment

### EASD
- Courses: 11
- Skills: Full 4Cs + Cognitive assessment

### UPAT
- Courses: 16, 33
- Skills: Cognitive, Critical Thinking and Creativity (limited collaboration and communication assessment)

## File Organization

```
Project/
├── Resources/
│   ├── neo4j_settings.json
│   ├── openai_settings.json
│   └── profiles_description.json
├── utils/
│   ├── neo4j_connection.py
│   ├── policy_recommendations.py
│   └── utils.py
├── Recommendations/          # Generated output files
│   ├── IASIS_2.jsonl
│   ├── IASIS_2.md
│   ├── IASIS_4.jsonl
│   ├── IASIS_4.md
│   ├── EASD_11.jsonl
│   ├── EASD_11.md
│   ├── UPAT_16.jsonl
│   ├── UPAT_16.md
│   └── UPAT_33.jsonl
│   └── UPAT_33.md
└── README.md
```

## Error Handling

The system includes comprehensive error handling:

- Database connection failures
- OpenAI API rate limits and errors
- Missing course or profile data
- Invalid configuration files

Errors are logged with descriptive messages to facilitate debugging.

## Customization

### Adding New Institutions
1. Update `profiles_description.json` with new institution profiles
2. Add institution-specific course IDs to the processing loop
3. Ensure Neo4j database contains relevant course and learner data

### Modifying Skills Assessment
1. Update the skills list in the `get_policy_recommendations()` function
2. Ensure database schema supports additional skill metrics
3. Update profile descriptions to reflect new assessment criteria

### Language Localization
The system supports multiple output languages. Simply specify the desired language in the `language` parameter when calling `get_policy_recommendations()`.

## Contributing

When contributing to this system:

1. Maintain compatibility with existing Neo4j schema
2. Ensure TESA framework alignment in new recommendations
3. Test with all supported institutions and courses
4. Update documentation for any new features or changes


# Contact

Ioannis Livieris (livieris@novelcore.eu)