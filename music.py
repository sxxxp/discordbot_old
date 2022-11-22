#import pymysql
import random
import discord
import datetime
from discord.ext import tasks
from discord import app_commands, Interaction, ui, ButtonStyle
import asyncio
import youtube_dl
import requests
import os
from enum import Enum
from bs4 import BeautifulSoup


GUILD_ID = '1012635532829921291'
youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'music/%(id)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    # bind to ipv4 since ipv6 addresses cause issues sometimes
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'options': '-vn',
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
musicid = 0


class MyClient(discord.Client):
    async def on_ready(self):
        await self.wait_until_ready()
        await tree.sync(guild=discord.Object(id=GUILD_ID))
        await client.change_presence(status=discord.Status.online, activity=discord.Game("노래"))
        print(f"{self.user} 에 로그인하였습니다!")
        self.quit_channel.start

    @tasks.loop(hours=1)
    async def quit_channel(self):
        voice_client: discord.VoiceClient = discord.utils.get(
            client.voice_clients, guild=GUILD_ID)
        if len(queue[GUILD_ID]) == 0:
            await voice_client.disconnect()

    async def on_message(self, message: discord.Message):
        pass


intents = discord.Intents.all()
client = MyClient(intents=intents)
tree = app_commands.CommandTree(client)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=False, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

    @classmethod
    async def test(cls, data):
        return cls(discord.FFmpegPCMAudio(data['url'], **ffmpeg_options), data=data)


queue = {}


def nextsong(interaction: Interaction, error):
    if error:
        print(error)
    guild = str(interaction.guild.id)
    voice_client: discord.VoiceClient = discord.utils.get(
        client.voice_clients, guild=interaction.guild)
    if len(queue[guild]) > 0:
        queue[guild].pop(0)
    if not voice_client is None:
        voice_client.stop()
    if not len(queue[guild]) == 0:
        voice_client: discord.VoiceClient = discord.utils.get(
            client.voice_clients, guild=interaction.guild)
        voice_client.play(queue[guild][0][0],
                          after=lambda e: nextsong(interaction, e))


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


@tree.command(guild=discord.Object(id=GUILD_ID), name="quit", description='퇴근시키기')
async def musicquit(interaction: Interaction):
    voice_client: discord.VoiceClient = discord.utils.get(
        client.voice_clients, guild=interaction.guild)
    await voice_client.disconnect()
    await interaction.response.send_message(f"{interaction.user.voice.channel.name}채널에서 나왔어요!")
    await asyncio.sleep(7)
    await interaction.delete_original_response()


@tree.command(guild=discord.Object(id=GUILD_ID), name="queue", description="노래 리스트")
async def queuelist(interaction: Interaction):
    guild = str(interaction.guild.id)
    try:
        queue[guild]
    except KeyError:
        queue[guild] = []
    if len(queue[guild]) == 0:
        return await interaction.response.send_message("음악이 없어요!", ephemeral=True)
    global page
    page = 1

    def em():
        embed = discord.Embed(title="노래 리스트")
        for i in range((page-1)*10, page*10):
            if len(queue[guild]) > i:
                embed.add_field(
                    name=f"{i+1}. {queue[guild][i][0].title} ({queue[guild][i][1]}) `{queue[guild][i][2]}`", value="\u200b", inline=False)
        embed.set_footer(text=f"Page : {page}")
        embed.set_thumbnail(url=queue[guild][0][0].data['thumbnails']
                            [-1]['url'] if len(queue[guild]) > 0 else None)
        return embed

    def vi():
        view = ui.View(timeout=None)
        undo = ui.Button(style=ButtonStyle.green, label="이전으로",
                         disabled=(True if page == 1 else False))
        next = ui.Button(style=ButtonStyle.green, label="다음으로", disabled=(
            True if len(queue[guild]) <= page*10 else False))
        refresh = ui.Button(style=ButtonStyle.red, label="새로고침")
        view.add_item(undo)
        view.add_item(next)
        view.add_item(refresh)
        refresh.callback = refresh_callback
        undo.callback = undo_callback
        next.callback = next_callback
        return view

    async def refresh_callback(interaction: Interaction):
        global page
        await interaction.response.edit_message(embed=em(), view=vi())

    async def undo_callback(interaction: Interaction):
        global page
        page -= 1
        await interaction.response.edit_message(embed=em(), view=vi())

    async def next_callback(interaction: Interaction):
        global page
        page += 1
        await interaction.response.edit_message(embed=em(), view=vi())
    await interaction.response.send_message(embed=em(), view=vi())


@tree.command(guild=discord.Object(id=GUILD_ID), name="join", description="봇 초대")
async def joinmusic(interaction: Interaction):
    voice_client: discord.VoiceClient = discord.utils.get(
        client.voice_clients, guild=interaction.guild)
    if interaction.user.voice.channel is None:
        return await interaction.response.send_message("아무채널에도 들어가있지 않아요!", ephemeral=True)
    if voice_client is None and interaction.user.voice is not None:
        await interaction.user.voice.channel.connect()
        voice_client: discord.VoiceClient = discord.utils.get(
            client.voice_clients, guild=interaction.guild)
        return await interaction.response.send_message(f"{interaction.user.voice.channel.name}채널 참가함!", ephemeral=True)
    if voice_client.channel != interaction.user.voice.channel and interaction.user.voice.channel is not None:
        await voice_client.disconnect()
        await interaction.user.voice.channel.connect()
        return await interaction.response.send_message(f"{interaction.user.voice.channel.name}채널 참가함!", ephemeral=True)


@tree.command(guild=discord.Object(id=GUILD_ID), name="play", description="노래 시작")
async def playmusic(interaction: Interaction, url_title: str, 먼저틀기: bool = False):
    await interaction.response.send_message("노래를 찾고있어요!!")
    guild = str(interaction.guild.id)
    try:
        queue[guild]
    except KeyError:
        queue[guild] = []
    if interaction.user.voice is None:
        await interaction.edit_original_response(content="아무 채널에도 들어가있지 않아요.")
    else:
        voice_client: discord.VoiceClient = discord.utils.get(
            client.voice_clients, guild=interaction.guild)
        if voice_client == None:
            await interaction.user.voice.channel.connect()
            voice_client: discord.VoiceClient = discord.utils.get(
                client.voice_clients, guild=interaction.guild)
        with ytdl:
            loop = False
            loop = loop or asyncio.get_event_loop()
            global data
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch6:{url_title}", download=False))
            if not data['entries']:
                player = await YTDLSource.from_url(url_title, loop=None)
                if not player:
                    await interaction.edit_original_response(content="노래를 찾지 못했어요")
                    await asyncio.sleep(7)
                    return await interaction.delete_original_response()
                else:
                    t = datetime.timedelta(seconds=player.data['duration'])
                    if 먼저틀기 and len(queue[guild]) > 1:
                        queue[guild].insert(1, (player, t, interaction.user))
                    else:
                        # https://www.youtube.com/watch?v=Erkp04Sva4Q&list=PLOX-SZzyjidAJtecl2yAo9m47OUS3NBdF&index=14&ab_channel=memories
                        queue[guild].append((player, t, interaction.user))
                    if not voice_client.is_playing():
                        value = "재생중!!"
                        voice_client.play(
                            player, after=lambda e: nextsong(interaction, e))
                    else:
                        value = "재생목록 추가됨!!"
                    embed = discord.Embed(
                        title=f"{player.title} {value} ({t})")
                    embed.set_image(url=player.data['thumbnails'][-1]['url'])
                    await interaction.edit_original_response(content="", embed=embed)
                    await asyncio.sleep(7)
                    return await interaction.delete_original_response()
        embed = discord.Embed(title=f'노래 검색어:{url_title}')
        view = ui.View(timeout=None)
        # async def button(interaction:Interaction):
        #  pass

        async def button1(interaction: Interaction):
            global data
            data = data['entries'][0]
            await playing(interaction, await YTDLSource.test(data))

        async def button2(interaction: Interaction):
            global data
            data = data['entries'][1]
            await playing(interaction, await YTDLSource.test(data))

        async def button3(interaction: Interaction):
            global data
            data = data['entries'][2]
            await playing(interaction, await YTDLSource.test(data))

        async def button4(interaction: Interaction):
            global data
            data = data['entries'][3]
            await playing(interaction, await YTDLSource.test(data))

        async def button5(interaction: Interaction):
            global data
            data = data['entries'][4]
            await playing(interaction, await YTDLSource.test(data))

        async def button6(interaction: Interaction):
            global data
            data = data['entries'][5]
            await playing(interaction, await YTDLSource.test(data))

        async def cancel_callback(interaction: Interaction):
            await interaction.response.edit_message(content="취소되었습니다.", view=None, embed=None)
            await asyncio.sleep(7)
            await interaction.delete_original_response()
        for idx, music in enumerate(data['entries']):
            embed.add_field(
                name=f"**{idx+1}. {music['title']}** ({datetime.timedelta(seconds=music['duration'])})", value='\u200b', inline=False)
            # b=ui.Button(label=f'{idx+1}',style=ButtonStyle.green,custom_id=f'{idx}',row=(idx)//3)
            # view.add_item(b)
        b1 = ui.Button(label='1', style=ButtonStyle.green, row=0)
        b2 = ui.Button(label='2', style=ButtonStyle.green, row=0)
        b3 = ui.Button(label='3', style=ButtonStyle.green, row=0)
        b4 = ui.Button(label='4', style=ButtonStyle.green, row=1)
        b5 = ui.Button(label='5', style=ButtonStyle.green, row=1)
        b6 = ui.Button(label='6', style=ButtonStyle.green, row=1)
        view.add_item(b1)
        view.add_item(b2)
        view.add_item(b3)
        view.add_item(b4)
        view.add_item(b5)
        view.add_item(b6)
        b1.callback = button1
        b2.callback = button2
        b3.callback = button3
        b4.callback = button4
        b5.callback = button5
        b6.callback = button6
        cancel = ui.Button(label="cancel", style=ButtonStyle.red, row=2)
        view.add_item(cancel)
        cancel.callback = cancel_callback
        await interaction.edit_original_response(content="", embed=embed, view=view)

        async def playing(interaction: Interaction, source: YTDLSource):
            t = datetime.timedelta(seconds=source.data['duration'])
            if 먼저틀기 and len(queue[guild]) > 1:
                queue[guild].insert(1, (source, t, interaction.user))
            else:
                # https://www.youtube.com/watch?v=Erkp04Sva4Q&list=PLOX-SZzyjidAJtecl2yAo9m47OUS3NBdF&index=14&ab_channel=memories
                queue[guild].append((source, t, interaction.user))
            if not voice_client.is_playing():
                value = "재생중!!"
                voice_client.play(
                    source, after=lambda e: nextsong(interaction, e))
            else:
                value = "재생목록 추가됨!!"
            embed = discord.Embed(title=f"{source.title} {value} ({t})")
            embed.set_image(url=source.data['thumbnails'][-1]['url'])
            await interaction.response.edit_message(content="", embed=embed, view=None)
            await asyncio.sleep(7)
            return await interaction.delete_original_response()


@tree.command(guild=discord.Object(id=GUILD_ID), name="shuffle", description="노래 셔플")
async def shfflemusic(interaction: Interaction):
    global queue
    guild = str(interaction.guild.id)
    first = queue[guild][0]
    random.shuffle(queue[guild])
    for i in range(len(queue[guild])):
        if queue[guild][i] == first:
            del queue[guild][i]
            break
    queue[guild].insert(0, first)
    await interaction.response.send_message("음악이 셔플되었습니다.")
    await asyncio.sleep(7)
    await interaction.delete_original_response()


@tree.command(guild=discord.Object(id=GUILD_ID), name="indexskip", description="순서 삭제")
async def indexskipmusic(interaction: Interaction, 시작: int, 끝: int):
    global queue
    guild = str(interaction.guild.id)
    del queue[guild][시작-1:끝]
    await interaction.response.send_message(f"{시작}번째부터 {끝}번째 노래가 삭제되었습니다.")
    await asyncio.sleep(7)
    await interaction.delete_original_response()


@tree.command(guild=discord.Object(id=GUILD_ID), name="skip", description="노래 스킵")
async def skipmusic(interaction: Interaction, 갯수: int = 1):
    global queue
    guild = str(interaction.guild.id)
    if 갯수 > len(queue[guild]):
        갯수 = len(queue[guild])
    queue[guild] = queue[guild][갯수-1:len(queue[guild])]
    await interaction.response.send_message(f"{갯수}개의 음악이 삭제되었습니다.")
    voice_client: discord.VoiceClient = discord.utils.get(
        client.voice_clients, guild=interaction.guild)
    voice_client.stop()
    await asyncio.sleep(7)
    await interaction.delete_original_response()
client.run(os.environ['token'])
