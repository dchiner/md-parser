import bs4
import argparse
import requests

SRC_URL = 0
DST_URL = 1
ERROR_BANNER = '\n' + '#' * 100 + '\n'

parser = argparse.ArgumentParser(
    prog='myLinkChecker.py',
    description='check all links in an online HTML site and ensures there are no broken links',
)
parser.add_argument(
    '-u',
    '--url',
     required=True,
    help='check links starting from URL'
)
args = parser.parse_args()
assert args.url.startswith('https://'), f'{ERROR_BANNER}URL must start with "https://"'

links_to_parse = {('START', args.url)}
parsed_urls = set()  

while links_to_parse:
    each_link = links_to_parse.pop()
    if each_link[DST_URL] in parsed_urls:
        continue
    parsed_urls.add(each_link[DST_URL])
    if each_link[DST_URL].startswith('mailto:'):
         continue
    try:
        response = requests.get(url=each_link[DST_URL], timeout=10)
        assert response.status_code == 200, f'{ERROR_BANNER}Error accessing "{each_link[DST_URL]}" from "{each_link[SRC_URL]}":\n{response.text}'
    except requests.exceptions.RequestException as e:
            print(f'{ERROR_BANNER}Exception accessing "{each_link[DST_URL]}" from "{each_link[SRC_URL]}":\n{e}')
            quit()
    each_page_soup = bs4.BeautifulSoup(markup=response.text, features='html.parser')
    for each_url in each_page_soup.find_all('a', href=True):
        if each_url['href'].startswith('https') and not each_url['href'].startswith(args.url):
              print('Skipping external link:', each_url['href'])
              continue
        assert not each_url['href'].startswith('http://'), f'{ERROR_BANNER}HTTP link "{each_link[DST_URL]}" in "{each_link[SRC_URL]}"'
        if each_url['href'].startswith('/'):
             each_new_dst_url = args.url + '/' + each_url['href']
        elif each_link[DST_URL].endswith('.html') or each_link[DST_URL].endswith('.htm'):
             each_new_dst_url = '/'.join(each_link[DST_URL].split('/')[:-1]) + '/'+ each_url['href']
        else:
             each_new_dst_url = each_link[DST_URL] + '/' + each_url['href']
        each_new_dst_url = each_new_dst_url.replace('//', '/').replace(':/', '://')
        print(each_link[DST_URL], '->', each_new_dst_url)
        links_to_parse.add((each_link[DST_URL], each_new_dst_url))