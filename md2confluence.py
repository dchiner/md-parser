import re
import pathlib
import argparse

args_parser = argparse.ArgumentParser(
        prog='md2confluence.py',
        description='Adapts markdown files to be compatible with Confluence Cloud.',
    )
args_parser.add_argument(
    '-p',
    '--path',
    required=True,
    help='The path of a markdown file',
)
args = args_parser.parse_args()
markdown_file_path = pathlib.Path(args.path)
assert markdown_file_path, f'The provided file path does not exist: {args.path}'
assert markdown_file_path.suffix == '.md', 'The provided file must be a markdown file with the .md extension'
markdown_content = markdown_file_path.read_text()
replacements_dict = {
    '```text': '{code:language=text}',
    '```': '{code}',
    '######': 'h6. ',
    '#####': 'h5. ',
    '####': 'h4. ',
    '###': 'h3. ',
    '##': 'h2. ',
    '#': 'h1. ',
    '**': '*',
}
for each_key, each_value in replacements_dict.items():
    markdown_content = markdown_content.replace(each_key, each_value)
for each_match in re.findall(r'\[([^\]]+)\]\(([^)]+)\)', markdown_content):
    markdown_content = markdown_content.replace(f'[{each_match[0]}]({each_match[1]})', f'[{each_match[0]}|{each_match[1]}]')    
for each_match in re.findall(r'`(.+?)`', markdown_content):
    markdown_content = markdown_content.replace(f'`{each_match}`', '{{'+each_match+'}}')
markdown_file_content_as_list = markdown_content.splitlines()
confluence_content = ''
for i in range(0, len(markdown_file_content_as_list)-1):
  if '| -' in markdown_file_content_as_list[i+1]:
    markdown_file_content_as_list[i] = markdown_file_content_as_list[i].replace('|', '||')
  if '| -' in markdown_file_content_as_list[i]:
    continue    
  confluence_content += markdown_file_content_as_list[i] + '\n'
confluence_file_path = markdown_file_path.with_suffix('.confluence.md')
print('Saving the adapted markdown file to: ', confluence_file_path)
confluence_file_path.write_text(confluence_content)