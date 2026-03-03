import os
import discord
from discord import app_commands
import random
from collections import defaultdict
import time
import re


TOKEN =  os.getenv("DISCORD_BOT_TOKEN")
class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True # ⭐ 加這行
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

def detect_style(text: str) -> str:

    t = text.strip()

    # 瑞希風：可愛語尾 / 顏文字 / 拉長音
    if re.search(r"(～|啦|欸|耶|好棒|超|♡|🥺|✨)", t):
        return "mizuki"
    # 真冬風：冷淡短句 / 很多省略號 / 極少情緒詞
    if re.search(r"(……|\.{3,})", t) or len(t) <= 4:
        return "mafuyu"
    # 彰人風：命令句 / 感嘆號 / 口氣衝
    if re.search(r"(快|給我|現在|立刻|!)", t):
        return "akito"
    return "normal"



client = MyClient()


def strip_mimic_prefix(text: str, pattern: str) -> str:

    return re.sub(pattern, "", text, count=1)



def favor_level(score: int) -> str:

    if score >= 8:

        return "high"

    elif score >= 3:

        return "mid"

    return "low"

@client.event
async def on_ready():
    print(f"✅ 登入成功：{client.user} (id={client.user.id})")

@client.tree.command(name="ping", description="測試機器人是否在線")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong!")


# 每個人好感度、模式
ena_mode = defaultdict(lambda: True) # 預設開啟繪名模式
favor = defaultdict(int) # 好感度 0 起跳
carrot_streak = defaultdict(int) # 連續紅蘿蔔次數
rage_until = defaultdict(float) # 暴走到什麼時間（timestamp）
carrot_mode = defaultdict(lambda: "strict") # 預設咖哩飯也有紅蘿蔔

def carrot_risk(text: str) -> str:

    """回傳: 'yes' (確定有) / 'maybe' (可能有) / 'no' (沒有)"""

    t = text.lower()



    # 1) 明確紅蘿蔔關鍵字（確定有）

    if any(k in t for k in ["紅蘿蔔", "胡蘿蔔", "carrot"]):

        return "yes"



    # 2) 高風險料理：常見會出現紅蘿蔔碎/丁/絲（但名稱不一定寫）

    maybe_keywords = [

        "咖哩", "咖喱",

        "便當",

        "炒飯", "炒麵",

        "什錦", "三色",

        "羅宋", "燴飯",

        "沙拉", "涼拌",

        "火鍋", "關東煮",

        "湯麵", "烏龍麵", "拉麵",  # 有些店會放配菜紅蘿蔔絲

        "義大利麵",               # 有些醬/配菜會混
    ]
    if any(k in text for k in maybe_keywords):

        return "maybe"

    return "no"

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
        "繪名上線" if state == "ena" else "繪名下線"
    )

@client.event
async def on_message(message: discord.Message):

    if message.author.bot:
        return
    content = message.content.strip()
    uid = str(message.author.id)

    style = detect_style(content)

    if style != "normal":
        lvl = favor_level(favor[uid])

        if style == "mizuki":
            replies = {
                "low": ["……別用那種語氣跟我講話。", "你學她幹嘛？很吵。"],
                "mid": ["……你學得還挺像。", "行啦，我聽到了。別再演。"],
                "high": ["……你這樣我會不知道怎麼回。", "吵死了…但算你有心。"],
            }

        elif style == "mafuyu":
            replies = {
                "low": ["不要突然變那麼冷。很煩。", "裝什麼冷淡。"],
                "mid": ["……你到底想說什麼？", "別用那種語氣。"],
                "high": ["……你這樣我會擔心。", "別壓抑。直接講。"],
            }

        elif style == "akito":
            replies = {
            "low": ["吵死了。別命令我。", "你以為大聲就有用？"],
            "mid": ["……你很急是吧。", "好啦，我知道了。"],
            "high": ["行。就這次配合你。", "……算了，聽你的。"],
            }
        else:
            return


        reply = random.choice(replies.get(lvl, ["", ""]))
        await message.channel.send(reply)
        return

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

@client.tree.command(name="choosefood", description="繪名幫你從自訂食物中選一個（討厭紅蘿蔔；連抽會暴走）")

@app_commands.describe(options="用逗號分隔，例如：咖哩飯, 拉麵, 紅蘿蔔炒蛋")

async def choosefood(interaction: discord.Interaction, options: str):

    items = [x.strip() for x in options.split(",") if x.strip()]



    if len(items) < 2:

        await interaction.response.send_message("至少給我兩個選項。別讓我幫你想。", ephemeral=True)

        return



    uid = interaction.user.id

    now = time.time()



    # 暴走模式：到時間前都不回（ephemeral 告訴你她在氣）

    if rage_until[uid] > now:

        remaining = int(rage_until[uid] - now)

        await interaction.response.send_message(

            f"……我現在不想講話。\n（暴走中，約 {remaining} 秒後再來）",

            ephemeral=True

        )

        return



    s_before = favor[uid]

    choice = random.choice(items)



    carrot_words = ["紅蘿蔔", "胡蘿蔔", "carrot"]

    has_carrot = any(word.lower() in choice.lower() for word in carrot_words)



    # C：抽到紅蘿蔔扣好感（扣 1~2，不會扣到負數）

    if has_carrot:

        favor[uid] = max(0, favor[uid] - random.randint(1, 2))

        carrot_streak[uid] += 1

    else:

        carrot_streak[uid] = 0



    # 連續抽到紅蘿蔔 → 進入暴走模式（例如 5 分鐘）

    if carrot_streak[uid] >= 2:

        rage_until[uid] = now + 5 * 60

        carrot_streak[uid] = 0  # 進暴走後重置

        await interaction.response.send_message(

            "……又是紅蘿蔔？你是想氣死我是不是。\n我走了。別吵我。",  # 這句可以再更兇一點

        )

        return



    s = favor[uid]  # 扣完後的好感



    if has_carrot:

        # B：嘴上嫌但還是接受結果（不重抽）

        if s_before < 3:

            reply = f"……你是認真的？**{choice}**。\n紅蘿蔔欸。算了，隨便你。"

        elif s_before < 8:

            reply = f"**{choice}**。\n我先講好：紅蘿蔔我不負責處理。"

        else:

            reply = f"今天吃 **{choice}**。\n……有紅蘿蔔的話自己挑掉。我才沒有在關心你。"



        if favor[uid] < s_before:

            reply += f"\n（繪名好感度 -{s_before - favor[uid]}）"

    else:

        if s < 3:

            reply = f"吃 **{choice}**。別再問了。"

        elif s < 8:

            reply = f"嗯…**{choice}** 吧。至少不會踩雷。"

        else:

            reply = f"今天吃 **{choice}**。好好吃飯，別又隨便帶過。"



    await interaction.response.send_message(reply)

client.run(TOKEN)
