import urllib.request
url = 'https://upload.wikimedia.org/wikipedia/commons/e/ea/Shavkat_Mirziyoyev_portrait.jpg'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    with open('webapp/images/president.jpg', 'wb') as out_file:
        out_file.write(response.read())
print('Downloaded successfully')
