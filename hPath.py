import pathlib
import argparse
import lib.hugo_uris
import lib.hugo_utils

parser = argparse.ArgumentParser(
    prog='hPath.py',
    description='generates a URL from a markdown file path and vice-versa',
)
parser.add_argument(
    '-u',
    '--uri',
    required=True,
    help='generate a page URL for a file with the "URI" path, or a file path for the "URI" URL '
)
parser.add_argument(
    '-o',
    '--open',
    action='store_true',
    help='open markdown files Microsoft Studio Code and URLs in default browser'
)
parser.add_argument(
    '-b',
    '--base_url',
    default=lib.hugo_uris.BASE_URL_LOCAL,
    help=f'use BASE_URL to generate the URLs, defaults to "{lib.hugo_uris.BASE_URL_LOCAL}"'
)
args = parser.parse_args()
hugo_file = pathlib.Path(args.uri)
if args.uri.startswith('http'):
    file_path = lib.hugo_utils.url2path(file_url=args.uri, base_dir=lib.hugo_uris.BASE_DIR)
    print(file_path)
    if args.open:
        lib.hugo_utils.open_in_editor(file_path)
else:
    file_url = lib.hugo_utils.path2url(
        file_path=pathlib.Path(args.uri),
        base_url=args.base_url,
        base_dir=lib.hugo_uris.BASE_DIR
    )
    print(file_url)
    if args.open:
        lib.hugo_utils.open_in_browser(file_path=file_url)
