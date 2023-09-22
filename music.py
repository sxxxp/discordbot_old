import pymysql
import discord
from discord.ext import tasks
from discord import app_commands, Interaction, ui, ButtonStyle
import asyncio
import requests
import os
import json
import io
import datetime
import random
from enum import Enum
from bs4 import BeautifulSoup
import re
# import dotenv
BASE_URL = "https://maplestory.nexon.com"
RANKING_USER_DATA_SELECTOR = "table.rank_table > tbody > tr.search_com_chk > td"
RANKING_USER_UNION_SELECTOR = "tr.search_com_chk > td"


def getJson(url: str):
    '''
    JSON 구하기
    -----------
    - url: JSON 파일 주소

    - ex) getJson('./json/util.json')

    `return 파싱된 JSON 파일`
    '''
    file = open(url, 'r', encoding="utf-8")
    data: dict = json.load(file)
    return data


# dotenv.load_dotenv()
con = pymysql.connect(host=os.environ['host'], port=int(os.environ['port']), user="root",
                      database="guildDatabase", passwd=os.environ['password'], charset='utf8', connect_timeout=120)
cur = con.cursor()
cur.execute("SELECT id FROM whitelist")
whitelist = list(cur.fetchall())
for i in range(len(whitelist)):
    whitelist[i] = whitelist[i][0]
print(whitelist)
sunday_channel = {}
cur.execute("SELECT guild,channel FROM sunday_channel")
data = list(cur.fetchall())
for key, value in data:
    sunday_channel[key] = value
print(sunday_channel)
GUILD_ID = '934824600498483220'
KST = datetime.timezone(datetime.timedelta(hours=9))
EXP_DATA = getJson("level.json")


class StarForceEvent(Enum):
    없음 = 0
    십오십육 = 1
    삼십퍼할인 = 2
    샤타포스 = 3


class MyClient(discord.Client):
    @tasks.loop(hours=1)
    async def reset_connect(self):
        cur = con.cursor()
        cur.execute("SELECT * FROM whitelist")
        cur.close()

    async def sunday_maple(self):
        print("썬데이 루프")
        print(sunday_channel)
        if not datetime.datetime.today().weekday() == 4:
            return
        url = 'https://maplestory.nexon.com/News/Event/Ongoing'
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        events = soup.select('dl dd p a')
        sunday_url = ""
        for event in events:
            if "썬데이" in event.getText().split(" "):
                sunday_url = url+"/"+event['href'].split("/")[-1]
                break
        if not sunday_url:
            for key, value in sunday_channel.items():
                channel = self.get_channel(int(value))
                if channel:
                    await channel.send("썬데이를 찾지 못했어요...")
                else:
                    del sunday_channel[key]
                    cur.execute(
                        "DELETE FROM sunday_channel WHERE guild = %s", key)
                    con.commit()
            await asyncio.sleep(1800)
            self.sunday_count += 1
            if self.sunday_count <= 2:
                await self.sunday_maple()
            return
        res = requests.get(sunday_url)
        soup = BeautifulSoup(res.text, 'html.parser')
        img_soup = soup.select(".new_board_con div div img")
        srcs = [img['src'] for img in img_soup]
        imgs = [requests.get(src) for src in srcs]
        for guild, channel in sunday_channel.items():
            image_files = []
            for idx, img in enumerate(imgs):
                if img.status_code == 200:
                    image_binary = io.BytesIO(img.content)
                    image_files.append(discord.File(
                        image_binary, filename=f"sunday{idx}.jpg"))
            guildChannel = self.get_channel(int(channel))
            if guildChannel:
                await guildChannel.send(content=f"[이벤트 링크]({sunday_url})", files=image_files)
            else:
                del sunday_channel[guild]
                cur.execute(
                    "DELETE FROM sunday_channel WHERE guild = %s", guild)
                con.commit()

    async def sunday_maple_channel(self, guild: int, id: int):
        print("썬데이 루프")
        if not datetime.datetime.today().weekday() == 4:
            return
        url = 'https://maplestory.nexon.com/News/Event/Ongoing'
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        events = soup.select('dl dd p a')
        sunday_url = ""
        for event in events:
            if "썬데이" in event.getText().split(" "):
                sunday_url = url+"/"+event['href'].split("/")[-1]
                break
        if not sunday_url:
            channel = self.get_channel(int(id))
            if channel:
                await channel.send("썬데이를 찾지 못했어요...")
            else:
                del sunday_channel[guild]
                cur.execute(
                    "DELETE FROM sunday_channel WHERE guild = %s", guild)
                con.commit()
            await asyncio.sleep(1800)
            await self.sunday_maple_channel(guild, id)
        res = requests.get(sunday_url)
        soup = BeautifulSoup(res.text, 'html.parser')
        img_soup = soup.select(".new_board_con div div img")
        srcs = [img['src'] for img in img_soup]
        imgs = [requests.get(src) for src in srcs]
        image_files = []
        for idx, img in enumerate(imgs):
            if img.status_code == 200:
                image_binary = io.BytesIO(img.content)
                image_files.append(discord.File(
                    image_binary, filename=f"sunday{idx}.jpg"))
        guildChannel = self.get_channel(int(id))
        if guildChannel:
            await guildChannel.send(content=f"[이벤트 링크]({sunday_url})", files=image_files)
        else:
            del sunday_channel[guild]
            cur.execute(
                "DELETE FROM sunday_channel WHERE guild = %s", key)
            con.commit()

    @tasks.loop(time=datetime.time(hour=10, minute=10, tzinfo=KST))
    async def sunday_maple_loop(self):
        self.sunday_count = 0
        await self.sunday_maple()

    async def on_ready(self):
        await self.wait_until_ready()
        await client.change_presence(status=discord.Status.online, activity=discord.Game("노래"))
        await tree.sync()
        print(datetime.datetime.now())
        print(f"{self.user} 에 로그인하였습니다!")
        self.reset_connect.start()
        self.sunday_maple_loop.start()

    async def on_error(self, event_method: str, /, *args, **kwargs) -> None:
        print(args)
        return await super().on_error(event_method, *args, **kwargs)

    # async def on_message(self, message: discord.Message):
    #     if message.author == self.user:
    #         return False
    #     emoji = "".join(re.compile("[:a-zA-Z]").findall(message.content))
    #     r = re.sub("[^a-zA-Z]", "", message.content).strip()
    #     if emoji == f":{r}:":
    #         guild = message.author.guild
    #         emoji_id = message.content.split(":")[2]
    #         emoji_id = emoji_id.replace(">", "")
    #         guild_emoji = discord.Client.get_emoji(self, int(emoji_id))
    #         guild_emoji = discord.utils.get(guild.emojis, id=int(emoji_id))
    #         if guild_emoji:
    #             def is_user(m: discord.Message):
    #                 return True if m.author == message.author else False
    #             embed = discord.Embed(color=message.author.color)
    #             embed.set_author(name=message.author.display_name,
    #                              icon_url=message.author.avatar)
    #             embed.set_image(url=guild_emoji.url)
    #             await message.channel.purge(limit=1, check=is_user)
    #             await message.channel.send(embed=embed)


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
    def __init__(self, messo: float, level: int, now: int, interaction: Interaction, event: StarForceEvent):
        messo *= 100000000
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
        self.chance = 0

        self.breakNum = 0
        self.first = messo
        self.best = [0, 0]
        self.log = []
        self.start = now

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
            value = (1000+(self.level**3)*(self.now+1)/25)
        elif self.now == 10:
            value = (1000+(self.level**3)*((self.now+1)**2.7)/400)
        elif self.now == 11:
            value = (1000+(self.level**3)*((self.now+1)**2.7)/220)
        elif self.now == 12:
            value = (1000+(self.level**3)*((self.now+1)**2.7)/150)
        elif self.now == 13:
            value = (1000+(self.level**3)*((self.now+1)**2.7)/110)
        elif self.now == 14:
            value = (1000+(self.level**3)*((self.now+1)**2.7)/75)
        elif self.now >= 15:
            value = (1000+(self.level**3)*((self.now+1)**2.7)/200)
        if self.siposipuk and self.now == 15:
            pass
        elif self.preventBreak and self.now <= 16 and self.now >= 15 and self.chance != 2:
            value *= 2
        if self.discount:
            value *= 0.7
        value = round(value, -2)
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
        return percent

    def embed(self):
        money = self.price()
        percent = self.probabilites()
        embed = discord.Embed(
            title=f"{self.user.display_name}님의 스타포스 시뮬레이터")
        embed.add_field(name=f"{self.now} > {self.now+1} 강화",
                        value="\u200b", inline=False)
        embed.add_field(
            name=("★☆찬스타임☆★" if self.chance == 2 else ""), value=f"```성공 : {round(percent[0]*100,2)}%\n실패 : {round((1-(percent[0]+percent[1]))*100,2)}%\n파괴 : {round(percent[1]*100,2)}%\n강화 비용 : {format(int(money),',')}메소```", inline=False)
        embed.add_field(
            name="\u200b", value=f"```정보:\n아이템 레벨: {self.level}\n보유 메소 : {round(self.messo/100000000,4)}억\n사용 메소 : {round((self.first-self.messo)/100000000,4)}억\n아이템 파괴 개수 : {self.breakNum}개\n적용 중인 이벤트 : {self.event.name}```", inline=False)
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
            self.button()

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
                self.parent.chance = 0
                self.parent.now += 1
                if self.parent.now > self.parent.best[0]:
                    self.parent.best = [self.parent.now, self.parent.messo]
                text = "★★★★★★성공★★★★★★"
                color = 0x20DE07
            elif value == -1:
                if self.parent.now > 15 and self.parent.now != 20:
                    self.parent.now -= 1
                    self.parent.chance += 1
                text = "★★★실패★★★"
                color = 0xBE2E22
            else:
                self.parent.chance = 0
                self.parent.breakNum += 1
                self.parent.log.append([self.parent.messo, self.parent.now])
                self.parent.now = 12
                text = "★★★★★파괴★★★★★"
                color = 0x97BDE0
            embed = self.parent.embed()
            embed.color = color
            embed.add_field(name=text, value="\u200b", inline=False)
            await interaction.response.edit_message(content="", embed=embed, view=self.parent.mainView(self.parent))

        @ui.button(label="끝내기", row=3, style=ButtonStyle.red)
        async def end(self, interaction: Interaction, button: ui.Button):
            if not interaction.user.id == self.parent.user.id:
                return
            embed = discord.Embed(title="종료")
            embed.add_field(
                name="\u200b", value=f"```초기 메소 : {round(self.parent.first/100000000,4)}억\n사용 메소 : {round((self.parent.first-self.parent.messo)/100000000,4)}억\n남은 메소 : {round(self.parent.messo/100000000,4)}억\n시작 스타포스 : {self.parent.start}성 > {self.parent.now}성\n최고 달성 : {self.parent.best[0]}성 {round((self.parent.first-self.parent.best[1])/100000000,4)}억 사용```\n이벤트 : {self.parent.event.name}", inline=False)
            text = ''
            prev = self.parent.first
            for idx, data in enumerate(self.parent.log):
                money, current = data
                spend = prev - money
                prev -= spend
                text += f"{idx+1}번째 파괴 {round(spend/100000000,4)}억 사용 {current}성에서 파괴\n"
            if text:
                embed.add_field(name="파괴기록", value=f"```{text}```")
            await interaction.response.edit_message(content="", embed=embed, view=None)
            await asyncio.sleep(30)
            await interaction.delete_original_response()

        @ui.button(label="파방", emoji="🔨", row=2, style=ButtonStyle.red)
        async def preventBreak(self, interaction: Interaction, button: ui.Button):
            if not interaction.user.id == self.parent.user.id:
                return
            self.parent.preventBreak = not self.parent.preventBreak
            await self.parent.setup(interaction)

        @ui.button(label="스타캐치", emoji="💥", row=2, style=ButtonStyle.primary)
        async def starCatch(self, interaction: Interaction, button: ui.Button):
            if not interaction.user.id == self.parent.user.id:
                return
            self.parent.starCatch = not self.parent.starCatch
            await self.parent.setup(interaction)

    async def setup(self, interaction: Interaction):
        try:
            await interaction.response.edit_message(content="", embed=self.embed(), view=self.mainView(self))
        except discord.errors.InteractionResponded:
            await interaction.edit_original_response(content="", embed=self.embed(), view=self.mainView(self))

    async def validity(self):
        self.eventHandler()
        await self.interaction.response.send_message("준비중입니다.")
        await self.setup(self.interaction)


@tree.command(name="썬데이알림", description="썬데이 알림을 받을 채널을 선택할수 있어요")
async def Sunday_Setting(interaction: Interaction, 채널: discord.TextChannel = None):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("채널 변경할 권한이 없어요!")
    if not 채널:
        del sunday_channel[str(interaction.guild.id)]
        cur.execute("DELETE FROM sunday_channel WHERE guild = %s",
                    interaction.guild.id)
        con.commit()
        return await interaction.response.send_message("이제부터 선데이 알림을 받지 않아요.")
    cur.execute(
        "SELECT COUNT(*) FROM sunday_channel WHERE guild = %s", interaction.guild.id)
    check = cur.fetchone()[0]
    if check:
        sunday_channel[str(interaction.guild.id)] = str(채널.id)
        cur.execute("UPDATE sunday_channel SET channel = %s WHERE guild = %s",
                    (채널.id, interaction.guild.id))
        con.commit()
        return await interaction.response.send_message(f"알림 받을 채널이 {채널.mention}로 변경되었습니다.")
    else:
        sunday_channel[str(interaction.guild.id)] = str(채널.id)
        cur.execute("INSERT INTO sunday_channel(guild,channel) VALUES(%s,%s)",
                    (interaction.guild.id, 채널.id))
        con.commit()
        return await interaction.response.send_message(f"알림 받을 채널이 {채널.mention}로 설정되었습니다.")


@tree.command(name="썬데이강제", description="개발자명령어")
async def forcedSunday(interaction: Interaction):
    if interaction.user.id == 432066597591449600:
        await client.sunday_maple()


@tree.command(name="썬데이강제채널", description="개발자명령어")
async def forcedSundayChannel(interaction: Interaction, 채널: discord.TextChannel):
    if interaction.user.id == 432066597591449600:
        await client.sunday_maple_channel(채널.guild.id, 채널.id)


@tree.command(name="스타포스", description="스타포스 시뮬레이터를 굴릴 수 있습니다.")
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


@tree.command(name="길드검색", description='리부트 길드를 검색합니다.')
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


@tree.command(name="캐릭터검색", description='캐릭터를 검색합니다.')
async def search(interaction: Interaction, 닉네임: str):
    await interaction.response.send_message("유저를 찾고 있어요!")
    url = f'{BASE_URL}/N23Ranking/World/Total?c={닉네임}&w=0'
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    data = soup.select(RANKING_USER_DATA_SELECTOR)
    if not data:
        url = f'{BASE_URL}/N23Ranking/World/Total?c={닉네임}&w=254'
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        data = soup.select(RANKING_USER_DATA_SELECTOR)
    if not data:
        return await interaction.edit_original_response(content="유저를 찾을 수 없어요!")
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
    try:
        union = soup.select(RANKING_USER_UNION_SELECTOR)[2].get_text()
    except IndexError:
        union = 0
    if not union:
        union = "대표캐릭터가 아닙니다."
    else:
        union = "Lv."+str(union)
    req = EXP_DATA[str(compare_level)]
    percent = round(int(exp)/req*100, 3)
    embed = discord.Embed(title=f"{닉네임}({job.replace(' ','')})")
    server: str
    server = "http://"+server[8:]
    embed.set_author(name="서버", icon_url=server)
    img: str
    a = img[8:].split("/")
    a.remove("180")
    img = "http://"+'/'.join(a)
    print(server, img)
    embed.set_thumbnail(url=img)
    embed.add_field(name=f"{level}({percent}%)", value="\u200b")
    embed.add_field(name=f"인기도 {ingido}", value="\u200b")
    embed.add_field(name=f"길드 : {guild}", value="\u200b", inline=False)
    embed.add_field(name=f"유니온 : {union}", value="\u200b")
    embed.add_field(name=f"무릉은 준비중이에요...", value="\u200b")
    await interaction.edit_original_response(content="", embed=embed)

client.run(os.environ['token'])
