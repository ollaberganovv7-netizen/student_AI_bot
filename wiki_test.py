import urllib.request, json
url = "https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&titles=Shavkat_Mirziyoyev&pithumbsize=800&format=json"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    pages = data['query']['pages']
    for page_id in pages:
        print(pages[page_id]['thumbnail']['source'])
