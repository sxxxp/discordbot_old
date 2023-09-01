from bs4 import BeautifulSoup
import requests
import time
import json
exp_data_url = "https://namu.wiki/w/%EB%A9%94%EC%9D%B4%ED%94%8C%EC%8A%A4%ED%86%A0%EB%A6%AC/%EC%8B%9C%EC%8A%A4%ED%85%9C/%EA%B2%BD%ED%97%98%EC%B9%98"
res = requests.get(exp_data_url)
soup = BeautifulSoup(res.text, "html.parser")
newbie = soup.select("table")[1]
middle = soup.select("table")[2]
goinmoll = soup.select("table")[3]
data = {}
for i in range(1, 200):
    data[i] = int(''.join(newbie.select("tr")[i].select("td")[1].select_one(
        "div").find_all(string=True, recursive=False)).replace(",", ''))
for i in range(1, 60):
    a = ''.join(middle.select("tr")[i].select("td")[1].select_one(
        "div").find_all(string=True, recursive=False)).replace(",", '')
    print(i, a)
    data[i+199] = int(a)
for i in range(1, 40):
    data[i+259] = int(''.join(goinmoll.select("tr")[i].select("td")[1].select_one(
        "div").find_all(string=True, recursive=False)).replace(",", ''))
json_string = json.dumps(data, indent=4)
with open("level.json", "w") as json_file:
    json_file.write(json_string)
