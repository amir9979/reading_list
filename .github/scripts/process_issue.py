import json
from pathlib import Path
import os

def parse_email_content(email_content):
    start = " __\n         \n         ### \n         \n         ###"
    sep = "---|---|---|---"
    save_sep = "[![Save]"
    initial_sep = '### '
    link_start_sep = 'https://scholar.google.co.uk/scholar_url?url='
    link_end_sep = '&hl=en'

    papers = [x.split(save_sep)[0] for x in email_content.split(start)[1].split(sep)][:-1]
    papers = [p.split(initial_sep)[1] for p in papers]
    relevant_info = []
    for paper in papers:
        clear_lines = [l.strip() for l in paper.splitlines() if l.strip()]
        title, fulllink = (clear_lines[0].split(' [')[1] if ' [' in clear_lines[0] else clear_lines[0].replace('[', '')).split('](')
        link = fulllink.split(link_end_sep)[0].split(link_start_sep)[1]
        details = clear_lines[1]
        authors = [a.strip() for a in details.split('-')[0].split(',')]
        venue, year = details.split('-')[1].split(',')
        abstract = ' '.join(clear_lines[2:])
        relevant_info.append({
            'title': title,
            'link': link,
            'authors': authors,
            'venue': venue.strip(),
            'year': year.strip(),
            'abstract': abstract.strip()
        })

    return relevant_info

print(parse_email_content(os.environ['ISSUE_BODY']))
