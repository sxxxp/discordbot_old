import pymysql
import discord
from discord.ext import tasks
from discord import app_commands, Interaction, ui, ButtonStyle
import asyncio
import requests
import os
import random
from enum import Enum
from bs4 import BeautifulSoup
import re

con = pymysql.connect(host=os.environ['host'], port=int(os.environ['port']), user="root",
                      database="guildDatabase", passwd=os.environ['password'], charset='utf8', connect_timeout=120)
cur = con.cursor()
cur.execute("SELECT id FROM whitelist")
whitelist = list(cur.fetchall())
for i in range(len(whitelist)):
    whitelist[i] = whitelist[i][0]
print(whitelist)
GUILD_ID = '934824600498483220'


class StarForceEvent(Enum):
    십오십육 = 1
    삼십퍼할인 = 2
    샤타포스 = 3


class MyClient(discord.Client):
    @tasks.loop(hours=1)
    async def reset_connect(self):
        cur = con.cursor()
        cur.execute("SELECT * FROM whitelist")
        cur.close()

    async def on_ready(self):
        await self.wait_until_ready()
        await client.change_presence(status=discord.Status.online, activity=discord.Game("노래"))
        await tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"{self.user} 에 로그인하였습니다!")
        self.reset_connect.start()

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return False
        emoji = "".join(re.compile("[:a-zA-Z]").findall(message.content))
        r = re.sub("[^a-zA-Z]", "", message.content).strip()
        if emoji == f":{r}:":
            # guild=message.author.guild
            emoji_id = message.content.split(":")[2]
            emoji_id = emoji_id.replace(">", "")
            guild_emoji = discord.Client.get_emoji(self, int(emoji_id))
            # guild_emoji=discord.utils.get(guild.emojis,id=int(emoji_id))
        if guild_emoji:
            def is_user(m: discord.Message):
                return True if m.author == message.author else False
            embed = discord.Embed(color=message.author.color)
            embed.set_author(name=message.author.display_name,
                             icon_url=message.author.avatar)
            embed.set_image(url=guild_emoji.url)
            await message.channel.purge(limit=1, check=is_user)
            await message.channel.send(embed=embed)


intents = discord.Intents.all()
client = MyClient(intents=intents)
tree = app_commands.CommandTree(client)

queue = {}


def checkSuccess(probabilities: list | tuple):
    random_number = random.uniform(0, 1)
    cumulative_probability = 0

    for i, prob in enumerate(probabilities):
        cumulative_probability += prob
        if random_number <= cumulative_probability:
            return i
    return -1


class Simulator:
    def __init__(self, messo: int, level: int, now: int, interaction: Interaction, event: StarForceEvent):
        self.user = interaction.user
        self.interaction = interaction
        self.messo = messo
        self.level = level
        self.now = now
        self.event = event
        self.discount = False
        self.siposipuk = False
        self.preventBreak = False
        self.starCatch = False
        self.breakNum = 0
        self.chance = 0

    def eventHandler(self):
        if self.event.value == 1:
            self.siposipuk = True
        if self.event.value == 2:
            self.discount = True
        if self.event.value == 3:
            self.siposipuk = True
            self.discount = True

    def price(self):
        value = 0
        if self.now <= 9:
            value = round(1000+(self.level**3)*(self.now+1)/25, -2)
        elif self.now == 10:
            value = round(1000+(self.level**3)*((self.now+1)**2.7)/400, -2)
        elif self.now == 11:
            value = round(1000+(self.level**3)*((self.now+1)**2.7)/220, -2)
        elif self.now == 12:
            value = round(1000+(self.level**3)*((self.now+1)**2.7)/150, -2)
        elif self.now == 13:
            value = round(1000+(self.level**3)*((self.now+1)**2.7)/110, -2)
        elif self.now == 14:
            value = round(1000+(self.level**3)*((self.now+1)**2.7)/75, -2)
        elif self.now >= 15:
            value = round(1000+(self.level**3)*((self.now+1)**2.7)/200, -2)
        if self.siposipuk and self.now == 15:
            pass
        elif self.preventBreak and self.now <= 16 and self.chance != 2:
            value *= 2
        if self.discount:
            value *= 0.7
        return value

    def probabilites(self):
        percent = []
        if self.now <= 2:
            percent = [(95-5*self.now)/100, 0]
        elif self.now >= 3 and self.now <= 14:
            percent = [(100-5*self.now)/100, 0]
        elif self.now <= 21:
            breakPercent = 0
            if self.now <= 17:
                breakPercent = 0.021
            elif self.now >= 18 and self.now <= 19:
                breakPercent = 0.028
            elif self.now >= 20 and self.now <= 21:
                breakPercent = 0.07
            if self.preventBreak and self.now <= 16:
                breakPercent = 0
            percent = [0.3, breakPercent]
        elif self.now == 22:
            percent = [0.03, 0.194]
        elif self.now == 23:
            percent = [0.02, 0.294]
        elif self.now == 24:
            percent = [0.01, 0.396]
        if self.starCatch:
            percent[0] *= 1.05
        if self.siposipuk:
            if self.now == 5 or self.now == 10 or self.now == 15:
                percent = [1, 0]
        if self.chance == 2:
            percent = [1, 0]
            self.chance = 0
        return percent

    def embed(self):
        money = self.price()
        percent = self.probabilites()
        embed = discord.Embed(
            title=f"{self.user.display_name}님의 스타포스 시뮬레이터", url=self.user.display_avatar)
        embed.add_field(name=f"{self.now} > {self.now+1} 강화",
                        value="\u200b", inline=False)
        embed.add_field(
            name="\u200b", value=f"```성공 : {round(percent[0]*100)}%\n실패 : {round((1-percent[0]+percent[1])*100)}\n파괴 : {round(percent[1]*100)}%\n강화 비용 : {money}메소```", inline=False)
        embed.add_field(
            name="\u200b", value=f"```정보:\n아이템 레벨: {self.level}\n보유 메소 : {round(self.messo/100000000,2)}억\n아이템 파괴 개수 : {self.breakNum}개\n적용 중인 이벤트 : {self.event.name}```", inline=False)
        embed.add_field(
            name=f"파방 : {'O' if self.preventBreak else 'X'}", value="\u200b", inline=False)
        embed.add_field(
            name=f"스타캐치 : {'O' if self.starCatch else 'X'}", value="\u200b", inline=False)
        embed.set_footer(text="파방 17성 이후 켜져있어도 적용 안됩니다.")
        return embed

    class mainView(ui.View):
        def __init__(self, parent: 'Simulator'):
            super().__init__(timeout=None)
            self.parent = parent

        def button(self):
            go_button = ui.Button(style=ButtonStyle.green, label="강화",
                                  disabled=self.parent.price() > self.parent.messo)
            go_button.callback = self.button_callback
            self.add_item(go_button)

        async def button_callback(self, interaction: Interaction):
            if not interaction.user.id == self.parent.user.id:
                return
            self.parent.messo -= self.parent.price()
            value = checkSuccess(self.parent.probabilites())
            if value == 0:
                self.parent.now += 1
            elif value == -1:
                if self.parent.now > 15 or self.parent.now != 20:
                    self.parent.now -= 1
                    self.parent.chance += 1
            else:
                self.parent.chance = 0
                self.parent.breakNum += 1
                self.parent.now = 12
            await self.parent.setup(interaction)

    async def setup(self, interaction: Interaction):
        try:
            await interaction.response.edit_message(embed=self.embed(), view=self.mainView(self))
        except discord.errors.InteractionResponded:
            await interaction.edit_original_response(embed=self.embed(), view=self.mainView(self))

    async def validity(self):
        self.eventHandler()
        await self.setup(self.interaction)


@tree.command(guild=discord.Object(id=GUILD_ID), name="스타포스", description="스타포스 시뮬레이터를 굴릴 수 있습니다.")
async def StarForceSimulator(interaction: Interaction, 시작별: int, 메소: int, 이벤트: StarForceEvent, 장비레벨: int):
    await Simulator(메소, 장비레벨, 시작별, interaction, 이벤트).validity()


@tree.command(guild=discord.Object(id=GUILD_ID), name="길드원정보검색", description="길드원의 정보에 문자열이 포함된 사람들을 불러옵니다.")
async def findGuildMateInfo(interaction: Interaction, 문자열: str):
    cur = con.cursor()
    cur.execute(f"SELECT name FROM info WHERE info LIKE '%{문자열}%'")
    names = cur.fetchall()
    global page
    page = 0

    def em():
        embed = discord.Embed(title=f"{문자열} 문자열이 포함된 길드원들")
        for i in range(page*24, (page+1)*24):
            if len(names) > i:
                embed.add_field(name=names[i][0], value='\u200b', inline=True)
        embed.set_footer(text=f"page {page+1}")
        return embed

    def vi():
        view = ui.View(timeout=None)
        undo = ui.Button(style=ButtonStyle.green, label="이전으로",
                         disabled=(True if page == 0 else False))
        next = ui.Button(style=ButtonStyle.green, label="다음으로", disabled=(
            True if len(names) <= (page+1)*24 else False))
        view.add_item(undo)
        view.add_item(next)
        undo.callback = undo_callback
        next.callback = next_callback
        return view

    async def undo_callback(interaction: Interaction):
        global page
        page -= 1
        await interaction.response.edit_message(embed=em(), view=vi())

    async def next_callback(interaction: Interaction):
        global page
        page += 1
        await interaction.response.edit_message(embed=em(), view=vi())

    await interaction.response.send_message(embed=em(), view=vi())


@tree.command(guild=discord.Object(id=GUILD_ID), name="권한보기", description="현재 권한을 가진 유저를 보여줍니다.")
async def findWhitelist(interaction: Interaction):
    embed = discord.Embed(title='현재 권한가진 사람들')
    for i in whitelist:
        embed.add_field(name=interaction.guild.get_member(
            int(i)).display_name, value="\u200b")
    await interaction.response.send_message(embed=embed)


@tree.command(guild=discord.Object(id=GUILD_ID), name="권한삭제", description="변경 권한을 삭제합니다.")
async def removeWhitelist(interaction: Interaction, 삭제할사람: discord.Member):
    if str(interaction.user.id) not in whitelist:
        return await interaction.response.send_message("권한이 없습니다.", ephemeral=True)
    cur = con.cursor()
    cur.execute("SELECT * FROM whitelist WHERE id = %s", 삭제할사람.id)
    if not cur.fetchone():
        return await interaction.response.send_message("이미 권한이 없습니다.", ephemeral=True)
    cur.execute("DELETE FROM whitelist WHERE id = %s", 삭제할사람.id)
    con.commit()
    whitelist.remove(str(삭제할사람.id))
    await interaction.response.send_message(f"{삭제할사람.display_name}님에게 권한이 삭제되었습니다.")


@tree.command(guild=discord.Object(id=GUILD_ID), name="권한추가", description="변경 권한을 추가합니다.")
async def addWhitelist(interaction: Interaction, 추가할사람: discord.Member):
    if str(interaction.user.id) not in whitelist:
        return await interaction.response.send_message("권한이 없습니다.", ephemeral=True)
    cur = con.cursor()
    cur.execute("SELECT * FROM whitelist WHERE id = %s", 추가할사람.id)
    if cur.fetchone():
        return await interaction.response.send_message("이미 권한이 있습니다.", ephemeral=True)
    cur.execute("INSERT INTO whitelist VALUES(%s)", 추가할사람.id)
    con.commit()
    whitelist.append(str(추가할사람.id))
    await interaction.response.send_message(f"{추가할사람.display_name}님에게 권한이 추가되었습니다.")


@tree.command(guild=discord.Object(id=GUILD_ID), name="길드원변경", description="예전 닉네임을 변경합니다.")
async def replaceGuildMate(interaction: Interaction, 예전닉네임: str, 현재닉네임: str):
    if str(interaction.user.id) not in whitelist:
        return await interaction.response.send_message("권한이 없습니다.", ephemeral=True)
    cur = con.cursor()
    cur.execute("SELECT * FROM info WHERE name = %s", 예전닉네임)
    if not cur.fetchone():
        return await interaction.response.send_message(f"{예전닉네임}님은 정보가 없습니다.")
    cur.execute("UPDATE info SET name = %s WHERE name = %s", (현재닉네임, 예전닉네임))
    con.commit()
    await interaction.response.send_message(f"{예전닉네임}님의 닉네임을 {현재닉네임}으로 변경했습니다.")


@tree.command(guild=discord.Object(id=GUILD_ID), name="길드원삭제", description="길드원 정보를 삭제합니다.")
async def removeGuildMate(interaction: Interaction, 길드원명: str):
    if str(interaction.user.id) not in whitelist:
        return await interaction.response.send_message("권한이 없습니다.", ephemeral=True)
    cur = con.cursor()
    cur.execute("SELECT * FROM info WHERE name = %s", 길드원명)
    if not cur.fetchone():
        return await interaction.response.send_message(f"{길드원명}님은 정보가 없습니다.")
    cur.execute("DELETE FROM info WHERE name = %s", 길드원명)
    con.commit()
    await interaction.response.send_message(f"성공적으로 {길드원명}님의 정보를 삭제했습니다.")


@tree.command(guild=discord.Object(id=GUILD_ID), name="길드원추가", description="길드원 정보를 추가합니다.")
async def addGuildMate(interaction: Interaction, 길드원명: str, 정보: str):
    if str(interaction.user.id) not in whitelist:
        return await interaction.response.send_message("권한이 없습니다.", ephemeral=True)
    cur = con.cursor()
    text = ""
    cur.execute("SELECT name FROM info WHERE name = %s", 길드원명)
    if cur.fetchone():
        cur.execute("UPDATE info SET info = %s WHERE name = %s", (정보, 길드원명))
        text = '수정'
    else:
        cur.execute("INSERT INTO info VALUES(%s,%s)", (길드원명, 정보))
        text = "추가"
    con.commit()
    await interaction.response.send_message(f"성공적으로 {길드원명}님의 정보를 {text}헀습니다.")


@tree.command(guild=discord.Object(id=GUILD_ID), name="길드원검색", description="길드원 정보를 검색합니다.")
async def searchGuildMate(interaction: Interaction, 길드원명: str):
    cur = con.cursor()
    cur.execute("SELECT * FROM info WHERE name = %s", 길드원명)
    info = cur.fetchone()
    if not info:
        return await interaction.response.send_message(f"{길드원명}님의 정보가 존재하지 않거나 삭제 되었습니다.", ephemeral=True)
    embed = discord.Embed(title=info[0])
    embed.add_field(name=info[1], value="\u200b")
    await interaction.response.send_message(embed=embed)


@tree.command(guild=discord.Object(id=GUILD_ID), name="길드검색", description='리부트 길드를 검색합니다.')
async def searchGuild(interaction: Interaction, 길드명: str):
    await interaction.response.send_message("길드를 찾고 있어요!")
    url = 'https://maple.gg/guild/reboot/'+길드명
    requests.get(url+'/sync')
    await asyncio.sleep(3)
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    check = soup.select_one('.d-inline-block.align-middle')
    if not check:
        master = soup.select_one('.text-grape-fruit.text-underline').text
        embed = discord.Embed(title=길드명)
        embed.add_field(name=f'마스터 : {master}', value="\u200b")
        await interaction.edit_original_response(content='', embed=embed)
    else:
        await interaction.edit_original_response(content='길드가 없습니다.')


@tree.command(guild=discord.Object(id=GUILD_ID), name="캐릭터검색", description='캐릭터를 검색합니다.')
async def search(interaction: Interaction, 닉네임: str):
    await interaction.response.send_message("유저를 찾고 있어요!")
    url = 'https://maple.gg/u/' + 닉네임
    requests.get(url+'/sync')
    await asyncio.sleep(2)
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    try:
        soup.select_one('.mb-3')['alt']
    except KeyError:
        level, job, ingido = soup.select('.user-summary-item')
        ingido.text[4:]
        guild = soup.select('.text-yellow.text-underline')
        character = soup.select(".character-image")
        moorong = soup.select(".user-summary-floor.font-weight-bold")
        cnt = 0
        seed_cnt = 0

        if len(moorong) == 1:
            cnt = 1
            seed = moorong[0].text
        elif len(moorong) == 2:

            seed = moorong[1].text
        if not moorong:
            cnt = 1
            seed_cnt = 1
            seed = ''
            moorong = '0'
        else:
            moorong = moorong[0].text.replace(" ", "")[:2]
        date = soup.select('.user-summary-date')
        union = soup.select(".user-summary-level")
        embed = discord.Embed(title=f"{닉네임}({job.text})")
        url = character[0]['src'].replace("https", "http")
        if not guild:
            guild = '없음'
        else:
            guild = guild[0].text
        union = '0' if not union else union[0].text
        if not seed:
            seed_cnt = 1
        embed.set_thumbnail(url=url)
        embed.add_field(name=f"레벨 : {level.text}", value='\u200b', inline=True)
        embed.add_field(
            name=f"인기도 : {ingido.text[4:]}", value='\u200b', inline=True)
        embed.add_field(
            name=f"길드 : {guild}", value='\u200b', inline=False)
        embed.add_field(
            name=f"무릉 : {moorong}층", value=date[0].text if moorong != '0' else '\u200b', inline=True)
        embed.add_field(
            name=f"유니온 : {union}", value=date[2-seed_cnt-cnt].text if union != '0' else '\u200b', inline=True)
        await interaction.edit_original_response(content="", embed=embed)
    else:
        await interaction.edit_original_response(content='유저가 없어요.')


client.run(os.environ['token'])
