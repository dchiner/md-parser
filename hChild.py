import pathlib
import lib.hugo_utils

PAGE_WEIGHT = 'PAGE_WEIGHT'
PAGE_TITLE = 'PAGE_TITLE'


def get_sub_md_files_dict(base_dir: pathlib.Path) -> dict[pathlib.Path, dict[str, int | str]]:
    sub_md_files_dict : dict[pathlib.Path, dict[str, int | str]] = dict()
    for each_md_file_path in base_dir.iterdir():
        if each_md_file_path.name == '_index.md':
            continue
        if each_md_file_path.name == 'img':
            continue
        if each_md_file_path.is_dir():
            each_md_file_content = each_md_file_path.joinpath('_index.md').read_text(encoding='utf8')
        else:
            each_md_file_content = each_md_file_path.read_text(encoding='utf8')
        sub_md_files_dict[each_md_file_path] = {
            PAGE_TITLE: lib.hugo_utils.get_page_title(file_contents=each_md_file_content),
            PAGE_WEIGHT: lib.hugo_utils.get_page_weight(
                file_contents=each_md_file_content,
                no_weigh_found=lib.hugo_utils.NO_WEIGHT_FOUND.exception
            )
        }
    return sub_md_files_dict


def check_page_weights(md_file_dict: dict[pathlib.Path, dict[str, int | str]]):
    pages_without_weight = [
        str(each_md_page_path) for each_md_page_path in md_file_dict
        if not md_file_dict[each_md_page_path][PAGE_WEIGHT]
    ]
    assert not pages_without_weight, f'The following pages does not have weight: {pages_without_weight}'
    page_weight_list = [
        md_file_dict[each_md_page_path][PAGE_WEIGHT]
        for each_md_page_path in md_file_dict
    ]
    pages_with_repeated_weight = [
        str(each_md_page_path) for each_md_page_path in md_file_dict
        if page_weight_list.count(md_file_dict[each_md_page_path][PAGE_WEIGHT]) > 1
    ]
    if pages_with_repeated_weight:
        assert f'The following pages have repeated weight: {pages_with_repeated_weight}'


def print_child_toc(md_file_dict: dict[pathlib.Path, dict[str, int | str]]):
    sorted_md_file_paths = [key for key, _ in sorted(md_file_dict.items(), key=lambda item: item[1][PAGE_WEIGHT])]
    for each_md_file_path in sorted_md_file_paths:
        each_page_title = md_file_dict[each_md_file_path][PAGE_TITLE]
        each_md_file_path = each_md_file_path.as_posix()
        if each_md_file_path.endswith('.md'):
            each_md_file_path = each_md_file_path[:-len('.md')]
        each_md_file_path = each_md_file_path.split('/content').pop()
        print(f'- [{each_page_title}]', end='')
        print(f'({each_md_file_path})')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        prog='hChild.py',
        description='Generate a markdown TOC for the files under a folder',
    )
    parser.add_argument(
        '-p',
        '--path',
        required=True,
        help='generates a toc for all the child pages under PATH'
    )
    parser.add_argument(
        '-o',
        '--open',
        action='store_true',
        help='Open the file in  Microsoft Studio Code'
    )
    args = parser.parse_args()
    if args.path.endswith('_index.md'):
        my_base_dir = pathlib.Path(args.path[:-len('_index.md')])
    else:
        my_base_dir = pathlib.Path(args.path)
    assert my_base_dir.exists(), f'Path not found: {my_base_dir}'
    assert my_base_dir.is_dir(), f'Not a folder {my_base_dir}'
    my_md_file_dict : dict[pathlib.Path, dict[str, int | str]] = get_sub_md_files_dict(base_dir=my_base_dir)
    check_page_weights(md_file_dict=my_md_file_dict)
    print_child_toc(md_file_dict=my_md_file_dict)
