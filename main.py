from requests_html import HTMLSession

session = HTMLSession()

url = "https://us.supreme.com/collections/all"

r = session.get(url)

r.html.render(sleep=1, keep_page=True, scrolldown=1)

items = r.html.find("ul.collection-ul > li > a")

for item in items:
    garment = {
        'title': item.attrs['href'],
        'link': item.attrs['data-cy-title']
    }
    print(garment)


