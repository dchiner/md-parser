import re
import json
import pathlib
import requests
import collections
from typing import Any
import lib.hugo_utils
import lib.hugo_uris

ERROR_NON_STANDARD_CHAR_MATCHES = "Non-standard character matches"
ERROR_REPEATED_WEIGHTS = "Repeated weights"
ERROR_TO_TO = 'To followed by **To'
ERROR_UNUSED_IMG_FILE = "Unused image file"
ERROR_UNUSED_SHARED_FILE = "Unused shared file"
LABEL_DETECTED_ON_ANCHOR = "Detected on anchor"
LABEL_DETECTED_ON_FILE = "Detected on file"
LABEL_DETECTED_ON_LINE= "Detected on line"
LABEL_DETECTED_ON_URL = "Detected on URL"
LABEL_DETECTED_ON_LINE_NUMBER = 'Detected on line number'
NON_STANDARD_CHAR_PATTERN = r"[\u200B\u200C\u200D\u2060]"
PDF_FILE_PATH = "/Entrust-PKIaaS-User-Guide.pdf"

def check_not_sized_imgs(
    error_log: collections.defaultdict[str, list[dict[str, Any]]],
    pages_dict: dict[pathlib.Path, str],
    md_file_path: pathlib.Path,
):
    each_img_split_list = pages_dict[md_file_path].split("webp)")
    for each_img_split in each_img_split_list[1:]:
        if each_img_split.strip().startswith('{width="'):
            continue
        if each_img_split.strip().startswith('{ width="'):
            continue
        error_log["Image without size specified"].append(
            {
                LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
                LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                    file_path=md_file_path,
                    base_url=lib.hugo_uris.HUGO_LOCAL_URL,
                    base_dir=lib.hugo_uris.HUGO_CONTENT_DIR_PATH,
                ),
            }
        )


def check_chars(
    error_log: collections.defaultdict[str, list[dict[str, Any]]],
    pages_dict: dict[pathlib.Path, str],
    md_file_path: pathlib.Path,
):
    non_standard_char_matches = re.findall(
        NON_STANDARD_CHAR_PATTERN, pages_dict[md_file_path]
    )
    if non_standard_char_matches:
        error_log["Non-standard character"].append(
            {
                LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
                LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                    file_path=md_file_path,
                    base_url=lib.hugo_uris.HUGO_LOCAL_URL,
                    base_dir=lib.hugo_uris.HUGO_CONTENT_DIR_PATH,
                ),
                ERROR_NON_STANDARD_CHAR_MATCHES: ",".join(
                    [repr(each_char) for each_char in set(non_standard_char_matches)]
                ),
            }
        )


def check_is_empty(
    error_log: collections.defaultdict[str, list[dict[str, Any]]],
    pages_dict: dict[pathlib.Path, str],
    md_file_path: pathlib.Path,
):
    if lib.hugo_utils.is_empty(file_content=pages_dict[md_file_path]):
        error_log["Empty file"].append(
            {
                LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
                LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                    file_path=md_file_path,
                    base_url=lib.hugo_uris.HUGO_LOCAL_URL,
                    base_dir=lib.hugo_uris.HUGO_CONTENT_DIR_PATH,
                ),
            }
        )


def check_links(
    error_log: collections.defaultdict[str, list[dict[str, Any]]],
    pages_dict: dict[pathlib.Path, str],
    md_file_path: pathlib.Path,
    external_links_set: set[str],
    base_dir: pathlib.Path,
):
    for each_tuple in re.findall(
        pattern=r"\[(.*?)\]\((.*?)\)", string=pages_dict[md_file_path]
    ):
        if each_tuple[1] == PDF_FILE_PATH:
            continue
        if each_tuple[0].startswith("http://") or each_tuple[1].startswith("http://"):
            error_log["HTTP link"].append(
                {
                    LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
                    LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                        file_path=md_file_path,
                        base_url=lib.hugo_uris.HUGO_LOCAL_URL,
                        base_dir=lib.hugo_uris.HUGO_CONTENT_DIR_PATH,
                    ),
                    LABEL_DETECTED_ON_ANCHOR: str(each_tuple),
                }
            )
            continue
        if each_tuple[0].startswith("https://") and each_tuple[0] != each_tuple[1]:
            error_log["Non-matching raw HTTPS URL"].append(
                {
                    LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
                    LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                        file_path=md_file_path,
                        base_url=lib.hugo_uris.HUGO_LOCAL_URL,
                        base_dir=lib.hugo_uris.HUGO_CONTENT_DIR_PATH,
                    ),
                    LABEL_DETECTED_ON_ANCHOR: each_tuple,
                }
            )
            continue
        if each_tuple[1].startswith("https"):
            external_links_set.add(each_tuple[1])
            continue
        if each_tuple[1].startswith("#"):
            continue
        if not each_tuple[1].startswith("/"):
            error_log["Link not starting with slash"].append(
                {
                    LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
                    LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                        file_path=md_file_path,
                        base_url=lib.hugo_uris.HUGO_LOCAL_URL,
                        base_dir=lib.hugo_uris.HUGO_CONTENT_DIR_PATH,
                    ),
                    LABEL_DETECTED_ON_ANCHOR: each_tuple,
                }
            )
            continue
        each_linked_file_path = lib.hugo_utils.get_linked_file_path(
            path_link=each_tuple[1], base_dir=base_dir
        )
        if not each_linked_file_path:
            error_log["Broken link"].append(
                {
                    LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
                    LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                        file_path=md_file_path,
                        base_url=lib.hugo_uris.HUGO_LOCAL_URL,
                        base_dir=lib.hugo_uris.HUGO_CONTENT_DIR_PATH,
                    ),
                    LABEL_DETECTED_ON_ANCHOR: each_tuple,
                }
            )
            continue
        if each_linked_file_path.suffix in [".webp", ".png", ".jpg", ".jpeg"]:
            continue
        if "#" in each_tuple[1]:
            each_anchor = each_tuple[1].split("#").pop().replace("-", " ").lower()
            if f"# {each_anchor}" not in pages_dict[
                each_linked_file_path
            ].lower().replace("-", " "):
                error_log["Broken external anchor"].append(
                    {
                        LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
                        LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                            file_path=md_file_path,
                            base_url=lib.hugo_uris.HUGO_LOCAL_URL,
                            base_dir=lib.hugo_uris.HUGO_CONTENT_DIR_PATH,
                        ),
                        LABEL_DETECTED_ON_ANCHOR: each_tuple,
                    }
                )
            continue
        if each_tuple[0] != lib.hugo_utils.get_page_title(
            file_contents=pages_dict[each_linked_file_path]
        ):
            error_log["Non-matching title"].append(
                {
                    LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
                    LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                        file_path=md_file_path,
                        base_url=lib.hugo_uris.HUGO_LOCAL_URL,
                        base_dir=lib.hugo_uris.HUGO_CONTENT_DIR_PATH,
                    ),
                    LABEL_DETECTED_ON_ANCHOR: each_tuple,
                }
            )


def check_child_toc(
    error_log: collections.defaultdict[str, list[dict[str, Any]]],
    md_file_path: pathlib.Path,
    pages_dict: dict[pathlib.Path, str],
):
    if md_file_path.name != "_index.md":
        return
    for each_file_path in md_file_path.parent.iterdir():
        if each_file_path.name == "_index.md":
            continue
        each_file_name = each_file_path.name.split(".")[0]
        if f"/{each_file_name})" in pages_dict[md_file_path]:
            continue
        if f"/{each_file_name}/)" in pages_dict[md_file_path]:
            continue
        error_log["Child page not in TOC"].append(
            {
                LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
                LABEL_DETECTED_ON_URL: lib.hugo_utils.path2url(
                    file_path=md_file_path,
                    base_url=lib.hugo_uris.HUGO_LOCAL_URL,
                    base_dir=lib.hugo_uris.HUGO_CONTENT_DIR_PATH,
                ),
                LABEL_DETECTED_ON_ANCHOR: each_file_name,
            }
        )


def check_repeated_weights(
    error_log: collections.defaultdict[str, list[dict[str, Any]]],
    md_file_path: pathlib.Path,
    pages_dict: dict[pathlib.Path, str],
):
    weights_list = list()
    if md_file_path.name != "_index.md":
        return
    for each_file_path in md_file_path.parent.iterdir():
        print(each_file_path)
        if each_file_path.name == "_index.md":
            continue
        if each_file_path.suffix == ".md":
            each_page_weight = lib.hugo_utils.get_page_weight(
                file_contents=pages_dict[each_file_path]
            )
        else:
            each_page_weight = lib.hugo_utils.get_page_weight(
                file_contents=pages_dict[each_file_path.joinpath("_index.md")]
            )
        weights_list.append(each_page_weight)
    weight_counts = collections.Counter(weights_list)
    repeated_weights = {w for w, count in weight_counts.items() if count > 1}
    if repeated_weights and repeated_weights != {-1}:
        error_log["Repeated weights under"].append(
            {
                LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
                ERROR_REPEATED_WEIGHTS: ",".join(
                    [str(each_weight) for each_weight in repeated_weights]
                ),
            }
        )

def check_to_before_to(md_file_path: pathlib.Path, pages_dict: dict[pathlib.Path, str], error_log: dict[str, list[dict[str, Any]]]):
    each_file_lines = [each_line.strip() for each_line in pages_dict[md_file_path].splitlines() if each_line.strip()]
    i=0
    for i in range(1, len(each_file_lines)):
        if '**To' in each_file_lines[i]:
            error_log[ERROR_TO_TO].append(
                {
                    LABEL_DETECTED_ON_FILE: md_file_path.as_posix(),
                    LABEL_DETECTED_ON_LINE: each_file_lines[i],
                    LABEL_DETECTED_ON_LINE_NUMBER: i
                }
            )

def check_unused_img_files(
    img_dir: pathlib.Path,
    error_log: dict[str, list[dict[str, Any]]],
    all_md_dict: dict[pathlib.Path, str],
):
    for each_img_file_path in img_dir.rglob(pattern="*.webp"):
        each_page_include_list = [
            each_page_contents
            for each_page_contents in all_md_dict.values()
            if each_img_file_path.name in each_page_contents
        ]
        if not each_page_include_list:
            error_log[ERROR_UNUSED_IMG_FILE].append(
                {
                    LABEL_DETECTED_ON_FILE: each_img_file_path.as_posix(),
                }
            )


def check_unused_shared_pages(
    shared_dir: pathlib.Path,
    error_log: dict[str, list[dict[str, Any]]],
    all_md_dict: dict[pathlib.Path, str],
):
    for each_shared_file_path in shared_dir.rglob(pattern="*.html"):
        each_page_include_list = [
            each_page_contents
            for each_page_contents in all_md_dict.values()
            if each_shared_file_path.stem in each_page_contents
        ]
        if not each_page_include_list:
            error_log[ERROR_UNUSED_SHARED_FILE].append(
                {
                    LABEL_DETECTED_ON_FILE: each_shared_file_path.as_posix(),
                }
            )


def parse_res(error_log: dict[str, list[dict[str, Any]]]):
    for each_error_key in error_log.keys():
        print(f"{each_error_key}: {len(error_log[each_error_key])}")
    output_json_file_path = pathlib.Path().home() / "Downloads/log.json"
    print(f"Saving file://{output_json_file_path.as_posix()}")
    with output_json_file_path.open(mode="w") as output_json_file:
        json.dump(obj=error_log, fp=output_json_file, indent=4)


def delete_unused_files(error_log: dict[str, list[dict[str, Any]]]):
    for each_item in error_log[ERROR_UNUSED_IMG_FILE]:
        each_img_file = pathlib.Path(each_item[LABEL_DETECTED_ON_FILE])
        print("Removing", each_img_file)
        each_img_file.unlink()
    for each_item in error_log[ERROR_UNUSED_SHARED_FILE]:
        each_shared_file = pathlib.Path(each_item[LABEL_DETECTED_ON_FILE])
        print("Removing", each_shared_file)
        each_shared_file.unlink()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog="hCheck.py",
        description="checks the files in the Hugo project",
    )
    parser.add_argument(
        "-b",
        "--base-dir",
        type=pathlib.Path,
        default=lib.hugo_uris.HUGO_CONTENT_DIR_PATH,
        help=f"Hugo base directory. Defaults to {lib.hugo_uris.HUGO_CONTENT_DIR_PATH}",
    )
    parser.add_argument(
        "-e", "--external", action="store_true", help="check external links"
    )
    parser.add_argument(
        "-d", "--delete", action="store_true", help="delete unused PNG and HTML files"
    )
    args = parser.parse_args()
    my_base_dir = pathlib.Path(args.base_dir)
    assert my_base_dir.exists(), f"Base directory {my_base_dir} does not exist"
    assert my_base_dir.is_dir(), f"Base directory {my_base_dir} is not a directory"
    my_shortcodes_dict = lib.hugo_utils.get_shortcodes_dict(
        base_dir=lib.hugo_uris.HUGO_SHORTCODES_DIR_PATH
    )
    my_pages_dict: dict[pathlib.Path, str] = lib.hugo_utils.get_pages_dict(
        base_dir=my_base_dir, shortcodes_dict=my_shortcodes_dict
    )
    my_error_log: collections.defaultdict[str, list[dict[str, Any]]] = (
        collections.defaultdict(list)
    )
    my_external_links_set: set[str] = set()
    for each_md_file_path in my_pages_dict:
        print("Checking", each_md_file_path)
        check_not_sized_imgs(
            error_log=my_error_log,
            pages_dict=my_pages_dict,
            md_file_path=each_md_file_path,
        )
        check_chars(
            error_log=my_error_log,
            pages_dict=my_pages_dict,
            md_file_path=each_md_file_path,
        )
        check_is_empty(
            error_log=my_error_log,
            pages_dict=my_pages_dict,
            md_file_path=each_md_file_path,
        )
        check_links(
            error_log=my_error_log,
            pages_dict=my_pages_dict,
            md_file_path=each_md_file_path,
            external_links_set=my_external_links_set,
            base_dir=my_base_dir,
        )
        check_child_toc(
            error_log=my_error_log,
            pages_dict=my_pages_dict,
            md_file_path=each_md_file_path,
        )
        check_repeated_weights(
            error_log=my_error_log,
            md_file_path=each_md_file_path,
            pages_dict=my_pages_dict,
        )
    check_unused_img_files(
        error_log=my_error_log,
        all_md_dict=my_pages_dict,
        img_dir=lib.hugo_uris.HUGO_SCREENSHOTS_DIR_PATH,
    )
    check_unused_shared_pages(
        error_log=my_error_log,
        all_md_dict=my_pages_dict,
        shared_dir=lib.hugo_uris.HUGO_SHARED_DIR_PATH,
    )
    print("=" * 103)
    if my_error_log:
        parse_res(error_log=my_error_log)
    else:
        print("No errors detected")
    if args.external:
        print("=" * 103)
        print("Checking external URLs:\n")
        for each_url in my_external_links_set:
            try:
                response = requests.get(url=each_url, timeout=10)
                if 200 <= response.status_code < 300:
                    print("OK".ljust(len("ERROR")), each_url)
                else:
                    print("ERROR", each_url)
            except requests.exceptions.RequestException:
                print("ERROR", each_url)
    if args.delete:
        delete_unused_files(error_log=my_error_log)
