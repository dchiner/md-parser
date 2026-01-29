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
    elif file_path.with_suffix(suffix='.png').exists():
        return file_path.with_suffix(suffix='.png')
    return file_path.joinpath('_index.md')


def get_linked_file_path(path_link: str, base_dir: pathlib.Path) -> pathlib.Path | None:
    file_relative_path = path_link[1:].split('/#')[0].split('#')[0]
    if file_relative_path.endswith('/'):
        file_relative_path = file_relative_path[:-1]
    png_abs_path = base_dir.joinpath(file_relative_path)
    if png_abs_path.suffix == '.png' and png_abs_path.exists():
        return png_abs_path
    index_file_path = base_dir.joinpath(file_relative_path).joinpath('_index.md')
    if index_file_path.exists():
        return index_file_path
    md_file_path = base_dir.joinpath(f'{file_relative_path}.md')
    if md_file_path.exists():
        return md_file_path
    return None


def get_page_title(file_contents: str) -> str:
    return file_contents.split('title: "').pop().split('"')[0].strip()


def get_page_weight(file_contents: str, no_weigh_found: int=NO_WEIGHT_FOUND.verbose) -> int:
    if 'weight:' not in file_contents:
        if no_weigh_found == NO_WEIGHT_FOUND.silent:
            return -1
        if no_weigh_found == NO_WEIGHT_FOUND.verbose:
            print('Skipping file without "weight:"')
            return -1
        if no_weigh_found == NO_WEIGHT_FOUND.exception:
            assert 'weight:' in file_contents, '"weight:" not found in file contents'
    return int(file_contents.split('weight:').pop().split('\n')[0].strip())


def is_empty(file_content: str) -> bool:
    if not file_content.strip():
        return True
    if '---' in file_content and not file_content.split('---')[2].strip():
        return True
    return False


def get_pages_dict(base_dir: pathlib.Path) -> dict[pathlib.Path, str]:
    pages_dict: dict[pathlib.Path, str ] = dict()
    for each_md_file_path in pathlib.Path(base_dir).rglob('*.md'):
        pages_dict[each_md_file_path] = pathlib.Path(each_md_file_path).read_text(encoding='utf8')
    return pages_dict


def open_in_editor(file_path: pathlib.Path):
    import os
    if file_path.suffix == '.png':
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
