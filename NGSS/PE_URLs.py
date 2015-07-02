from lxml import html
import requests

base_url = 'http://www.nextgenscience.org'
page = requests.get(base_url+'/search-standards-dci')
tree = html.fromstring(page.text)

# Build list of relative URLs
pe_urls = tree.xpath('//table[@class="standard-table"]//td//a/@href')

# Sort the URLs stably by grade level by 2nd character in string:
def grade_level(url):
    # url[1] is 2nd character, 1st after /
    if url[1:4]=='k-2': return '3' # Stable sorting will put this before 3rd grade
    if url[1]=='k': return '0'
    if url[1:3]=='ms': return '6'
    if url[1:3]=='hs': return '9'
    return url[1]
pe_urls = sorted(pe_urls, key=grade_level)

# Add base URLs to get full URLs
pe_urls = list(map(lambda x: base_url+x, pe_urls))

# Show our results
for url in pe_urls:
    print(url)
