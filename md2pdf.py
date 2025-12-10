
import re
from markdown_pdf import MarkdownPdf, Section

with open(r"C:\Users\chinerd\git\src\entrust.com\pking\pkihub-docs\merged.md", encoding="utf8") as f:
    md = f.read()

# Convert text -> "text" (remove the broken link)
md = re.sub(r"\[([^\]]+)\]\(#[^)]+\)", r"\1", md)

pdf = MarkdownPdf()
pdf.add_section(Section(md, toc=False))
pdf.save(r"c:\users\chinerd\Downloads\document.pdf")
