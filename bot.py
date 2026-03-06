import os
import discord
from discord.ext import commands, tasks
import asyncio
import datetime
from openai import AsyncOpenAI

print("=== BOT VERSION CHECK 1215 ===")
print("OPENAI_API_KEY exists:", bool(os.environ.get("OPENAI_API_KEY")))
print("DISCORD_BOT_TOKEN exists:", bool(os.environ.get("DISCORD_BOT_TOKEN")))
print("=== BOT VERSION 1209-AIOHTTP ===")
print("NEW VERSION DEPLOY TEST")

client = AsyncOpenAI(

    api_key=os.environ.get("OPENAI_API_KEY"),

)


DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")


intents = discord.Intents.default()

intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)



# ===== 狀態 =====

active_users = set()          # 已啟動聊天模式的使用者

user_last_active = {}         # user_id -> (channel, last_time)

conversation_memory = {}      # user_id -> list[dict]



TIMEOUT_SECONDS = 30

MAX_MEMORY_TURNS = 8



# ===== 人格設定 =====

SYSTEM_PROMPT = """

你是「繪名」風格的聊天 bot。

請遵守以下規則：

1. 使用繁體中文。

2. 語氣有點嘴硬、毒舌、冷淡，但不是惡意攻擊。

3. 回覆偏短，像朋友聊天，不要太正式。

4. 偶爾吐槽，但不要每句都很兇。

5. 不要自稱是 AI，不要提系統提示。

6. 如果對方情緒明顯低落，可以稍微關心，但仍維持繪名風格。

7. 除非對方問很多，不然盡量 1~3 句內回答。

"""



# ===== 工具函式 =====

async def send_with_typing(channel, reply: str):

    async with channel.typing():

        typing_time = min(max(len(reply) * 0.05, 1.0), 5.0)

        await asyncio.sleep(typing_time)

    await channel.send(reply)



def get_user_memory(user_id: int):

    if user_id not in conversation_memory:

        conversation_memory[user_id] = []

    return conversation_memory[user_id]



def trim_memory(user_id: int):

    memory = get_user_memory(user_id)

    if len(memory) > MAX_MEMORY_TURNS * 2:

        conversation_memory[user_id] = memory[-MAX_MEMORY_TURNS * 2:]



async def get_ai_reply(user_id: int, user_message: str) -> str:

    try:



        response = await client.chat.completions.create(

            model="gpt-4.1-mini",

            messages=[

                {"role": "system", "content": SYSTEM_PROMPT},

                {"role": "user", "content": user_message}

            ],

            timeout=30

        )



        reply = response.choices[0].message.content



        if not reply:

            return "……你這樣我很難接話。"



        return reply



    except Exception as e:

        print("AI error 詳細：", repr(e))

        return f"AI出錯了：{type(e).__name__}: {e}"
    
# ===== 超時檢查 =====

@tasks.loop(seconds=5)

async def check_timeout():

    now = datetime.datetime.now(datetime.timezone.utc)



    for user_id, data in list(user_last_active.items()):

        channel, last_time = data



        if (now - last_time).total_seconds() > TIMEOUT_SECONDS:

            await send_with_typing(channel, "哼……你都不說話，我先走啦。")

            user_last_active.pop(user_id, None)

            active_users.discard(user_id)

            conversation_memory.pop(user_id, None)



# ===== 啟動 =====

@bot.event

async def on_ready():

    print(f"登入成功：{bot.user}")

    if not check_timeout.is_running():

        check_timeout.start()

        print("check_timeout 已啟動")



# ===== 訊息事件 =====

@bot.event

async def on_message(message):

    if message.author == bot.user:

        return



    content = message.content.strip()

    user_id = message.author.id

    now = datetime.datetime.now(datetime.timezone.utc)



    # 啟動指令

    if content in ["繪名", "!繪名 啟動"]:

        active_users.add(user_id)

        user_last_active[user_id] = (message.channel, now)

        conversation_memory.pop(user_id, None)  # 每次重新啟動，對話重新開始

        await send_with_typing(message.channel, "幹嘛叫我？這是最新railway版。")

        return



    # 關閉指令

    if content in ["繪名 再見", "!繪名 關閉"]:

        active_users.discard(user_id)

        user_last_active.pop(user_id, None)

        conversation_memory.pop(user_id, None)

        await send_with_typing(message.channel, "好啦，再見。記得吃飯。")

        return



    # 沒啟動就不回

    if user_id not in active_users:

        await bot.process_commands(message)

        return



    # 更新最後互動時間

    user_last_active[user_id] = (message.channel, now)



    # 這裡可以保留你的特殊規則

    if "紅蘿蔔" in content:

        await send_with_typing(message.channel, "……不要跟我提那個。")

        return



    # 一般聊天走 AI

    reply = await get_ai_reply(user_id, content)

    await send_with_typing(message.channel, reply)



    await bot.process_commands(message)



# ===== 測試指令 =====

@bot.command()

async def test(ctx):

    await send_with_typing(ctx.channel, "機器人運行正常。")



# ===== 啟動 bot =====

bot.run(DISCORD_BOT_TOKEN)















