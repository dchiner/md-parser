import re
import json
import pathlib
import requests
import PIL.Image
import lib.hugo_utils
import lib.hugo_uris

PNG_MAX_WIDTH = 750
ERROR_BROKEN_EXTERNAL_ANCHOR = 'Broken external anchor'
ERROR_BROKEN_LINK = 'Broken link'
ERROR_EMPTY_TITLE = 'Empty file'
ERROR_HTTP_LINK = 'HTTP link'
ERROR_LINK_NOT_STARTING_WITH_SLASH = 'Link not starting with slash ("/")'
ERROR_NON_MATCHING_RAW_HTTPS_URL = 'Non-matching raw HTTPS URL'
ERROR_NON_MATCHING_TITLE = 'No matching title'
ERROR_PNG_WIDTH_TO_LARGE = f'Picture width exceeding {PNG_MAX_WIDTH} pixels'
ERROR_UNUSED_PNG_FILE = 'Unused PNG file'
LABEL_DETECTED_ON_ANCHOR = 'Detected on anchor'
LABEL_DETECTED_ON_FILE = 'Detected on file'
LABEL_DETECTED_ON_URL = 'Detected on URL'
LABEL_ERRORS = 'ERRORS'
LABEL_EXTERNAL_LINKS = 'External links'


def parse_md(all_pages_dict, log_list, external_links_set, max_png_width):
    for each_md_file_path in all_pages_dict:
        print('Parsing', each_md_file_path)
        if lib.hugo_utils.is_empty(file_content=all_pages_dict[each_md_file_path]):
            log_list.append(
                {
                    LABEL_ERROR_TYPE: 'Empty file',
                    LABEL_DETECTED_ON_FILE: each_md_file_path.as_posix(),
                    LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                        file_path=each_md_file_path,
                        base_url=lib.hugo_uris.BASE_URL_LOCAL,
                        base_dir=lib.hugo_uris.BASE_DIR
                    )
                }
            )
        for each_tuple in re.findall(pattern=r"\[(.*?)\]\((.*?)\)", string=all_pages_dict[each_md_file_path]):
            if each_tuple[0].startswith('http://') or each_tuple[1].startswith('http://'):
                log_list.append(
                    {
                        LABEL_ERROR_TYPE: 'HTTP link',
                        LABEL_DETECTED_ON_FILE: each_md_file_path.as_posix(),
                        LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                            file_path=each_md_file_path,
                            base_url=lib.hugo_uris.BASE_URL_LOCAL,
                            base_dir=lib.hugo_uris.BASE_DIR
                        ),
                        LABEL_DETECTED_ON_ANCHOR: str(each_tuple)
                    }
                )
                continue
            if each_tuple[0].startswith('https://') and each_tuple[0] != each_tuple[1]:
                log_list.append(
                    {
                        LABEL_ERROR_TYPE: 'Non-matching raw HTTPS URL',
                        LABEL_DETECTED_ON_FILE: each_md_file_path.as_posix(),
                        LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                            file_path=each_md_file_path,
                            base_url=lib.hugo_uris.BASE_URL_LOCAL,
                            base_dir=lib.hugo_uris.BASE_DIR
                        ),
                        LABEL_DETECTED_ON_ANCHOR: each_tuple
                    }
                )
                continue
            if each_tuple[1].startswith('https'):
                external_links_set.add(each_tuple[1])
                continue
            if each_tuple[1].startswith('#'):
                continue
            if not each_tuple[1].startswith('/'):
                log_list.append(
                    {
                        LABEL_ERROR_TYPE: 'Link not starting with slash ("/")',
                        LABEL_DETECTED_ON_FILE: each_md_file_path.as_posix(),
                        LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                            file_path=each_md_file_path,
                            base_url=lib.hugo_uris.BASE_URL_LOCAL,
                            base_dir=lib.hugo_uris.BASE_DIR
                        ),
                        LABEL_DETECTED_ON_ANCHOR: each_tuple
                    }
                )
                continue
            each_linked_file_path = lib.hugo_utils.get_linked_file_path(
                path_link=each_tuple[1],
                base_dir=lib.hugo_uris.BASE_DIR
            )
            if not each_linked_file_path:
                log_list.append(
                    {
                        LABEL_ERROR_TYPE: 'Broken link',
                        LABEL_DETECTED_ON_FILE: each_md_file_path.as_posix(),
                        LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                            file_path=each_md_file_path,
                            base_url=lib.hugo_uris.BASE_URL_LOCAL,
                            base_dir=lib.hugo_uris.BASE_DIR
                        ),
                        LABEL_DETECTED_ON_ANCHOR: each_tuple
                    }
                )
                continue
            if each_linked_file_path.suffix == '.png':
                with PIL.Image.open(each_linked_file_path) as png_file:
                    each_img_size = png_file.size
                if each_img_size[0] > max_png_width:
                    log_list.append(
                        {
                            LABEL_ERROR_TYPE: f'Picture width exceeding {max_png_width} pixels',
                            LABEL_DETECTED_ON_FILE: each_linked_file_path.as_posix(),
                            LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                                file_path=each_md_file_path,
                                base_dir=lib.hugo_uris.BASE_DIR,
                                base_url=lib.hugo_uris.BASE_URL_LOCAL
                            ),
                            LABEL_DETECTED_ON_ANCHOR: each_tuple
                        }
                    )
                continue
            if '#' in each_tuple[1]:
                each_anchor = each_tuple[1].split('#').pop().replace('-', ' ')
                if f'# {each_anchor}' not in all_pages_dict[each_linked_file_path].lower().replace('-', ' '):
                    log_list.append(
                        {
                            LABEL_ERROR_TYPE: 'Broken external anchor',
                            LABEL_DETECTED_ON_FILE: each_md_file_path.as_posix(),
                            LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                                file_path=each_md_file_path,
                                base_url=lib.hugo_uris.BASE_URL_LOCAL,
                                base_dir=lib.hugo_uris.BASE_DIR
                            ),
                            LABEL_DETECTED_ON_ANCHOR: each_tuple
                        }
                    )
                continue
            if each_tuple[0] != lib.hugo_utils.get_page_title(file_contents=all_pages_dict[each_linked_file_path]):
                log_list.append(
                    {
                        LABEL_ERROR_TYPE: 'No matching title',
                        LABEL_DETECTED_ON_FILE: each_md_file_path.as_posix(),
                        LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                            file_path=each_md_file_path,
                            base_url=lib.hugo_uris.BASE_URL_LOCAL,
                            base_dir=lib.hugo_uris.BASE_DIR
                        ),
                        LABEL_DETECTED_ON_ANCHOR: each_tuple
                    }
                )


def check_unused_png_files(base_dir, log_dict, all_md_dict):
    for each_png_file_path in base_dir.joinpath('img').rglob(pattern='*.png'):
        each_page_include_list = [
            each_page_contents for each_page_contents in all_md_dict.values()
            if each_png_file_path.name in each_page_contents
        ]
        if not each_page_include_list:
            log_dict.append(
                {
                    LABEL_ERROR_TYPE: 'Unused PNG file',
                    LABEL_DETECTED_ON_FILE: each_png_file_path.as_posix(),
                }
            )


LABEL_ERROR_TYPE = 'Error type'
if __name__ == '__main__':
    import argparse
    import lib.hugo_utils

    parser = argparse.ArgumentParser(
        prog='hCheck.py',
        description='checks the files in the Hugo project',
    )
    parser.add_argument(
        '-o',
        '--open',
        action='store_true',
        help='open the generated JSON log in browser'
    )
    parser.add_argument(
        '-e',
        '--external',
        action='store_true',
        help='check external links'
    )
    parser.add_argument(
        '-d',
        '--delete',
        action='store_true',
        help='delete unused PGN files'
    )
    args = parser.parse_args()
    my_pages_dict = lib.hugo_utils.get_pages_dict(base_dir=lib.hugo_uris.BASE_DIR)
    my_log_list = list()
    my_external_links_set = set()
    my_max_png_width = 750
    parse_md(
        all_pages_dict=my_pages_dict,
        log_list=my_log_list,
        max_png_width=my_max_png_width,
        external_links_set=my_external_links_set
    )
    check_unused_png_files(
        log_dict=my_log_list,
        all_md_dict=my_pages_dict,
        base_dir=lib.hugo_uris.BASE_DIR
    )
    print('=' * 103)
    if my_log_list:
        error_keys = [each_item[LABEL_ERROR_TYPE] for each_item in my_log_list]
        [print(f'{each_error_key}: {error_keys.count(each_error_key)}') for each_error_key in set(error_keys)]
        output_json_file_path = pathlib.Path().home() / 'Downloads/log.json'
        print(f'Saving file://{output_json_file_path.as_posix()}')
        json.dump(
            obj=sorted(my_log_list, key=lambda x: x[LABEL_ERROR_TYPE]),
            fp=output_json_file_path.open(mode='w')
        )
        if args.open:
            lib.hugo_utils.open_in_browser(file_path=output_json_file_path)
    else:
        print('No errors detected')
    if args.external:
        print('=' * 103)
        print('Checking external URLs:\n')
        for each_url in my_external_links_set:
            try:
                response = requests.get(url=each_url, timeout=10)
                if 200 <= response.status_code < 300:
                    print('OK'.ljust(len('ERROR')), each_url)
                else:
                    print('ERROR', each_url)
            except requests.exceptions.RequestException as e:
                print('ERROR', each_url)
    if args.delete:
        for each_item in my_log_list:
            if each_item[LABEL_ERROR_TYPE] == ERROR_UNUSED_PNG_FILE:
                each_png_file = pathlib.Path(each_item[LABEL_DETECTED_ON_FILE])
                print('Removing', each_png_file)
                each_png_file.unlink()
