import re
from bs4 import BeautifulSoup
# def html2text(html_content: str = None):
#     """
#     Convert HTML content to plain text using BeautifulSoup.

#     Args:
#         html_content (str): The HTML content to be converted to text.

#     Returns:
#         str: The plain text extracted from the HTML content.
#     """    
#     return text_preprocess(BeautifulSoup(html_content, "html.parser").get_text())


def html2text(html_string):
    """
    Convert HTML to formatted text while preserving structure.
    
    Args:
        html_string (str): HTML string to convert
        
    Returns:
        str: Formatted plain text
    """
    # Parse the HTML
    soup = BeautifulSoup(html_string, 'html.parser')
    
    # Handle different HTML elements
    for element in soup.find_all():
        if element.name == 'p':
            # Add line breaks before and after paragraphs
            element.insert_before('\n')
            element.insert_after('\n')
        elif element.name in ['strong', 'b']:
            # Keep bold formatting with **text**
            element.insert_before('**')
            element.insert_after('**')
        elif element.name in ['em', 'i']:
            # Keep italic formatting with *text*
            element.insert_before('*')
            element.insert_after('*')
        elif element.name == 'ul':
            # Add line break before lists
            element.insert_before('\n')
        elif element.name == 'li':
            # Convert list items to bullet points
            element.insert_before('• ')
            element.insert_after('\n')
    
    # Extract text and clean up
    text = soup.get_text()
    
    # Clean up whitespace and line breaks
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    # Replace multiple line breaks with maximum of 2
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Remove empty lines at start and end
    text = text.strip()
    
    return text.replace(" **", "** ").replace('"', "'")