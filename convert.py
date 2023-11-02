import re
import sys
import os
import subprocess
from enum import Enum


class Section(Enum):
    QUESTION = 1
    SOLUTION = 2
    PART = 3


markdown = sys.argv[1]
if not os.path.isabs(markdown):
    markdown = os.path.join(os.getcwd(), markdown)

file = open(markdown, "r")
lines = file.readlines() + ["\n", "##"]
n_question = 0
is_question = False
prev_level = prev_section = None

preamble = []

i = 0
if lines[i] == "---\n":
    # parse yaml
    i += 1
    while i < len(lines) and (line := lines[i]) != "---\n":
        tokens = line.split()
        key = tokens[0][:-1].lower()
        value = " ".join(tokens[1:])
        preamble.append("\\newcommand{\\" + key + "}{" + value + "}\n")
        i += 1
    i += 1

preamble += [
    "\\documentclass[12pt]{exam}\n",
    "\\input{/Users/alex/git/latex/preamble.tex}\n",
    "\\usepackage{xcolor}\n",
    "\\definecolor{blush}{rgb}{0.87, 0.36, 0.51}\n",
    "\\definecolor{brightmaroon}{rgb}{0.76, 0.13, 0.28}\n",
    "\\usepackage[colorlinks=true, allcolors=brightmaroon, backref=page]{hyperref}\n",
    "\\begin{document}\n\n",
    "\\begin{questions}\n"
]


def end_section(end_tag=None):
    if end_tag is None:
        if prev_section == Section.QUESTION:
            end_tag = "\\end{question}\n\n"
        elif prev_section == Section.SOLUTION:
            end_tag = "\\end{solution}\n\n"
        elif prev_section == Section.PART:
            end_tag = "\n\n"
        else:
            return

    if new_lines[-1] == "\n":
        new_lines[-1] = end_tag
    else:
        new_lines.append(end_tag)


def get_cite_key(s):
    match = re.search(r"\[\[@(.*?)\]\]", s)
    return "\\cite{" + match.group(1) + "}" if match else None


has_refs = False
new_lines = []
while i < len(lines):
    line = lines[i]
    tokens = line.split() if line else []
    if line.startswith("#"):
        # starting new section
        # close previous section (if any)
        end_section()

        level = len(tokens[0])
        if level == 2:
            if prev_level == 4:
                end_section("\\end{parts}\n\n")
            if i < len(lines) - 1:
                new_lines += ["\\newpage", "\n", "\\begin{question}", "\n"]
                prev_section = Section.QUESTION
                i += 1
        elif tokens[1] == "Solution":
            new_lines += ["\\begin{solution}", "\n"]
            prev_section = Section.SOLUTION
            i += 1
        else:
            if prev_section == Section.QUESTION:
                new_lines += ["\\begin{parts}", "\n"]
            new_lines += ["\\part "]
            prev_section = Section.PART
            i += 1
        prev_level = level
    else:
        # new_lines.append(line)
        for j, token in enumerate(tokens):
            cite_key = get_cite_key(token)
            if cite_key:
                has_refs = True
                tokens[j] = cite_key
        line = " ".join(tokens)
        new_lines.append(line + "\n")
    i += 1

postamble = ["\\end{questions}\n", "\\end{document}"]
if has_refs:
    postamble = [
        "\\newpage\n",
        "\\bibliographystyle{plain}\n",
        "\\bibliography{/Users/alex/git/latex/ref}\n",
    ] + postamble

dir_name = os.path.dirname(markdown)
# filename = os.path.basename(markdown)[:-3]
# tex = os.path.join(dir_name, filename + "output.tex")
tex = os.path.join(dir_name, "output.tex")
file = open(tex, "w")
new_lines = preamble + new_lines + postamble
file.writelines(new_lines)
file.close()

subprocess.run(["tectonic", tex, "--outfmt", "pdf"])
