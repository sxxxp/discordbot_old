from bs4 import BeautifulSoup
import requests
import time
import json
BASE_URL = "https://maplestory.nexon.com"
RANKING_USER_DATA_SELECTOR = "table.rank_table > tbody > tr.search_com_chk > td"
RANKING_USER_UNION_SELECTOR = "tr.search_com_chk > td"

닉네임 = "양다래새"
url = f'{BASE_URL}/N23Ranking/World/Total?c={닉네임}&w=0'
res = requests.get(url)
soup = BeautifulSoup(res.text, 'html.parser')
data = soup.select(RANKING_USER_DATA_SELECTOR)
if not data:
    url = f'{BASE_URL}/N23Ranking/World/Total?c={닉네임}&w=254'
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    data = soup.select(RANKING_USER_DATA_SELECTOR)
# if not data:
#     return await interaction.edit_original_response(content="유저를 찾을 수 없어요!")
level = data[2].get_text()
exp = data[3].get_text().replace(",", '')
server = data[1].select_one("dl > dt > a > img")['src']
job = data[1].select_one("dl > dd").get_text().split("/")[1]
ingido = data[4].get_text()
guild = data[5].get_text()
img = data[1].select_one("span.char_img > img")['src']
compare_level = int(level.replace("Lv.", ""))
union_url = f'{BASE_URL}/N23Ranking/World/Union?c={닉네임}&w=0'
res = requests.get(union_url)
soup = BeautifulSoup(res.text, 'html.parser')
union = soup.select(RANKING_USER_UNION_SELECTOR)[2].get_text()
if not union:
    union = "대표캐릭터가 아닙니다."
req = EXP_DATA[str(compare_level)]
percent = round(int(exp)/req*100, 3)
