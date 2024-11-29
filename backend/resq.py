import bs4
import requests

url = 'https://www.taobao.com'
url_s = 'https://search.jd.com/Search?keyword=111&enc=utf-8&wq=111&pvid=990e162d4a6f4709b27dfd68435855c1'
response = requests.get(url_s)
soup = bs4.BeautifulSoup(response.text, 'html.parser')

with open('taobao.html', 'w', encoding='utf-8') as f:
    f.write(str(soup))