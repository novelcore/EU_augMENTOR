import numpy as np

def get_data(nInstances:int=None, number_questionnaire_features:int=None)->(np.ndarray, list):
    '''
        Create synthetic data for a learner in UPAT
        - 44 values as answers of a questionnaire (ordinal)
        - 5 values as grades, i.e. performance, creativity, critical thinking, collaboration, communication (ordinal)
        - 2 values as engagement metrics (ordinal)
        
        Paramaters
        ----------
        nInstances: (int)
            number of instances
        number_questionnaire_features: (int)
            number questionnaire features

        Return
        ------
            Tuple composed by an array with data and a list of feature names
    '''

    # Questionnaire data
    questionnaire_data = []
    for _ in range(number_questionnaire_features):
        questionnaire_data.append([np.random.randint(0,5) for _ in range(nInstances)])

    # Grades
    grades_data = []
    for _ in range(6):
        grades_data.append([np.random.randint(5,10) for _ in range(nInstances)])

    # Engagement metrics
    engagement_metrics_data = []
    for _ in range(2):
        engagement_metrics_data.append([np.random.randint(0,3) for _ in range(nInstances)])

    # Merge data
    data = np.array([questionnaire_data + grades_data + engagement_metrics_data])[0].T
    # Data features
    features = [f"Question ({i+1})" for i in range(number_questionnaire_features)] + ["Performance grade", "Quiz grade", "Creativity grade", "Collaboration grade", "Critical_thinking grade", "Communication grade"] + ["Engagement metric (1)", "Engagement metric (2)"]
 
    return data, features


# Transformation function for the 'presentation' field
def transform_presentation(presentation:str=None):
    """
    Transforms the 'presentation' field by extracting items if it follows a specific pattern.

    The function checks if the input string starts with 'r>>>>>' and ends with '<<<<<1'. If the pattern matches,
    it extracts the content between these delimiters, splits it by the delimiter '\r|', and converts it into a
    dictionary where each item is indexed by its position in the list. If the pattern does not match, the original
    input is returned unchanged.

    Parameters:
    -----------
    presentation : str
        A string that potentially contains a specially formatted list of items.

    Returns:
    --------
    dict or str
        - If the 'presentation' string matches the pattern, a dictionary is returned where keys are indices (starting from 0) 
          and values are the extracted items.
        - If the pattern does not match, the original 'presentation' string is returned as-is.

    Example:
    --------
    >>> transform_presentation('r>>>>>item1\r|item2\r|item3<<<<<1')
    {0: 'item1', 1: 'item2', 2: 'item3'}

    >>> transform_presentation('normal_string')
    'normal_string'
    """    
    if presentation.startswith('r>>>>>') and presentation.endswith('<<<<<1'):
        if "\r|" in presentation[6:-6]:
            items = presentation[6:-6].split('\r|')
        elif "\n|" in presentation[6:-6]:
            items = presentation[6:-6].split('\n|')
        else:
            raise Exception("Cannot process information for extracting question's available responess")
        return {i: item for i, item in enumerate(items)}