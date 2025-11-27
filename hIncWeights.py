import lib.hugo_utils
import pathlib
import argparse

parser = argparse.ArgumentParser(
    prog='hIncWeights.py',
    description='lists the page weights of a markdown Hugo prokect',
)
parser.add_argument(
    '-p',
    '--path',
    help=f'increase the weigth in the first-level sections under PATH'
)
parser.add_argument(
    '-i',
    '--increment',
    help='add INC to each weight'
)
parser.add_argument(
    '-g',
    '--greater',
    help='increment only weights greater than GREATER'
)
args = parser.parse_args()
base_dir = pathlib.Path(args.path)
weights_dict = dict()
assert base_dir.is_dir(), f'"{base_dir}" is not a directory'
for each_file_path in base_dir.iterdir():
    if each_file_path.name == 'img':
        continue
    if each_file_path.is_file():
        each_markdown_file_path  = each_file_path
    else:
        each_markdown_file_path = each_file_path.joinpath('_index.md')
    each_page_contents = each_markdown_file_path.read_text(encoding='utf8')
    each_page_weight = lib.hugo_utils.get_page_weight(
        file_contents=each_page_contents,
        no_weigh_found=lib.hugo_utils.NO_WEIGHT_FOUND.silent
    )
    if each_page_weight <= int(args.greater):
        continue
    assert f'weight: {each_page_weight}' in each_page_contents, f'No valid format in {each_markdown_file_path}'
    each_new_page_weight = each_page_weight + int(args.increment)
    weights_dict[each_page_weight] = {'path': each_file_path, 'new': each_new_page_weight}
    each_page_contents = each_page_contents.replace(
        f'weight: {each_page_weight}',
        f'weight: {each_new_page_weight}'
    )
    each_markdown_file_path.write_text(data=each_page_contents, encoding='utf8')
for each_weight in sorted(weights_dict.keys()):
    print(weights_dict[each_weight]['path'].name.ljust(12), each_weight, '->', weights_dict[each_weight]['new'])
