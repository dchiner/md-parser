import pathlib
import argparse

import lib.hugo_uris
import lib.hugo_utils

parser = argparse.ArgumentParser(
    prog='hWeights.py',
    description='lists the weights in an Hugo folder',
)
parser.add_argument(
    '-p',
    '--path',
    required=False,
    default=lib.hugo_uris.BASE_DIR,
    help=f'check the weights in the PATH folder. Defaults to {lib.hugo_uris.BASE_DIR}'
)
parser.add_argument(
    '-o',
    '--open',
    action='store_true',
    help='open the output in the default browser'
)
args = parser.parse_args()
dir_path = pathlib.Path(args.path)
assert dir_path.exists(), f'Path "{args.path}" not found'
assert dir_path.is_dir(), f'"{args.path}" is not a dir'
page_list = list()
weight_list = list()
for each_path in dir_path.iterdir():
    if each_path == dir_path / '_index.md':
        continue
    if each_path == dir_path / 'img':
        continue
    if each_path.is_file():
        each_file_contents = each_path.read_text(encoding='utf8')
    else:
        each_file_contents = each_path.joinpath('_index.md').read_text(encoding='utf8')
    each_file_title = lib.hugo_utils.get_page_title(file_contents=each_file_contents)
    each_file_name = each_path.name
    each_file_weight = lib.hugo_utils.get_page_weight(file_contents=each_file_contents)
    weight_list.append(each_file_weight)
    page_list.append((each_file_weight, each_file_name, each_file_title))

res_list = list()
res_list.append('Weight'.ljust(7) + 'Folder'.ljust(10) + 'Title')
res_list.append('-' * 80)
for each_item in sorted(page_list, key=lambda x: x[0]):
    res_list.append(str(each_item[0]).ljust(7) + each_item[1].ljust(10) + each_item[2])
res_list.append('\nRepeated weights:')
[
    res_list.append(each_file_weight) for each_file_weight in weight_list
    if weight_list.count(each_file_weight) > 1
]
print('\n'.join(res_list))
if args.open:
    save_to = pathlib.Path().home().joinpath('Downloads/weights.txt')
    save_to.write_text(data='\n'.join(res_list), encoding='utf8')
    lib.hugo_utils.open_in_browser(file_path=save_to)
