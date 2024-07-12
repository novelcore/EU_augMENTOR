import numpy as np
import textwrap

seed = 42
np.random.seed(seed)

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


def show(response:str)->None:
    print()
    print(color.BLUE + "\nResponse: " + color.END, end = "")
    for text in response.split("\n"):
        print("{}".format(textwrap.fill(text, width=170)))