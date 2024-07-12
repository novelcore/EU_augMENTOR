from bs4 import BeautifulSoup

def html2text(html_content: str = None):
    """
    Convert HTML content to plain text using BeautifulSoup.

    Args:
        html_content (str): The HTML content to be converted to text.

    Returns:
        str: The plain text extracted from the HTML content.
    """    
    return BeautifulSoup(html_content, "html.parser").get_text()