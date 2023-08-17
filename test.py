from bs4 import BeautifulSoup
import requests
import time


url = 'https://maplestory.nexon.com/News/Event/Closed'
res = requests.get(url)
soup = BeautifulSoup(res.text, 'html.parser')
print(soup)
time.sleep(2)
sunday_url = ''
events = soup.select('dl dd p a')
for event in events:
    if event.getText() == "썬데이 메이플":
        sunday_url = url+"/"+event['href'].split("/")[-1]
        break
if not sunday_url:
    print("못찾음")
    exit()
print(sunday_url)
time.sleep(4)
res = requests.get(sunday_url)
soup = BeautifulSoup(res.text, 'html.parser')
print(soup)

img = soup.select_one(".new_board_con div div img")
print(img)
