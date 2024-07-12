import requests
from urllib.parse import urlparse
from googlesearch import search
from bs4 import BeautifulSoup

# Videos
# ----------------------------------------------------------------
def search_videos(query, number_of_results=5):
    """
    Search for videos related to a query on YouTube.

    Args:
        query (str): The search query.
        number_of_results (int): Number of videos to retrieve. Default is 5.

    Returns:
        list: A list of dictionaries containing the title and URL of each video.
    """
    search_query = query + " site:youtube.com"
    search_results = search(search_query, stop=number_of_results)

    videos = []
    for result in search_results:
        if "youtube.com" in result:
            parsed_url = urlparse(result)
            if parsed_url.path == "/watch":
                # Fetch the title of the video
                title = get_video_title(result)
                # Sanity check
                if len(title) > 0:
                    videos.append({"Title": title, "URL": result})

    return videos


def get_video_title(video_url):
    """
    Retrieve the title of a YouTube video.

    Args:
        video_url (str): The URL of the YouTube video.

    Returns:
        str: The title of the video, or "Title not found" if not available.
    """
    response = requests.get(video_url)
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.find("meta", property="og:title")
    return title["content"] if title else "Title not found"


# Documents
# ----------------------------------------------------------------
def search_documents(query, number_of_results=5):
    """
    Search for documents (PDFs, DOC, DOCX) related to a query.

    Args:
        query (str): The search query.
        number_of_results (int): Number of documents to retrieve. Default is 5.

    Returns:
        list: A list of dictionaries containing the title and URL of each document.
    """    
    search_query = query + " filetype:pdf OR filetype:doc OR filetype:docx"
    search_results = search(search_query, stop=number_of_results)

    documents = []
    for result in search_results:
        if any(filetype in result for filetype in ['.pdf', '.doc', '.docx']):
            # Sanity check
            if len(result.split('/')[-1]) == 0: continue            
            documents.append({
                'Title': result.split('/')[-1],
                'URL': result
            })

    return documents


# Articles
# ----------------------------------------------------------------
def search_articles(query, number_of_results=5):
    """
    Search for articles or blog posts related to a query.

    Args:
        query (str): The search query.
        number_of_results (int): Number of articles to retrieve. Default is 5.

    Returns:
        list: A list of dictionaries containing the title, URL, and content of each article.
    """
    search_query = query + " site:.com OR site:.org OR site:.net"  # Restrict search to common article/blog domains
    search_results = search(search_query, stop=number_of_results)

    articles = []
    for result in search_results:
        if any(domain in result for domain in ['.com', '.org', '.net']):
            article = extract_article_info(result)
            if article:
                articles.append(article)

    return articles

def extract_article_info(url):
    """
    Extract relevant information from an article webpage.

    Args:
        url (str): The URL of the article webpage.

    Returns:
        dict: A dictionary containing the title, URL, and content of the article.
    """
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract relevant information from the webpage
        title = soup.title.text.strip()
        content = ' '.join([p.text for p in soup.find_all('p')])
        
        return {'Title': title, 'URL': url, 'content': content}
    except Exception as e:
        print(f"Error extracting data from {url}: {e}")
        return None


# Tutorials
# ----------------------------------------------------------------
def search_tutorials(query, number_of_results=5):
    """
    Search for tutorials or guides related to a query.

    Args:
        query (str): The search query.
        number_of_results (int): Number of tutorials to retrieve. Default is 5.

    Returns:
        list: A list of dictionaries containing the title and URL of each tutorial.
    """
    search_query = query + " tutorial OR guide"
    search_results = search(search_query, stop=number_of_results)

    tutorials = []
    for result in search_results:
        # Sanity check
        if len(result.split('/')[-1]) == 0: continue
        tutorials.append({
            'Title': result.split('/')[-1],
            'URL': result
        })

    return tutorials


# Research Papers
# ----------------------------------------------------------------
def search_google_scholar(query, number_of_results=5):
    """
    Search for research papers related to a query on Google Scholar.

    Args:
        query (str): The search query.
        number_of_results (int): Number of papers to retrieve. Default is 5.

    Returns:
        list: A list of dictionaries containing the title and link of each paper.
    """
    url = f"https://scholar.google.com/scholar?q={query}&num={number_of_results}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    results = []

    for result in soup.find_all('h3', class_='gs_rt'):
        title = result.get_text()
        # Sanity check
        if len(title) == 0: continue        
        # Handle titles such as "[HTML][HTML] Password"
        if "] " in title: title = title[title.find("] ")+2:]
        link = result.a['href']
        # Sanity check
        if len(title) < 5: continue
        results.append({'Title': title, 'URL': link})

    return results

