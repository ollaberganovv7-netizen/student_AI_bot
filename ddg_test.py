from duckduckgo_search import DDGS
with DDGS() as ddgs:
    results = ddgs.images('Shavkat Mirziyoyev official portrait president.uz', max_results=3)
    for r in results:
        print(r['image'])
