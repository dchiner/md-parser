import easygui # type: ignore

input_str = str(easygui.textbox(title='Parse pyLinkValidator output', msg='Paste the command output')).strip() #type: ignore
if input_str in ["", "None"]:
    quit()
broken_links :set[str]= set()
for each_line in input_str.split('\n'):
    each_line = each_line.strip()
    if each_line.startswith('not found'):
        broken_links.add(each_line)
        continue
    if not each_line.startswith('error'):
        continue
    if '#12' in each_line:
        continue
    if '#11' in each_line:
        continue
    broken_links.add(each_line)
if not easygui.ccbox(title='Broken links', msg='\n'.join(broken_links), choices=['Parse another', 'Close']): # type: ignore
    quit()