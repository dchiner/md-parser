import pathlib
import argparse
import lib.hugo_uris
import lib.hugo_utils


class MarkdownFile:

    def __init__(self, file_path: pathlib.Path):
        page_contents = file_path.read_text(encoding='utf8')
        self.title = lib.hugo_utils.get_page_title(file_contents=page_contents)
        self.weight = lib.hugo_utils.get_page_weight(
            file_contents=page_contents,
            no_weigh_found=lib.hugo_utils.NO_WEIGHT_FOUND.silent
        )



def get_page_dicts(base_dir: pathlib.Path) -> dict[pathlib.Path, MarkdownFile]:
    md_pages_dict : dict[pathlib.Path, MarkdownFile] = dict()
    for each_md_file_path in base_dir.rglob('*.md'):
        if each_md_file_path == base_dir / '_index.md':
            continue
        each_md_file: MarkdownFile = MarkdownFile(file_path=each_md_file_path)
        if each_md_file_path.name == '_index.md':
            each_md_file_path = each_md_file_path.parent
        md_pages_dict[each_md_file_path] = each_md_file
    return md_pages_dict


def print_dir(base_dir: pathlib.Path, current_dir: pathlib.Path, pages_dict: dict[pathlib.Path, MarkdownFile], max_rec: int, current_rec: int =0):
    weights_list : list[int] = [pages_dict[each_path].weight for each_path in current_dir.iterdir() if each_path in pages_dict]
    for each_weight in sorted(weights_list):
        each_path = [
            each_sub_file_path for each_sub_file_path in current_dir.iterdir() 
            if each_sub_file_path in pages_dict and pages_dict[each_sub_file_path].weight == each_weight
        ].pop()
        each_relative_path = each_path.relative_to(lib.hugo_uris.BASE_DIR).as_posix()
        each_pretty_path = ' ' * each_relative_path.rfind('/')
        each_pretty_path += str(each_weight).ljust(5)
        each_pretty_path += each_relative_path[each_relative_path.rfind('/') + 1:]
        print(
            each_pretty_path.ljust(50),
            pages_dict[each_path].title.ljust(70),
        )
        if (current_rec < max_rec) and each_path.is_dir():
            print_dir(
                base_dir=base_dir,
                current_dir=each_path,
                pages_dict=pages_dict,
                max_rec=max_rec,
                current_rec=current_rec + 1
            )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='hListWeights.py',
        description='lists the page weights of a markdown Hugo project',
    )
    parser.add_argument(
        '-p',
        '--path',
        required=False,
        default=lib.hugo_uris.BASE_DIR,
        help=f'check the weights in the PATH folder. Defaults to {lib.hugo_uris.BASE_DIR}'
    )
    parser.add_argument(
        '-r',
        '--rec',
        default=9999,
        help='recurse the file tree up to REC times'
    )
    args = parser.parse_args()
    my_base_dir = pathlib.Path(args.path)
    my_pages_dict = get_page_dicts(base_dir=my_base_dir)
    print_dir(
        base_dir=my_base_dir,
        current_dir=my_base_dir,
        pages_dict=my_pages_dict,
        max_rec=int(args.rec)
    )
