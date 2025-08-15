import http.client

conn = http.client.HTTPSConnection("stocktwits.p.rapidapi.com")

headers = {
    'x-rapidapi-key': "427c7faa7bmshac7c567f35f2667p1e47d6jsn83598eb75717",
    'x-rapidapi-host': "stocktwits.p.rapidapi.com"
}

conn.request("GET", "/streams/symbol/AAPL.json?limit=20", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))
print(res.status)