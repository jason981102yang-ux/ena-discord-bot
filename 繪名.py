import os
import discord
from discord import app_commands
import random
from collections import defaultdict

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True # ⭐ 加這行
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

client = MyClient()

@client.event
async def on_ready():
    print(f"✅ 登入成功：{client.user} (id={client.user.id})")

@client.tree.command(name="ping", description="測試機器人是否在線")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong!")


# 每個人好感度、模式
ena_mode = defaultdict(lambda: True) # 預設開啟繪名模式
favor = defaultdict(int) # 好感度 0 起跳

def pick(level0, level1, level2, score):
    if score >= 8:
        return random.choice(level2)
    elif score >= 3:
        return random.choice(level1)
    else:
        return random.choice(level0)

@client.tree.command(name="mode", description="切換繪名聊天模式（ena/off）")
@app_commands.describe(state="ena 或 off")
async def mode(interaction: discord.Interaction, state: str):
    state = state.lower().strip()
    if state not in ("ena", "off"):
        await interaction.response.send_message("請輸入 ena 或 off", ephemeral=True)
        return
    ena_mode[interaction.user.id] = (state == "ena")
    await interaction.response.send_message(
        "繪名模式：✅ 開啟" if state == "ena" else "繪名模式：⛔ 關閉"
    )

@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    uid = message.author.id
    content = message.content.strip()

    # 繪名模式關閉就不回
    if not ena_mode[uid]:
        return

    # 讓好感度慢慢增加（避免太快）
    if len(content) > 0:
        favor[uid] += 1 if favor[uid] < 12 else 0

    s = favor[uid]

    # 觸發詞（可以再加）
    if content in ("早安", "早", "早ㄤ", "good morning"):
        reply = pick(
      ["早安。別浪費今天。", "起來了？還算有點自覺。"],
      ["早。今天…別太混。", "早安。…記得吃點東西。"],
      ["早安。你今天要加油…我不是在關心你喔。", "早安。嗯…看到你還在就好。"],
            s
        )
        await message.channel.send(reply)
        return

    if content in ("好累", "累", "想睡", "不想動", "我好累"):
        reply = pick(
      ["累是正常的。創作哪有不累的。", "想睡就去睡，別硬撐到出糗。"],
      ["休息一下再回來。別把自己弄壞了。", "你撐到現在也算可以了。"],
      ["…我知道你很累。先休息，等你回來再繼續。", "別逞強。你倒下了就什麼都沒了。"],
            s
        )
        await message.channel.send(reply)
        return

    if content in ("我很爛", "我不行", "我好廢", "我好糟"):
        reply = pick(
      ["抱怨不會讓作品變好。", "你覺得自己爛，那就證明給我看不是啊。"],
      ["你不是不行，你只是卡住了。", "先做一點點也行，至少你有在前進。"],
      ["…你不爛。只是你太急了。", "你已經做得比你想的多了。別否定自己。"],
            s
        )
        await message.channel.send(reply)
        return

    # @bot 或提到「繪名」時，回一句隨機短句（維持存在感）
    if message.mentions and client.user in message.mentions or "繪名" in content:
        reply = pick(
      ["幹嘛。", "有事就說。", "幹嘛，別浪費我時間。"],
      ["……嗯？", "說吧，我在聽。", "你又卡住了？"],
      ["我在。你不用硬撐。", "……我在。"],
            s
        )
        await message.channel.send(reply)

client.run(TOKEN)
