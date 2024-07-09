# import time
# import json 
import numpy as np

seed = 42
np.random.seed(seed)

# # List of metrics
# available_metrics = ["Basic skills", "Quiz", "Creativity", "Collaboration", "Critical thinking", "Communication"]

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


# def performance_evaluation(grades:list=None)->float:
#     '''
#         Given a list of grades of a specific metric, this function implements the trent using linear regression

#         Parameters
#         ----------
#         grades: (list)
#             list of grades

#         Returns
#         -------
#         trent (float)
#     '''
#     # Extract x and y values from the points
#     x_values = np.array([i for i in range(len(grades))])
#     y_values = np.array(grades)


#     # Calculate the necessary statistics
#     n = len(x_values)
#     sum_x = np.sum(x_values)
#     sum_y = np.sum(y_values)
#     sum_x_squared = np.sum(x_values**2)
#     sum_xy = np.sum(x_values * y_values)

#     # Calculate the coefficient(s)
#     slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x_squared - sum_x**2)
#     # intercept = (sum_y - slope * sum_x) / n

#     return slope


# def load_json_to_dict(input_path:str=None, file_encoding:str='utf-8') -> dict:
#     """
#         Load a json file to a dictionary form.

#         Parameters
#         ----------
#         input_path: (str)
#             input path
#         file_encoding: (str)
#             file encoding (utf-8 is default)

#         Return
#         ------
#         JSON file contents 
#     """
#     json_dict = {}
#     with open(input_path, 'r', encoding = file_encoding) as json_file:
#         json_dict = json.load(json_file)
#     return json_dict



# def save_dict_to_json(dictionary:dict=None, output_path:str=None, file_encoding:str='utf-8', separators=(',', ':')):
#     """
#         Function that tries to save a dict to a human readable json file.
#         If the write attempt fails, then it retries for a short time period.
#         Finally an error is logged.

#         Parameters
#         ----------
#         dictionary: (dict)
#             dictionary to be saved
#         output_path: (str)
#             output path
#         file encoding: (str)
#             file_encoding
#         separators: tuple
#             separators for saving file in JSON
#     """
#     for _ in range(10):
#         try:
#             with open(output_path, 'w', encoding = file_encoding) as file:
#                 json.dump(
#                     dictionary, file, ensure_ascii = False, separators = separators
#                 )
#         except:
#             time.sleep(0.1)
#             continue
#         break
#     else:
#         print('[ERROR] Could not save the json file')