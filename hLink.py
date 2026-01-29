import pathlib
import argparse
import lib.hugo_uris
import lib.hugo_utils

parser = argparse.ArgumentParser(
    prog='hLink.py',
    description='generates a markdown link from a path or URL',
)
parser.add_argument(
    '-u',
    '--uri',
    required=True,
    help='the file path of page URL'
)
args = parser.parse_args()

if args.uri.startswith('http'):
    file_path = lib.hugo_utils.url2path(file_url=args.uri, base_dir=lib.hugo_uris.BASE_DIR)
    hugo_file = pathlib.Path(file_path)
else:
    hugo_file = pathlib.Path(args.uri)
assert hugo_file.exists(), f'File {hugo_file} not found'
file_contents = hugo_file.read_text(encoding='utf-8')
page_title = file_contents.split('title: "').pop().split('"')[0]
page_link_url = hugo_file.relative_to(lib.hugo_uris.BASE_DIR)
page_link_url = page_link_url.as_posix().split('_index.md')[0].split('.md')[0]
print(f'[{page_title}](/{page_link_url})')


'''
BASE_URL_DEV = 'https://docs.dev.pkihub.com'
BASE_URL_LOCAL = 'http://localhost:1313'
BASE_URL_DEMO = 'https://docdemo.entrust.com:9993'
PRODUCTION_URL_DEMO = 'https://docs.pkiaas.entrust.com'
'''