import re
import types
import pathlib


NO_WEIGHT_FOUND = types.SimpleNamespace(
    silent='Silent',
    exception='Exception',
    verbose='Verbose'
)

def path2url(file_path :pathlib.Path, base_url: str, base_dir: pathlib.Path) -> str:
    if file_path.name == '_index.md':
        file_path = file_path.parent
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    if file_path.suffix:
        return base_url + file_path.as_posix()[len(str(base_dir)):-len(file_path.suffix)]
    return base_url + file_path.as_posix()[len(str(base_dir)):]


def url2path(file_url: str, base_dir: pathlib.Path) -> pathlib.Path:
    file_url = file_url.split('/#')[0]
    file_path = base_dir.joinpath('/'.join(file_url.split('/')[3:]))
    if file_path.with_suffix(suffix='.md').exists():
        return file_path.with_suffix(suffix='.md')
    elif file_path.with_suffix(suffix='.webp').exists():
        return file_path.with_suffix(suffix='.webp')
    return file_path.joinpath('_index.md')


def get_linked_file_path(path_link: str, base_dir: pathlib.Path) -> pathlib.Path | None:
    file_relative_path = path_link[1:].split('/#')[0].split('#')[0]
    if file_relative_path.endswith('/'):
        file_relative_path = file_relative_path[:-1]
    img_abs_file_path = base_dir.parent / 'static' / file_relative_path
    if img_abs_file_path.exists():
        return img_abs_file_path
    index_abs_file_path = base_dir.joinpath(file_relative_path).joinpath('_index.md')
    if index_abs_file_path.exists():
        return index_abs_file_path
    md_abs_file_path = base_dir.joinpath(f'{file_relative_path}.md')
    if md_abs_file_path.exists():
        return md_abs_file_path
    return None


def get_page_title(file_contents: str) -> str:
    return file_contents.split('title: "').pop().split('"')[0].strip()


def get_page_weight(file_contents: str, no_weigh_found: int=NO_WEIGHT_FOUND.verbose) -> int:
    if 'weight:' in file_contents:
        return int(file_contents.split('weight:').pop().split('\n')[0].strip())
    if no_weigh_found == NO_WEIGHT_FOUND.silent:
            return -1
    if no_weigh_found == NO_WEIGHT_FOUND.verbose:
            print('Skipping file without "weight:"')
            return -1
    assert 'weight:' in file_contents, '"weight:" not found in file contents'


def is_empty(file_content: str) -> bool:
    if not file_content.strip():
        return True
    if '---' in file_content and not file_content.split('---')[2].strip():
        return True
    return False

def get_shortcodes_dict(base_dir: pathlib.Path) -> dict[str, str]:
    shortcodes_dict: dict[str, str] = dict()
    for each_shortcode_file_path in base_dir.rglob('*.html'):
        each_shortcode_file_contents = each_shortcode_file_path.read_text(encoding='utf8')
        if "`" in each_shortcode_file_contents:
          shortcodes_dict[each_shortcode_file_path.stem] = each_shortcode_file_contents.split("`")[1].strip()          
        else:          
          shortcodes_dict[each_shortcode_file_path.stem] = each_shortcode_file_contents

    return shortcodes_dict

def get_pages_dict(base_dir: pathlib.Path, shortcodes_dict: dict[str, str]) -> dict[pathlib.Path, str]:
    pages_dict: dict[pathlib.Path, str ] = dict()
    for each_md_file_path in base_dir.rglob('*.md'):
        each_md_file_contents = each_md_file_path.read_text(encoding='utf8')
        for each_math in re.findall('{{<.+>}}', each_md_file_contents):
            each_shortcode_name = each_math.split('<')[1].split('>')[0].strip()
            assert each_shortcode_name in shortcodes_dict, f'Shortcode "{each_shortcode_name}" not found in shortcodes_dict'
            each_md_file_contents = each_md_file_contents.replace(each_math, shortcodes_dict[each_shortcode_name])
        pages_dict[each_md_file_path] = each_md_file_contents
    return pages_dict


def open_in_editor(file_path: pathlib.Path):
    import os
    if file_path.suffix == '.webp':
        app_name = 'Microsoft Paint'
        app_exe = 'mspaint'
    else:
        app_name = 'Microsoft Visual Studio Code'
        app_exe = r'code'
    print(f'Opening "{file_path}" in {app_name}...')
    os.system(f'start {app_exe} {file_path}')


def open_in_browser(file_path: pathlib.Path | str):
    import webbrowser
    print('Opening in browser')
    if pathlib.Path(file_path).is_file():
        import os
        os.system(f'start msedge file://{pathlib.Path(file_path).as_posix()}')
    else:
        webbrowser.open(url=str(file_path))
