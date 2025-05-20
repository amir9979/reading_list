import json
import os

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
    relevant_info = []
    for paper in papers:
        clear_lines = [l.strip() for l in paper.splitlines() if l.strip()]
        title, fulllink = (clear_lines[0].split(' [')[1] if ' [' in clear_lines[0] else clear_lines[0].replace('[', '')).split('](')
        link = fulllink.split(link_end_sep)[0].split(link_start_sep)[1]
        relevant_info.append({
            'title': title,
            'link': link,
            'details': clear_lines[1],
            'abstract': ' '.join(clear_lines[2:]).strip()
        })

    return json.dumps(relevant_info)

# print(parse_email_content(os.environ['ISSUE_BODY']))
