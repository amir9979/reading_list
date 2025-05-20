import json
import os
import arxiv

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

def get_article(link):
    article_id = next(arxiv.Client().results(arxiv.Search(id_list=[parse_id(link)])))
    return article_to_dict(article_id)

def parse_email_content(email_content):
    start = '\r\n### \r\n\r\n### \r\n\r\n'
    sep = "---|---|---|---"
    save_sep = "[![Save]"
    initial_sep = '###'
    link_start_sep = 'scholar_url?url='
    link_end_sep = '&hl=en'

    if start not in email_content:
        start = start.replace('\r', '')
    email_content = email_content[email_content.find('###'):].split(sep)
    papers = [x.split(save_sep)[0] for x in email_content][:-1]
    papers = [p.split(initial_sep)[1] for p in papers]
    papers = [p for p in papers if p.strip()]
    relevant_info = []
    arxiv = ''
    for i, paper in enumerate(papers):
        clear_lines = [l.replace('###', '').strip() for l in paper.splitlines() if l.replace('###', '').strip()]
        title, fulllink = (clear_lines[0].split(' [')[1] if ' [' in clear_lines[0] else clear_lines[0].replace('[', '')).split('](')
        link = fulllink.split(link_end_sep)[0].split(link_start_sep)[1]
        ans = {
            'title': title,
            'link': link,
            'details': clear_lines[1],
            'abstract': ' '.join(clear_lines[2:]).strip()
        }
        if 'arxiv' in link.lower():
            arxiv = get_article(link)
            ans.update(arxiv)
        relevant_info.append(ans)

    return json.dumps(relevant_info)

print(parse_email_content(os.environ['ISSUE_BODY']))
