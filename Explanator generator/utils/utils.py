import re
import time
import json 
import math
import numpy as np
from typing import Union, Dict
seed = 42
np.random.seed(seed)

# The available_metrics list contains five strings that represent key skills or competencies typically assessed in educational or performance settings. 
available_metrics = ["Cognitive", "Creativity", "Collaboration", "Critical thinking", "Communication"]
engagement_metrics = ["Total time", "Number of clicks", "Number of actions", "Number of submissions"]

# This color class is a simple utility that defines various ANSI escape codes for formatting text in terminal outputs. 
# ANSI escape sequences allow for colorization and styling of text when printed in compatible terminals.
class color: 
   '''
           Define class variables for different color codes using ANSI escape sequences
   '''
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   ITALICS = '\033[3m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

def get_indicator_emoji(indicator: str = None) -> str:
    """
    Return an emoji corresponding to a given indicator.

    Args:
        indicator (str, optional): The name of the indicator.
            Supported values:
                - "Cognitive" -> 🧠
                - "Creativity" -> 🎨
                - "Collaboration" -> 🤝
                - "Critical thinking" -> 💭
                - "Communication" -> 💬
            Defaults to None.

    Returns:
        str: An emoji string representing the indicator.
             Returns an empty string if the indicator is not recognized.
    """
    if indicator == "Cognitive":
        return "🧠"
    elif indicator == "Creativity":
        return "🎨"
    elif indicator == "Collaboration":
        return "🤝"
    elif indicator == "Critical thinking":
        return "💭"
    elif indicator == "Communication":
        return "💬"
    else:
        return ""

def get_color_indicator(score: float = None) -> str:
    """
    Returns a color-coded indicator emoji based on the score value.

    Parameters
    ----------
    score : float, optional
        A numeric score between 0 and 100.
        - >= 95  : 🟣 (Outstanding/Perfect)
        - >= 90  : 🟢 (Excellent)
        - >= 80  : 🔵 (Very Good)
        - >= 70  : 🟡 (Good)
        - >= 60  : 🟠 (Satisfactory)
        - >= 50  : 🟤 (Fair/Needs Improvement)
        - < 50   : 🔴 (Poor)
        If None is provided, returns a neutral indicator.

    Returns
    -------
    str
        An emoji string representing the performance level.
    """
    if score is None:
        return "⚪"  # Neutral / undefined score

    if score >= 95:
        return "🌟"   # Outstanding/Perfect (Purple)
    elif score >= 90:
        return "🟢"   # Excellent (Green)
    elif score >= 80:
        return "🔵"   # Very Good (Blue)
    elif score >= 70:
        return "🟡"   # Good (Yellow)
    elif score >= 60:
        return "🟠"   # Satisfactory (Orange)
    elif score >= 50:
        return "🟤"   # Fair/Needs Improvement (Brown)
    else:
        return "🔴"   # Poor (Red)


def clean_KG_query_response(response:list=None):
    """
    Clean and deduplicate a list of dictionaries returned from a Knowledge Graph (KG) query.

    This function performs two main tasks:
      1. Removes key-value pairs where the value is None.
      2. Removes duplicate dictionaries while preserving the original order.

    Args:
        response (list[dict]): A list of dictionaries representing KG query results.

    Returns:
        list[dict]: A new list containing unique dictionaries (with None values removed).

    Example:
        >>> data = [
        ...     {'user': 'alice', 'score': None},
        ...     {'user': 'bob', 'score': 90},
        ...     {'user': 'alice', 'score': None}
        ... ]
        >>> clean_KG_query_response(data)
        [{'user': 'alice'}, {'user': 'bob', 'score': 90}]
    """
    response = [{k: v for k, v in d.items() if v is not None} for d in response]
    unique = []
    seen = set()
    for d in response:
        t = tuple(sorted(d.items()))
        if t not in seen:
            seen.add(t)
            unique.append(d)
    return unique


def get_performance_emoji(score: float) -> str:
    """
    Return an emoji representing performance level based on score.

    Args:
        score (float): Performance score between 0 and 100.

    Returns:
        str: Emoji indicating performance category:
             - 🌟 for score >= 85
             - ✅ for score >= 65
             - ⚠️ for score >= 50
             - 📉 for score < 50
    """
    if score >= 85:
        return "🌟"
    elif score >= 65:
        return "✅"
    elif score >= 50:
        return "⚠️"
    else:
        return "📉"

tesa_framework = """# TESA Framework

## The Teaching Object of the Educational Scenario

In **Phase A**, the teaching subject to be studied is defined, including the course content and key components of the scenario. This phase focuses on identifying specific points of the learning object, including:

- Scenario title and theme  
- Target class(es)  
- Relevant knowledge areas  
- Curriculum alignment  
- Duration for classroom implementation  

Once the teaching subject is defined, the **primary components** of the scenario must be identified, such as:

- Prerequisite knowledge learners should have  
- Prior knowledge learners already possess  
- Justification for the scenario's appropriateness for the learners' level  

This phase is **exclusively for educators** and does **not** involve learners.

### Key Questions

1. What are the individual sections of the scenario that introduce and build the concept(s) to be studied?
2. Does the scenario take into account prerequisite knowledge? How is it integrated?
3. Does the scenario consider learners' prior knowledge? How is it used in constructing new knowledge?
4. Is the scenario appropriate for the learners' knowledge level?

Additionally, define cognitive prerequisites related to **Emerging Technologies**, such as software and tools to be used.

## Learners' Representations and Possible Difficulties

This phase uses relevant literature and teacher experience to identify learners' **difficulties and misconceptions**.

### Key Tasks

- Identify learners' **prior ideas and representations**
- Document **common misconceptions**
- Organize **cognitive difficulties** learners face

These insights are critical for defining:

- Scenario objectives (Phase C)  
- Teaching materials (Phase D)  
- Learning activities (Phase E)  

### Key Questions

1. How are learners' prior ideas and representations detected and transformed?
2. How are misconceptions identified and addressed?
3. What cognitive difficulties are considered and how are they addressed?

This phase connects the scenario with findings from **science education research** and teacher experience.

## Purpose, Objectives, and Learning Outcomes

This phase defines the **purpose** and **learning outcomes** of the scenario.

### Two Axes of Learning Objectives

**a) Subject Matter and Learning Process:**

- Based on the curriculum and learners' cognitive difficulties
- Used to define:
  - Learning activities (Phase E)
  - Teaching materials (Phase D)
  - Use of Emerging Technologies

Objectives can be:

- **High-level** (e.g., 4Cs competencies)
- **Low-level** (e.g., knowledge, skills, attitudes)

**b) Use of Emerging Technologies:**

- Objectives focus on integrating technology into teaching
- Emphasize **added value** and **innovative practices**

## Teaching Material of the Educational Scenario

This phase describes all materials needed:

- **Ready-made materials** (e.g., printed worksheets, maps, software)
- **Custom materials** created for the scenario
- **Infrastructure** (e.g., computers, projectors)

Worksheets and educational software are detailed, including their usage. Materials must support in-class **implementation activities**.

## Activities for Implementation in the Classroom

This critical phase details classroom procedures for teachers and learners.

### Requirements

- Define theoretical and methodological approach  
- Outline teaching approaches and strategies  
- Emphasize the integration of **Emerging Technologies**  

### Types of Activities

1. **Psychological and cognitive preparation**
2. **Teaching new knowledge**
3. **Consolidation of subject matter**
4. **Assessment**
5. **Metacognition**

These activities follow a **structured lesson plan** and are often proposed via **e-sheets**.

## Evaluation of the Educational Scenario

Evaluation focuses on **learning progression** and **scenario effectiveness**.

### Types of Evaluation

- **Formative:** Ongoing, during implementation  
- **Final:** Summative, post-implementation  

Evaluation considers:

- Achievement of learning objectives  
- Use of tools and technologies  
- Implementation process effectiveness  

Evaluation is grounded in **Activity Theory**.

## Technology-Augmented e-Activities (In Situ and Online)

This section defines **pedagogical activity** using **PeDeMET** principles and **Activity Theory**.

### Components of Pedagogical Activity

1. **Context**  
   - Subjects (learners and teacher), difficulty, environment, expected outcomes
2. **Strategies**  
   - Learning/teaching models and theories
3. **Processes**  
   - Activity types, techniques, tools, interaction roles, evaluation methods

Pedagogical activities guide both **teacher and learner actions**, often designed by **educational software teams**.

### Categories of Pedagogical Activities

#### a) Cognitive and Psychological Preparation

- Assess pre-existing knowledge  
- Detect cognitive schemas and representations  
- Create emotional security and prepare learners for the lesson

#### b) Teaching Activities of the Subject Matter

- Introduce knowledge and build new concepts  
- Integrate Emerging Technologies  
- Use strategies like inquiry, collaboration, problem-solving, and project-based learning

#### c) Consolidation Activities

- Focus on **application and assimilation**  
- Use similar strategies to teaching phase  
- Aim for **high-level competencies**

#### d) Assessment Activities

- Evaluate what learners have/haven't learned  
- Include self-assessment and peer assessment  
- Support formative evaluation and redesign

#### e) Metacognitive Activities

- Summarize and reflect on the lesson  
- Compare initial ideas with new knowledge  
- Support homework and deeper learning  
- Include self-assessment, peer feedback, and discussion

## Summary Flow of Activities

The typical progression:

1. **Cognitive/Psychological Preparation**
2. **Teaching**
3. **Consolidation**
4. **Assessment**
5. **Metacognition**

Activities may be conducted **in situ** (synchronously) or **online** (asynchronously).

Each activity must identify:

- Learning objectives  
- Teaching strategies  
- Use and value of technology  

Worksheets and e-sheets are derived directly from these structured activities."""

def update_response(text:str=None, d_abbreviations:dict=None)->str:
    '''
        Update a text containing some abbreviations with the meaning of each abbreviation.
        For example:
        input: Next, we present the requested description: Description_Activitity_14, ...
        output: Next, we present the requested description: This activitity focuses on improving the indicators: Creativity, Collaboration\nFor successfully performing the activity, the learner ...

        Parameters
        ----------
        text: (str)
            input text for replacing abbreviations 
        d_abbreviations: (dict)
            dictionary with keys the abbreviations and values their corresponding meanining

        Returns
        -------
            text with its abbreviations replaced with their corresponing meaning
    '''
    for key in d_abbreviations:
        if key in text: text = text.replace(key, d_abbreviations[key])        
    
    return text


def calculate_trent(values:list=None)->float:
    '''
        Given a list of grades of a specific metric, this function implements the trent using linear regression

        Parameters
        ----------
        grades: (list)
            list of grades

        Returns
        -------
        trent (float)
    '''
    # Extract x and y values from the points
    x_values = np.array([i for i in range(len(values))])
    y_values = np.array(values)


    # Calculate the necessary statistics
    n = len(x_values)
    sum_x = np.sum(x_values)
    sum_y = np.sum(y_values)
    sum_x_squared = np.sum(x_values**2)
    sum_xy = np.sum(x_values * y_values)

    # Calculate the coefficient(s)
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x_squared - sum_x**2)

    return slope

def load_json_to_dict(input_path:str=None, file_encoding:str='utf-8') -> dict:
    """
        Load a json file to a dictionary form.

        Parameters
        ----------
        input_path: (str)
            input path
        file_encoding: (str)
            file encoding (utf-8 is default)

        Return
        ------
        JSON file contents 
    """
    json_dict = {}
    with open(input_path, 'r', encoding = file_encoding) as json_file:
        json_dict = json.load(json_file)
    return json_dict



def save_dict_to_json(dictionary:dict=None, output_path:str=None, file_encoding:str='utf-8', separators=(',', ':')):
    """
        Function that tries to save a dict to a human readable json file.
        If the write attempt fails, then it retries for a short time period.
        Finally an error is logged.

        Parameters
        ----------
        dictionary: (dict)
            dictionary to be saved
        output_path: (str)
            output path
        file encoding: (str)
            file_encoding
        separators: tuple
            separators for saving file in JSON
    """
    for _ in range(5):
        try:
            with open(output_path, 'w', encoding = file_encoding) as file:
                json.dump(
                    dictionary, file, ensure_ascii = False, separators = separators
                )
            print(f"[INFO] Dictionary was saved in {output_path}")
        except Exception as e:
            print(f"[ERROR] Dictionary was not saved in {output_path}")
            print(f" > {e}")
            time.sleep(0.1)
            continue


def include_links(input: Union[str, Dict], d_links: Dict[str, str]) -> Union[str, Dict]:
    """
    Replaces occurrences of activity or resource identifiers with their corresponding 
    formatted Markdown links in a given input (string or dictionary of strings).

    Args:
        input (str | dict): The input data where links should be replaced. If it's a 
                            dictionary, replacements occur in its values (which should be strings).
        d_links (dict): A dictionary mapping identifiers (e.g., "Quiz:19", "Quiz 19") 
                        to their respective formatted Markdown links.

    Returns:
        str | dict: The modified input with identifiers replaced by their corresponding 
                    links. If the input is a dictionary, it will return the updated dictionary.
    """
    if isinstance(input, dict):
        # Iterate over the dictionary to replace links in each string value
        for item in input:
            for key, value in d_links.items():
                # Replace all variations of 'module'
                input[item] = re.sub(key, value, input[item], flags=re.IGNORECASE)
                input[item] = re.sub(key.replace(":", " "), value, input[item], flags=re.IGNORECASE)
    else:
        # Replace links in the input string directly
        for key, value in d_links.items():
                input = re.sub(key, value, input, flags=re.IGNORECASE)
                input = re.sub(key.replace(":", " "), value, input, flags=re.IGNORECASE)    
    return input


def assignment_4C(value: str = None, available_metrics:list=available_metrics):
    """
    Identifies and returns the first matching metric from `available_metrics` 
    that is present in the provided string `value`.

    Parameters:
    value (str): A string to be checked against the list of metrics. 
                 If `None` is provided, the function will return `None`.

    Returns:
    str: The first matching metric from `available_metrics`, or `None` if no match is found.
    """
    for metric in available_metrics:
        if metric.lower().split("_")[0] in value.lower():
            return metric
    return None


def text_preprocess(text:str=None)->str:
    '''
        Text preprocessing

        Parameters
        ----------
        text: input text

        Returns
        -------
        preprocessed text
    '''
    # Replace tabs
    text = text.replace('\t', ' ')
    # Remove multiple spaces using a regular expression
    text = re.sub(' +', ' ', text) 
    text = re.sub(r'\.+', ".", text)
    # Remove errors
    text = re.sub('\xa0', ' ', text)
    text = text.replace("\x07","")
    # Other processing steps
    text = text.replace("’","'")
    text = text.replace('"',"'")
    
    return text.strip()

def strip_accents_and_lowercase(s:str=None)->str:
    '''
    Quick strip accents and lowercase
    Parameters
    ----------
    s: text

    Returns
    -------
    text with stripped accents and lowercase
    '''
    s = s.lower()
    s = s.replace('ά','α').replace('έ','ε').replace('ή','η').replace('ί','ι').replace('ό','ο').replace('ύ','υ').replace('ώ','ω')
    s = s.replace('ϊ','ι').replace('ϋ','υ')
    s = s.replace('ΐ','ι').replace('ΰ','υ')
    return s


def format_time(time:int=None, language:str='english'):
    """
    Format time in seconds to a human-readable string in English, Greek, or Serbian.

    Args:
        time (int/float): Time in seconds
        lang (str): Language code ('english', 'greek', 'serbian')

    Returns:
        str: Formatted time string
    """
    labels = {
        'english': {
            'day': 'day', 'days': 'days',
            'hour': 'hr', 'hours': 'hrs',
            'minute': 'min', 'minutes': 'mins',
            'second': 'sec', 'seconds': 'secs'
        },
        'greek': {
            'day': 'ημέρα', 'days': 'ημέρες',
            'hour': 'ώρα', 'hours': 'ώρες',
            'minute': 'λεπτό', 'minutes': 'λεπτά',
            'second': 'δευτ.', 'seconds': 'δευτ.'
        },
        'serbian': {
            'day': 'dan', 'days': 'dana',
            'hour': 'sat', 'hours': 'sati',
            'minute': 'minut', 'minutes': 'minuta',
            'second': 'sek.', 'seconds': 'sek.'
        }
    }

    if language not in labels:
        language = 'english'

    l = labels[language]

    def pluralize(value, singular, plural):
        return f"{value} {singular if value == 1 else plural}"

    time = int(time)

    if time < 60:
        return pluralize(time, l['second'], l['seconds'])
    elif time < 3600:
        minutes = time // 60
        seconds = time % 60
        return f"{pluralize(minutes, l['minute'], l['minutes'])} {pluralize(seconds, l['second'], l['seconds'])}"
    elif time < 86400:
        hours = time // 3600
        remaining = time % 3600
        minutes = remaining // 60
        seconds = remaining % 60
        return f"{pluralize(hours, l['hour'], l['hours'])} {pluralize(minutes, l['minute'], l['minutes'])} {pluralize(seconds, l['second'], l['seconds'])}"
    else:
        days = time // 86400
        remaining = time % 86400
        hours = remaining // 3600
        remaining %= 3600
        minutes = remaining // 60
        seconds = remaining % 60
        return f"{pluralize(days, l['day'], l['days'])} {pluralize(hours, l['hour'], l['hours'])} {pluralize(minutes, l['minute'], l['minutes'])} {pluralize(seconds, l['second'], l['seconds'])}"


def compute_histogram_bins(data:list=None, low:float=None, high:float=None) -> dict:
    """
    Computes the percentage distribution of numeric values in a dataset across three bins:
    'Low', 'Medium', and 'High', based on provided threshold values.

    The function first filters out non-numeric entries (e.g., strings, None, NaN), 
    then categorizes the valid values into three bins:
        - 'Low': values less than `low_threshold`
        - 'Medium': values between `low_threshold` and `high_threshold`
        - 'High': values greater than `high_threshold`

    Parameters:
        data (iterable): List or iterable of values (may include non-numeric entries).
        low (float): The lower bound separating 'Low' and 'Medium'.
        high (float): The upper bound separating 'Medium' and 'High'.

    Returns:
        dict: Dictionary with keys 'Low', 'Medium', and 'High', and values representing
              the percentage of total valid data points in each bin, rounded to one decimal.

    Example:
        >>> compute_histogram_bins([1, 5, 10, 20, None, 'abc'], 5, 15)
        {'Low': 25.0, 'Medium': 50.0, 'High': 25.0}
    """
    # Clean data: ignore non-numeric or invalid entries (NaN, None, etc.)
    cleaned_data = []
    for x in data:
        try:
            val = float(x)
            if not math.isnan(val):
                cleaned_data.append(val)
        except (TypeError, ValueError):
            continue  # Skip non-convertible entries

    # Define bin edges
    bins = [float('-inf'), low, high, float('inf')]  # Low, Medium, High
    labels = ['Low', 'Medium', 'High']

    # Use numpy histogram to count in bins
    counts, _ = np.histogram(cleaned_data, bins=bins)
    total = counts.sum()

    # Normalize to percentage
    if total == 0:
        return {label: 0.0 for label in labels}

    percentages = (counts / total) * 100

    # Round to one decimal (optional)
    result = dict(zip(labels, np.round(percentages, 1)))

    return result
