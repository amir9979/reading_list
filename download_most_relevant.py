import os
import re
import arxiv
import sqlite3
import tarfile
import pandas as pd


def parse_id(input_string):
    """
    Extracts the arXiv ID from a given input string, which can be either an arXiv ID or a URL.

    Args:
        input_string: The input string that is either an arXiv ID or a URL.

    Returns:
        The extracted arXiv ID if the input is valid, otherwise None.
    """
    # Pattern to match a direct arXiv ID
    id_pattern = re.compile(r"\d{4}\.\d{4,5}(v\d+)?$")
    if id_pattern.match(input_string):
        return input_string

    # Pattern to match an arXiv URL and extract the ID
    url_pattern = re.compile(r"https?://(?:www\.)?arxiv\.org/(abs|pdf)/(\d{4}\.\d{4,5})(v\d+)?(\.pdf)?$")
    url_match = url_pattern.match(input_string)
    if url_match:
        return url_match.group(2) + (url_match.group(3) if url_match.group(3) else "")


def download_article(article_id, directory, download_source=True):
    """
    Downloads the article with the given ID from arXiv and saves it to the specified directory.

    Args:
        article_id: The arXiv ID of the article to download.
        directory: The directory where the article will be saved.
        download_source: Whether to download the source files of the article.
    """
    # Proceed with the download
    directory = directory
    os.makedirs(directory, exist_ok=True)
    article = get_article(article_id)

    if not os.path.isfile(os.path.join(directory, article_id + '.pdf')):
        print(f'Starting download of article: "{article.title}" ({article_id})')
        # pdf_path = article.download_pdf(dirpath=directory, filename=article_id + '.pdf')
        # print(f"Download finished! Result saved at:\n{pdf_path}")
        if download_source:
            print(f'Starting download of article source files: "{article.title}" ({article_id})')
            tar_file_path = article.download_source(dirpath=directory, filename=article_id + '.tar')
            with tarfile.open(tar_file_path, 'r') as tar:
                # Extract all the contents into the specified directory
                tar.extractall(path=os.path.join(directory, article_id))


def get_article(article_id):
    return next(arxiv.Client().results(arxiv.Search(id_list=[article_id])))


def article_to_dict(article_id):
    """
    Converts an article's result object to a dictionary with semicolon-separated lists and basic types.

    Parameters:
    - article_id: The ID of the article to retrieve.
    - get_article_by_id: A function that takes the article_id and returns the result object.

    Returns:
    - dict: A dictionary representing the article with semicolon-separated lists.
    """
    # Get the result object using the provided function
    result = get_article(article_id)

    # Convert the result object into a dictionary with basic types
    article_dict = {
        'article_id': article_id,
        'entry_id': result.entry_id,
        'updated': result.updated.strftime('%Y-%m-%d %H:%M:%S') if result.updated else None,
        'published': result.published.strftime('%Y-%m-%d %H:%M:%S') if result.published else None,
        'title': result.title,
        'authors': ';'.join([author.name for author in result.authors]) if result.authors else None,  # Join list into semicolon-separated string
        'summary': result.summary,
        'comment': result.comment,
        'journal_ref': result.journal_ref,
        'doi': result.doi if result.doi else f'https://doi.org/10.48550/arXiv.{article_id}',
        'primary_category': result.primary_category,
        'categories': ';'.join(result.categories) if result.categories else None,
        # Join list into semicolon-separated string
        'links': ';'.join([link.href for link in result.links]) if result.links else None,
        # Join list of links into semicolon-separated string
        'pdf_url': result.pdf_url
    }

    return article_dict


def fetch_and_download_links(database_path='papers.db', download_path='downloads'):
    # Define the function to download source
    # Set up the SQLite database connection
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Query all links from the papers table
    cursor.execute("select title, link, count(*) c from papers where link like '%arxiv%' group by title, link order by c desc")
    rows = cursor.fetchall()
    articles_metadata = []
    # Process each link
    for ind, row in enumerate(rows):
        if ind == 100:
            break
        try:
            article_id = parse_id(row[1])
            # articles_metadata.append(article_to_dict(article_id))
            download_article(article_id, download_path)
        except:
            pass

    # Close the database connection
    # pd.DataFrame(articles_metadata).to_sql('arxiv_metadata', conn, if_exists='append', index=False)
    # conn.commit()
    conn.close()

# Usage
fetch_and_download_links()
