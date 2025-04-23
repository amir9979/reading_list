from tex2py import tex2py
from pylatexenc.latexwalker import LatexWalker, LatexEnvironmentNode, LatexMacroNode, LatexCharsNode, LatexGroupNode
from pylatexenc.latex2text import LatexNodes2Text


# Function to process LaTeX content
def extract_text_from_latex(latex_code):
    # Create a LatexWalker object to parse the LaTeX code
    walker = LatexWalker(latex_code)
    nodelist, pos, length = walker.get_latex_nodes()

    extracted_text = []

    # Recursive function to process each node
    def process_node(node):
        if isinstance(node, LatexMacroNode):
            # Extract titles, sections, etc.
            if node.macroname in ('title', 'section', 'subsection', 'subsubsection', 'caption'):
                extracted_text.append(LatexNodes2Text().nodelist_to_text(node.nodeargd.argnlist[0].nodelist))
            elif node.macroname in ('cite'):
                extracted_text.append(
                    f"Citation: {LatexNodes2Text().nodelist_to_text(node.nodeargd.argnlist[0].nodelist)}")
            elif node.macroname in ('footnote'):
                extracted_text.append(
                    f"Footnote: {LatexNodes2Text().nodelist_to_text(node.nodeargd.argnlist[0].nodelist)}")

        elif isinstance(node, LatexEnvironmentNode):
            if node.environmentname == 'abstract':
                extracted_text.append("Abstract:")
                extracted_text.append(LatexNodes2Text().nodelist_to_text(node.nodelist))
            elif node.environmentname in ('itemize', 'enumerate'):
                for item in node.nodelist:
                    process_node(item)

        elif isinstance(node, LatexCharsNode):
            # Extract plain text
            extracted_text.append(node.chars)

        elif isinstance(node, LatexGroupNode):
            for n in node.nodelist:
                process_node(n)

        # Continue processing for other node types if needed

    # Process each node
    for node in nodelist:
        process_node(node)

    # Join the extracted text
    return "\n".join(extracted_text)


def toc_to_str(toc, file_path):
    accumulated_strings = []

    # Iterate over sections in toc
    try:
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
    joined_string = ' '.join(accumulated_strings)

    # Save the joined string to the specified file
    try:
        with open(file_path, 'w') as file:
            file.write(joined_string)
        print(f"Successfully saved to {file_path}")
    except Exception as e:
        print(f"Error saving to file: {e}")


with open(r'downloads\2406.13233\main.tex') as f:
    data = f.read()
    toc = tex2py(data)
    extracted_text = extract_text_from_latex(data)
print(toc_to_str(toc))
# print(extracted_text)