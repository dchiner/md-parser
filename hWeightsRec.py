import lib.hugo_uris
import lib.hugo_utils


def print_dir(dir_path, pages_dict):
    sub_files_list = [each_path for each_path in pages_dict if each_path.parent == dir_path]
    weight_list = [pages_dict[each_path]['weight'] for each_path in sub_files_list]
    for each_weight in sorted(weight_list):
        each_path = [
            sub_file_path for sub_file_path in sub_files_list
            if pages_dict[sub_file_path]['weight'] == each_weight
        ].pop()
        each_pretty_path = each_path.relative_to(lib.hugo_uris.BASE_DIR).as_posix()
        each_pretty_path = ' ' * each_pretty_path.rfind('/') + str(each_weight) + ' ' + each_pretty_path[
            each_pretty_path.rfind('/') + 1:
        ]
        print(
            each_pretty_path.ljust(50),
            pages_dict[each_path]['title'].ljust(70),
        )
        if each_path.is_dir():
            print_dir(dir_path=each_path, pages_dict=pages_dict)


if __name__ == '__main__':
    my_pages_dict = dict()
    for each_md_file_path in lib.hugo_uris.BASE_DIR.rglob('*.md'):
        if each_md_file_path == lib.hugo_uris.BASE_DIR / '_index.md':
            continue
        if each_md_file_path == lib.hugo_uris.BASE_DIR / 'img':
            continue
        each_file_contents = each_md_file_path.read_text(encoding='utf8')
        each_file_title = lib.hugo_utils.get_page_title(file_contents=each_file_contents)
        each_file_weight = lib.hugo_utils.get_page_weight(
            file_contents=each_file_contents,
            no_weigh_found=lib.hugo_utils.NO_WEIGHT_FOUND.silent
        )
        if each_md_file_path.name == '_index.md':
            each_md_file_path = each_md_file_path.parent
        my_pages_dict[each_md_file_path] = {'title': each_file_title, 'weight': each_file_weight}
    print_dir(dir_path=lib.hugo_uris.BASE_DIR, pages_dict=my_pages_dict)
