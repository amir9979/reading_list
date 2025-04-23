from utils import *
from urllib.parse import urlparse


def is_valid_url(url):
    """Validate whether a string is a valid URL using urllib."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def read_bbl_files(directory, input_key):
    """Main function to read .bbl files from a directory and extract citation data."""
    bibitems = []
    for name, content in read_file_type(directory, '.bbl'):
        bibitems.extend(process_bib_content(content, input_key))
    return bibitems


def process_bib_content(content, input_key):
    """Process the content of a .bbl file and extract citations."""
    bibitems = []
    clear_content = clean_bbl_content(content)
    for bibitem in parse_bibitems(clear_content):
        citation_data = extract_citation_data(bibitem, input_key)
        if citation_data:
            bibitems.append(citation_data)
    return bibitems


def clean_bbl_content(content):
    """Clean the .bbl content by removing unnecessary parts."""
    return content.replace(r'\end{thebibliography}', '').strip()


def parse_bibitems(content):
    """Parse the cleaned .bbl content into individual bibitems."""
    return [[n.replace('\n', ' ') for n in b.strip().split(r'\newblock')] for b in content.split('\\bibitem')[1:]]


def extract_citation_data(bibitem, input_key):
    """Extract citation data from a parsed bibitem."""
    try:
        citation_key = get_citation_key(bibitem[0])
        title, link = get_title_and_link(bibitem)

        return {
            'input_key': input_key,
            'citation_key': citation_key.strip(),
            'header': bibitem[0].strip(),
            'name': bibitem[1].strip(),
            'title': title,
            'link': link,
            'full_bib': '\n'.join(bibitem)
        }
    except IndexError:
        return None  # Handle cases where the bibitem structure is unexpected


def get_citation_key(header):
    """Extract the citation key from the bibitem header."""
    return header.split(']{')[1].split('}')[0]


def get_link(item):
    prefix = ''
    for p in ['\\url', '\\href', '\\doi']:
        if p in item:
            prefix = p + '{'
    if prefix == '':
        return None
    link = item.split(prefix)[1].split('}')[0]
    return link


def get_title_and_link(bibitem):
    """Extract the title and link from a bibitem."""
    title = bibitem[1].strip()
    link = ''
    if len(bibitem) == 2:
        link = get_link(bibitem[1])
    elif len(bibitem) == 3:
        if '} {' in title:
            l, t = bibitem[1].split('} {', 1)
            link = get_link(l + '}')
            title = t.replace('}', '').strip()
    elif len(bibitem) == 4:
        link = get_link(bibitem[3])
    elif len(bibitem) == 5:
        link = get_link(bibitem[3])
    elif len(bibitem) == 6:
        link = get_link(bibitem[4])
    return title, link
