import re
import json
import pathlib
import requests
import collections
import lib.hugo_utils
import lib.hugo_uris

LABEL_DETECTED_ON_ANCHOR = 'Detected on anchor'
LABEL_DETECTED_ON_FILE = 'Detected on file'
LABEL_DETECTED_ON_URL = 'Detected on URL'
LABEL_NON_STANDARD_CHAR_MATCHES = 'Non-standard character matches'
NON_STANDARD_CHAR_PATTERN = r'[\u200B\u200C\u200D\u2060]'
PDF_FILE_PATH = '/Entrust-PKIaaS-User-Guide.pdf'
ERROR_UNUSED_IMG_FILE = 'Unused image file'



def check_not_sized_imgs(error_log: collections.defaultdict[str, list], pages_dict: dict[pathlib.Path, str], md_file_path: pathlib.Path):
        each_img_split_list = pages_dict[md_file_path].split('webp)')
        for each_img_split in each_img_split_list[1:]:
            if each_img_split.strip().startswith('{width="'):
              continue
            if each_img_split.strip().startswith('{ width="'):
              continue
            error_log['Image without size specified'].append(
                {
                    LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
                    LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                        file_path=md_file_path,
                        base_url=lib.hugo_uris.BASE_URL_LOCAL,
                        base_dir=lib.hugo_uris.BASE_DIR
                    )
                }
            )

def check_chars(error_log: collections.defaultdict[str, list], pages_dict: dict[pathlib.Path, str], md_file_path: pathlib.Path):
        non_standard_char_matches = re.findall(NON_STANDARD_CHAR_PATTERN, pages_dict[md_file_path])
        if non_standard_char_matches:
            error_log['Non-standard character'].append(
                {
                    LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
                    LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                        file_path=md_file_path,
                        base_url=lib.hugo_uris.BASE_URL_LOCAL,
                        base_dir=lib.hugo_uris.BASE_DIR
                    ),
                    LABEL_NON_STANDARD_CHAR_MATCHES: ','.join([repr(each_char) for each_char in set(non_standard_char_matches)])
                }
            )
def check_is_empty(error_log: collections.defaultdict[str, list], pages_dict: dict[pathlib.Path, str], md_file_path: pathlib.Path):
        if lib.hugo_utils.is_empty(file_content=pages_dict[md_file_path]):
            error_log['Empty file'].append(
                {
                    LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
                    LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                        file_path=md_file_path,
                        base_url=lib.hugo_uris.BASE_URL_LOCAL,
                        base_dir=lib.hugo_uris.BASE_DIR
                    )
                }
            )
def check_links(error_log: collections.defaultdict[str, list], pages_dict: dict[pathlib.Path, str], md_file_path: pathlib.Path, external_links_set: set[str], base_dir: pathlib.Path):
        for each_tuple in re.findall(pattern=r"\[(.*?)\]\((.*?)\)", string=pages_dict[md_file_path]):
            if each_tuple[1] == PDF_FILE_PATH:
                continue
            if each_tuple[0].startswith('http://') or each_tuple[1].startswith('http://'):
                error_log['HTTP link'].append(
                    {
                        LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
                        LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                            file_path=md_file_path,
                            base_url=lib.hugo_uris.BASE_URL_LOCAL,
                            base_dir=lib.hugo_uris.BASE_DIR
                        ),
                        LABEL_DETECTED_ON_ANCHOR: str(each_tuple)
                    }
                )
                continue
            if each_tuple[0].startswith('https://') and each_tuple[0] != each_tuple[1]:
                error_log['Non-matching raw HTTPS URL'].append(
                    {
                        LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
                        LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                            file_path=md_file_path,
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
                error_log['Link not starting with slash'].append(
                    {
                        LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
                        LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                            file_path=md_file_path,
                            base_url=lib.hugo_uris.BASE_URL_LOCAL,
                            base_dir=lib.hugo_uris.BASE_DIR
                        ),
                        LABEL_DETECTED_ON_ANCHOR: each_tuple
                    }
                )
                continue
            each_linked_file_path = lib.hugo_utils.get_linked_file_path(
                path_link=each_tuple[1],
                base_dir=base_dir
            )
            if not each_linked_file_path:
                error_log['Broken link'].append(
                    {
                        LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
                        LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                            file_path=md_file_path,
                            base_url=lib.hugo_uris.BASE_URL_LOCAL,
                            base_dir=lib.hugo_uris.BASE_DIR
                        ),
                        LABEL_DETECTED_ON_ANCHOR: each_tuple
                    }
                )
                continue
            if each_linked_file_path.suffix in ['.webp', '.png', '.jpg', '.jpeg']:
                continue
            if '#' in each_tuple[1]:
                each_anchor = each_tuple[1].split('#').pop().replace('-', ' ')
                if f'# {each_anchor}' not in pages_dict[each_linked_file_path].lower().replace('-', ' '):
                    error_log['Broken external anchor'].append(
                        {
                            LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
                            LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                                file_path=md_file_path,
                                base_url=lib.hugo_uris.BASE_URL_LOCAL,
                                base_dir=lib.hugo_uris.BASE_DIR
                            ),
                            LABEL_DETECTED_ON_ANCHOR: each_tuple
                        }
                    )
                continue
            if each_tuple[0] != lib.hugo_utils.get_page_title(file_contents=pages_dict[each_linked_file_path]):
                error_log['Non-matching title'].append(
                    {
                        LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
                        LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                            file_path=md_file_path,
                            base_url=lib.hugo_uris.BASE_URL_LOCAL,
                            base_dir=lib.hugo_uris.BASE_DIR
                        ),
                        LABEL_DETECTED_ON_ANCHOR: each_tuple
                    }
                )

def check_child_toc(error_log: collections.defaultdict[str, list], md_file_path: pathlib.Path, pages_dict: dict[pathlib.Path, str], base_dir: pathlib.Path):
  if md_file_path.name != '_index.md':
    return
  for each_file_path in md_file_path.parent.iterdir():
      if each_file_path.name == '_index.md':
        continue
      each_file_name = each_file_path.name.split('.')[0]
      if  f'/{each_file_name})' in pages_dict[md_file_path]:
        continue
      if  f'/{each_file_name}/)' in pages_dict[md_file_path]:
        continue
      error_log['Child page not in TOC'].append(
          {
              LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
              LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                  file_path=md_file_path,
                  base_url=lib.hugo_uris.BASE_URL_LOCAL,
                  base_dir=lib.hugo_uris.BASE_DIR
              ),
              LABEL_DETECTED_ON_ANCHOR: each_file_name
          }
      )

def check_unused_img_files(img_dir: pathlib.Path, error_log: dict[str, list], all_md_dict: dict[pathlib.Path, str]):
    for each_img_file_path in img_dir.rglob(pattern='*.webp'):
        each_page_include_list = [
            each_page_contents for each_page_contents in all_md_dict.values()
            if each_img_file_path.name in each_page_contents
        ]
        if not each_page_include_list:
            error_log[ERROR_UNUSED_IMG_FILE].append(
                {
                    LABEL_DETECTED_ON_FILE: each_img_file_path.as_posix(),
                }
            )

def parse_res(error_log: dict[str, list]):
    [print(f'{each_error_key}: {len(error_log[each_error_key])}') for each_error_key in error_log.keys()]
    output_json_file_path = pathlib.Path().home() / 'Downloads/log.json'
    print(f'Saving file://{output_json_file_path.as_posix()}')
    json.dump(obj=error_log, fp=output_json_file_path.open(mode='w'))

def delete_unused_files(error_log: dict[str, list]):
    for each_item in error_log[ERROR_UNUSED_IMG_FILE]:
        each_img_file = pathlib.Path(each_item[LABEL_DETECTED_ON_FILE])
        print('Removing', each_img_file)
        each_img_file.unlink()            

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        prog='hCheck.py',
        description='checks the files in the Hugo project',
    )
    parser.add_argument(
        '-b',
        '--base-dir',
        type=pathlib.Path,
        default=lib.hugo_uris.BASE_DIR,
        help=f'Hugo base directory. Defaults to {lib.hugo_uris.BASE_DIR}'
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
    my_base_dir = pathlib.Path(args.base_dir)
    assert my_base_dir.exists(), f'Base directory {my_base_dir} does not exist'
    assert my_base_dir.is_dir(), f'Base directory {my_base_dir} is not a directory'
    my_pages_dict : dict[pathlib.Path, str] = lib.hugo_utils.get_pages_dict(base_dir=my_base_dir)
    my_error_log = collections.defaultdict(list) 
    my_external_links_set : set[str] = set()
    for each_md_file_path in my_pages_dict:
        print('Checking', each_md_file_path)
        check_not_sized_imgs(
            error_log=my_error_log,
            pages_dict=my_pages_dict,
            md_file_path=each_md_file_path
        )
        check_chars(
            error_log=my_error_log,
            pages_dict=my_pages_dict,
            md_file_path=each_md_file_path
        )
        check_is_empty(
            error_log=my_error_log,
            pages_dict=my_pages_dict,
            md_file_path=each_md_file_path
        )
        check_links(
            error_log=my_error_log,
            pages_dict=my_pages_dict,
            md_file_path=each_md_file_path,
            external_links_set=my_external_links_set,
            base_dir=my_base_dir
        )
        check_child_toc(
            error_log=my_error_log,
            pages_dict=my_pages_dict,
            md_file_path=each_md_file_path,
            base_dir=my_base_dir
        )
    check_unused_img_files(
        error_log=my_error_log,
        all_md_dict=my_pages_dict,
        img_dir=lib.hugo_uris.BASE_DIR.parent.joinpath('static/img/screenshots')
    )
    print('=' * 103)
    if my_error_log:
        parse_res(error_log=my_error_log)
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
            except requests.exceptions.RequestException:
                print('ERROR', each_url)
    if args.delete:
        delete_unused_files(error_log=my_error_log)
