import os
import tarfile
import argparse
import time
import pandas as pd
from pylatexenc.latex2text import LatexNodes2Text
from pylatexenc.latexwalker import *
import shutil
import ftfy
from tex2py import tex2py
from glob import glob
from utils import read_file_type
from parse_bbls import *

def extract_tarfile(tar_file, path='.'):
    """
    Extracts the contents of a .tar.gz file to a specified directory.
    
    Parameters:
    tar_file (str): The path to the .tar.gz file.
    path (str): The directory to extract the contents to.
    
    Returns:
    None
    """
    with tarfile.open(tar_file, 'r:gz') as tar:
        tar.extractall(path=path)

def read_tex_files(directory):
    return read_file_type(directory, '.tex')


def read_bbl_files2(directory, input_key):
    bibitems = []
    for name, content in read_file_type(directory, '.bbl'):
        clear_content = content.replace(r'\end{thebibliography}', '').strip()
        for bibitem in [b.strip().split('\n') for b in clear_content.split('\\bibitem')[1:]]:
            citation_key = bibitem[0].split('}]{')[1].replace('}', '')
            if len(bibitem) == 3:
                both = bibitem[2].replace('\\newblock ', '').replace('\\href', '').split('} {')
                if len(both) > 1:
                    link = both[0].replace('{', '').replace('\\newblock ', '').replace('emph{', '').replace('\\href', '').strip()
                    title = both[1].replace('}', '').strip()
                else:
                    link = ''
                    title = both[0].strip()
            elif len(bibitem) == 4:
                title = 2
                link = 3
                if 'href' in bibitem[2]:
                    link = 2
                    title = 3
                title = bibitem[title].replace('\\newblock ', '').strip()
                link = bibitem[link].replace('\\newblock ', '').replace('emph{', '').replace('\\href', '').strip()
            bibitems.append({
                            'input_key': input_key,
                            'citation_key': citation_key.strip(),
                            'header': bibitem[0].strip(),
                            'name': bibitem[1].strip(),
                            'title': title,
                            'link': link,
                            'full_bib': '\n'.join(bibitem)
                            })
    return bibitems


def find_main_tex_file(tex_files):
    """
    Finds the main .tex file, which contains the \documentclass command.
    
    Parameters:
    tex_files (list of tuples): A list of tuples, each containing the file name and its content.
    
    Returns:
    tuple: The main .tex file and its content.
    """
    for file, content in tex_files:
        if re.search(r'\\documentclass', content):
            return file, content
    return tex_files[0]  # Return the first file if no documentclass is found

def clean_tex_content(tex_content, debug=False):
    """
    Cleans the TeX content by removing tables, figures, and math blocks.
    
    Parameters:
    tex_content (str): The TeX content to be cleaned.
    debug (bool): If True, prints debug information.
    
    Returns:
    str: The cleaned TeX content.
    """
    def debug_print(message):
        if debug:
            print(message)

    def remove_pattern(pattern, description):
        matches = re.findall(pattern, tex_content, flags=re.DOTALL)
        if matches:
            debug_print(f"Found {len(matches)} {description} blocks.")
            for match in matches:
                debug_print(f"Removing {description} block: {match[:100]}...")  # Print the first 100 characters of each match
        return re.sub(pattern, '', tex_content, flags=re.DOTALL)

    tex_content = remove_pattern(r'\\begin\{table\}.*?\\end\{table\}', 'table')
    tex_content = remove_pattern(r'\\begin\{tabular\}.*?\\end\{tabular\}', 'tabular')
    tex_content = remove_pattern(r'\\begin\{figure\}.*?\\end\{figure\}', 'figure')  # Added for figures
    tex_content = remove_pattern(r'\$\$.*?\$\$', 'display math')
    tex_content = remove_pattern(r'\$.*?\$', 'inline math')

    return tex_content

def fix_text_issues(text):
    """
    Fixes text issues such as ligatures and other character problems.
    
    Parameters:
    text (str): The text to be fixed.
    
    Returns:
    str: The fixed text.
    """
    fixed_text = ftfy.fix_text(text)
    return fixed_text

def tex_to_text(tex_content):
    """
    Converts TeX content to plain text using pylatexenc.
    
    Parameters:
    tex_content (str): The TeX content to be converted.
    
    Returns:
    str: The converted plain text.
    """
    converter = LatexNodes2Text()
    text = converter.latex_to_text(tex_content)
    return text

def clean_text(text):
    """
    Cleans the plain text by removing LaTeX commands and unwanted tags, and fixing text issues.
    
    Parameters:
    text (str): The text to be cleaned.
    debug (bool): If True, prints debug information.
    
    Returns:
    str: The cleaned text.
    """
    # Fix text issues
    text = fix_text_issues(text)

    # Preserve paragraphs by keeping double newlines
    text = re.sub(r'(\n\s*\n)', '\n\n', text)
    
    # Remove common LaTeX commands and unwanted tags
    text = re.sub(r'\\cite\{.*?\}', '<cit.>', text)
    text = re.sub(r'\\ref\{.*?\}', '<ref>', text)
    text = re.sub(r'\\label\{.*?\}', '', text)
    text = re.sub(r'\\begin\{.*?\}', '', text)
    text = re.sub(r'\\end\{.*?\}', '', text)
    text = re.sub(r'\\[a-zA-Z]+\*?\{.*?\}', '', text)
    
    # Remove specific unwanted tags
    text = re.sub(r'<cit.>', '', text)
    text = re.sub(r'<ref>', '', text)
    
    # Remove angle brackets around URLs
    text = re.sub(r'<(https?://[^>]+)>', r'\1', text)
    
    # Restore single newlines within blocks
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    
    # Ensure there is a newline after each block
    text = re.sub(r'(\n\n)+', '\n\n', text)
    
    return text.strip()


def toc_to_str(tex):
    accumulated_strings = []

    # Iterate over sections in toc
    try:
        toc = tex2py(tex)
        for section in toc.sections:
            try:
                # Iterate over subsections in each section
                for subsection in section.subsections:
                    try:
                        # Iterate over descendants of each subsection
                        for descendant in subsection.descendants:
                            try:
                                # Check if the descendant is of type string
                                if isinstance(descendant, str):
                                    # Accumulate the string descendant
                                    accumulated_strings.append(descendant)
                            except Exception as e:
                                print(f"Error processing descendant: {e}")
                    except Exception as e:
                        print(f"Error processing subsection: {e}")
            except Exception as e:
                print(f"Error processing section: {e}")
    except Exception as e:
        print(f"Error processing toc: {e}")

    # Join all accumulated strings into one single string
    return ''.join(accumulated_strings)


def find_citations(nodelist, input_key):
    references = []

    for ind, node in enumerate(nodelist):
        # Check if the node is of type 'latexmacroNode' and has 'macroname' attribute set to 'cite'
        if 'latexmacroNode'.lower() in str(type(node)).lower():
            if hasattr(node, 'macroname'):
                if getattr(node, 'macroname', None) == 'cite':
                    relevant_text = ' '.join([x.chars.lower().strip() for x in nodelist[ind-6: ind -1] if hasattr(x,'chars')] + [x.chars.lower().strip() for x in nodelist[ind + 1: ind + 6] if hasattr(x,'chars')]).strip()
                    # backward augment
                    # for text_ind in range(ind - 2, max(ind - 6, -len(nodelist)), -1):
                    #     text_node = nodelist[text_ind]
                    #     # augment text until first dot or newline
                    #     if 'LatexCharsNode'.lower() in str(type(text_node)).lower():
                    #         chars = text_node.chars.strip()
                    #         if '\n' in chars:
                    #             relevant_text = chars[chars.rfind('\n') + 1:] + relevant_text
                    #             break
                    # # forward augment
                    # for text_ind in range(ind + 1, min(ind + 6, len(nodelist) - 1)):
                    #     text_node = nodelist[text_ind]
                    #     # augment text until first dot or newline
                    #     if 'LatexCharsNode'.lower() in str(type(text_node)).lower():
                    #         chars = text_node.chars.strip()
                    #         if '\n' in chars:
                    #             relevant_text += chars[:chars.find('\n')]
                    #             break
                    try:
                        for citation in node.nodeargs[3].nodelist[0].chars.split(','):
                            references.append({'relevant_text': relevant_text.strip(), 'citation_key': citation.strip(), 'input_key': input_key})
                    except:
                        pass

        # Check if the node has a 'nodelist' attribute
        if hasattr(node, 'nodelist'):
            # Recursively search in the nested nodelist
            references.extend(find_citations(node.nodelist, input_key))

    return references


# Example usage:
# Assuming `nodelist` is your list of LaTeX nodes
# result = find_cite_macros(nodelist)
# print(result)

def extract_text_and_stats(input_folder, output_folder, output_file, output_bbl_file, output_citations, force, debug):
    """
    Extracts text from TeX files in .tar.gz archives, cleans the text, and generates statistics.
    
    Parameters:
    input_folder (str): The folder containing the .tar.gz files.
    output_folder (str): The folder to save the extracted text files.
    output_file (str): The CSV file to save the statistics.
    force (bool): If True, forces reprocessing of already processed files.
    debug (bool): If True, prints debug information.
    
    Returns:
    None
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    data = []
    bbls = []
    citations = []
    for tar_file in glob('./downloads/*.tar'):
        output_file_name = os.path.basename(tar_file).replace('.tar', '')
        extract_path = os.path.join(input_folder, output_file_name)  # Remove .tar.gz extension
        output_txt_file = os.path.join(output_folder, f"{output_file_name}.txt")

        if os.path.exists(output_txt_file) and not force:
            print(f"Skipping already processed file: {tar_file}")
            continue

        if not os.path.exists(extract_path):
            os.makedirs(extract_path)

        start_time = time.time()
        try:
            extract_tarfile(tar_file, extract_path)
        except:
            continue

        tex_files = read_tex_files(extract_path)
        bbls.extend(read_bbl_files(extract_path, output_file_name))
        main_tex_file, main_tex_content = find_main_tex_file(tex_files)

        citations.extend(find_citations(LatexWalker(main_tex_content).get_latex_nodes(pos=0)[0], output_file_name))
        clean_tex = clean_tex_content(main_tex_content, debug)
        text = toc_to_str(clean_tex)
        clean_text_content = clean_text(text)

        num_words = len(clean_text_content.split())
        num_paragraphs = clean_text_content.count('\n\n') + 1
        num_chars = len(clean_text_content)
        extraction_time = time.time() - start_time

        with open(output_txt_file, 'w', encoding='utf-8') as f:
            f.write(clean_text_content)

        data.append({
            'file': tar_file,
            'num_words': num_words,
            'num_paragraphs': num_paragraphs,
            'num_chars': num_chars,
            'extraction_time': extraction_time
        })

        # Remove extracted files
        shutil.rmtree(extract_path)
    
    pd.DataFrame(data).to_csv(output_file, index=False)
    pd.DataFrame(bbls).to_csv(output_bbl_file, index=False)
    pd.DataFrame(citations).to_csv(output_citations, index=False)
    print(f"Extraction complete. Statistics saved to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract text from arXiv TeX files and generate statistics.")
    parser.add_argument('input_folder', type=str, help='Folder containing the tar.gz files')
    parser.add_argument('output_folder', type=str, help='Folder to save the extracted text files')
    parser.add_argument('output_file', type=str, help='CSV file to save the statistics')
    parser.add_argument('output_bbl_file', type=str, help='CSV file to save the statistics')
    parser.add_argument('output_citations_file', type=str, help='CSV file to save the statistics')
    parser.add_argument('-f', '--force', action='store_true', help='Force reprocessing of already processed files')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()
    
    extract_text_and_stats(args.input_folder, args.output_folder, args.output_file, args.output_bbl_file, args.output_citations_file, args.force, args.debug)
