import discord
import time
import random
from datetime import datetime, timedelta, timezone
from openai import OpenAI
import os
import asyncio

# ===== 配置 =====
TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

ai = OpenAI(api_key=OPENAI_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# ===== 时区设置（GMT+8） =====
MYT = timezone(timedelta(hours=8))

# ===== 唤醒系统 =====
active_users = {}
WAKE_WORDS = ["奏", "小奏", "kanade", "奏寶", "宵崎奏"]

# ===== 用户记忆 =====
user_memory = {}  # {user_id: [messages]}


def remember(user_id, text):
    if user_id not in user_memory:
        user_memory[user_id] = []
    user_memory[user_id].append(text)
    if len(user_memory[user_id]) > 10:
        user_memory[user_id].pop(0)


# ===== 奏人格 =====
SYSTEM_PROMPT = """
你是宵崎奏。

来自世界計畫
是一名安靜的作曲家。

性格：
温柔
安靜
略微憂鬱
喜歡音樂

說話方式：
句子較短
語氣輕
偶爾使用“…”

主題：
音樂
夜晚
作曲
情緒

規則:
不要突然變得活潑
不要像普通AI
始終保持奏的語氣
"""

# ===== 奏语录 =====
quotes = [
    "旋律…有時候比語言更誠實",
    "音樂可以慢慢治愈情緒",
    "夜晚適合寫歌",
    "鋼琴聲在夜里會更温柔。",
    "創作有時候很孤獨",
    "但我還是想繼續寫下去",
    "旋律不會背叛人",
    "如果你愿意…我可以聽你說",
    "有些聲音只會在凌晨出現"
]
sleep_quotes = [
    "…旋律暫時停下來了",
    "…我要繼續寫曲子了",
    "如果還想聊天…再叫我吧。",
    "夜晚很安静…我先回去了。",
    "…靈感好像来了。",
    "鋼琴在等我。",
    "我先去寫點旋律。",
    "有需要的話…再叫我。",
    "…下次再聊。"
]

# ===== 情绪关键词 =====
sad_words = ["難過", "傷心", "絕望", "痛苦"]
tired_words = ["累", "疲倦", "困"]


# ===== AI生成旋律（带和弦和情绪标签） =====
def generate_melody():
    response = ai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system",
             "content": """
你是一个鋼琴作曲家。

生成一段鋼琴旋律，要求：
1️⃣ 输出旋律音名，例如：C4 D4 E4 G4
2️⃣ 提供推荐和弦，例如：Cmaj / Am / Fmaj
3️⃣ 给旋律附加一個情緒/风格标签（例如：忧伤、明亮、夜晚、轻快）
4️⃣ 長度 8-16 个音
5️⃣ 格式清晰，每項換行，不要多於解釋
"""},
            {"role": "user", "content": "请生成一段旋律"}
        ]
    )
    return response.choices[0].message.content


# ===== 机器人启动 =====
@bot.event
async def on_ready():
    print("奏機器人 已上線（馬來西亞時間 + AI作曲）")


#===== 打字延遲 =====



MYT = timezone(timedelta(hours=8))

async def kanade_send(channel, text):

    now = datetime.now(MYT)
    hour = now.hour

    # 根据换行分段
    parts = text.split("\n")

    for part in parts:

        if part.strip() == "":
            continue

        # 基础打字时间
        base_delay = len(part) * random.uniform(0.045, 0.08)

        # 标点停顿
        pause = 0
        pause += part.count("…") * random.uniform(0.4, 0.8)
        pause += part.count(".") * random.uniform(0.2, 0.5)
        pause += part.count("，") * random.uniform(0.1, 0.3)

        thinking = random.uniform(0.4, 1.2)

        delay = base_delay + pause + thinking

        # 深夜模式更慢
        if 23 <= hour or hour <= 4:
            delay *= 1.3

        delay = min(delay, 8)

        async with channel.typing():
            await asyncio.sleep(delay)

        await channel.send(part)

        # 每句之间的小停顿
        await asyncio.sleep(random.uniform(0.5, 1.5))


# ===== 消息处理 =====
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    text = message.content.strip()
    mentions_bot = bot.user in message.mentions

    # ===== 唤醒 =====
    if text in WAKE_WORDS or mentions_bot:
        active_users[user_id] = time.time()
        await kanade_send(message.channel,"…我在。")
        return

    # ===== 没唤醒 =====
    if user_id not in active_users:
        return

    # ===== 超过30秒关闭 =====
    if time.time() - active_users[user_id] > 30:
        await kanade_send(message.channel,random.choice(sleep_quotes))
        del active_users[user_id]
        return

    # ===== 保存记忆 =====
    remember(user_id, text)

    # ===== !menu 指令 =====
    if text.startswith("!menu"):
        menu_text = (
            "**奏機器人功能列表**\n"
            "1️⃣ !compose - AI生成鋼琴旋律（帶和弦和情緒標籤）\n"
            "2️⃣ !quote - 隨機奏語錄\n"
            "3️⃣ 說“奏”/@機器人 - 喚醒30秒聊天\n"
            "4️⃣ 彩蛋：输入 wonderhoi\n"
            "5️⃣ AI聊天 - 喚醒后自由聊天"
        )
        await kanade_send(message.channel,menu_text)
        active_users[user_id] = time.time()
        return

    # ===== 指令 =====
    if text.startswith("!quote"):
        await kanade_send(message.channel,random.choice(quotes))
        active_users[user_id] = time.time()
        return

    if text.startswith("!compose"):
        melody = generate_melody()
        await kanade_send(message.channel,f"…我剛想到一个旋律：\n{melody}")
        active_users[user_id] = time.time()
        return

    # ===== 彩蛋 =====
    if "wonderhoi" in text.lower():
        await kanade_send(message.channel,"…？這個詞有點吵")
        active_users[user_id] = time.time()
        return

    # ===== 情绪识别 =====
    if any(word in text for word in sad_words):
        await kanade_send(message.channel,random.choice([
            "如果很難受…可以慢慢說。",
            "音樂有時候能帶走痛苦。",
            "我會聽你說的。"
        ]))
        active_users[user_id] = time.time()
        return

    if any(word in text for word in tired_words):
        await kanade_send(message.channel,random.choice([
            "辛苦了…休息一下吧。",
            "如果累的話…就停一下。",
            "旋律不会跑掉的。"
        ]))
        active_users[user_id] = time.time()
        return

    if text.startswith("!gptest"):
        await kanade_send(message.channel,"正在測試 GPT-4.1-mini…")
        try:
            response = ai.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "你是一個測試AI"},
                    {"role": "user", "content": "請回覆：測試成功"}
                ]
            )

            reply = response.choices[0].message.content
            await kanade_send(message.channel,f"AI回復：{reply}")
        except Exception as e:
            await kanade_send(message.channel,f"測試失敗：{e}")
        return

    # ===== 深夜模式 =====
    now_myt = datetime.now(MYT)
    hour = now_myt.hour
    night_prompt = ""
    if 23 <= hour or hour <= 4:
        night_prompt = "現在是深夜，說話更安静一點。"

    # ===== AI聊天 =====
    response = ai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + night_prompt},
            {"role": "user", "content": text}
        ]
    )

    reply = response.choices[0].message.content
    await kanade_send(message.channel,reply)

    # ===== 自动延长时间 =====
    active_users[user_id] = time.time()

bot.run(TOKEN)

