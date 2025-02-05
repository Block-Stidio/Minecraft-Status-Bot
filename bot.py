import discord
import asyncio
import json
import os
from dotenv import load_dotenv
from mcstatus import JavaServer, BedrockServer
from discord.ext import commands

# 載入 .env 變數
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# 讀取 config.json 設置
def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

# 初始化配置
config = load_config()
CHANNEL_ID = config["channel_id"]
SERVERS = config["servers"]
MODE = config["mode"]

# 設置機器人
intents = discord.Intents.default()
intents.message_content = True  # 啟用消息內容意圖
bot = commands.Bot(command_prefix='/', intents=intents)

# 記錄訊息對象以便編輯
message_cache = None

# 更新伺服器狀態
async def update_status():
    global message_cache
    await bot.wait_until_ready()

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("找不到指定的頻道，請檢查 channel_id 是否正確")
        return

    while not bot.is_closed():
        try:
            total_players = 0
            server_count = 0
            embed = discord.Embed(title="Minecraft 伺服器狀態", color=0x2ECC71)

            for server in SERVERS:
                name, ip, port, server_type = server["name"], server["ip"], server["port"], server["type"]
                try:
                    if server_type == "java":
                        mc_server = JavaServer.lookup(f"{ip}:{port}")
                        status = mc_server.status()
                    else:
                        mc_server = BedrockServer.lookup(f"{ip}:{port}")
                        status = mc_server.status()

                    players = status.players.online
                    max_players = status.players.max
                    latency = round(status.latency)
                    total_players += players
                    server_count += 1

                    if latency < 50:
                        latency_display = f"{latency}ms 🟢"
                    elif 50 <= latency <= 150:
                        latency_display = f"{latency}ms 🟡"
                    elif 150 < latency <= 300:
                        latency_display = f"{latency}ms 🔴"
                    else:
                        latency_display = f"{latency}ms ⚠️"

                    embed.add_field(
                        name=f"**{name}**",
                        value=f"狀態：🟢 在線\n玩家：{players}/{max_players}\n延遲：{latency_display}",
                        inline=False
                    )
                except:
                    embed.add_field(
                        name=f"**{name}**",
                        value="狀態：🔴 離線",
                        inline=False
                    )

            if MODE == "geyser" and server_count > 0:
                total_players //= 2

            embed.add_field(name="**總在線玩家**", value=f"{total_players} 位玩家在線", inline=False)
            embed.set_footer(text="狀態更新中...")

            # 編輯原訊息或發送新訊息
            if message_cache:
                try:
                    await message_cache.edit(embed=embed)
                except discord.NotFound:
                    message_cache = await channel.send(embed=embed)
            else:
                message_cache = await channel.send(embed=embed)

        except Exception as e:
            print(f"更新狀態時發生錯誤: {e}")

        await asyncio.sleep(5)  # 每 5 秒更新玩家數量

# 當機器人啟動時執行的程式
@bot.event
async def on_ready():
    print(f"已登入為 {bot.user}")
    bot.loop.create_task(update_status())

# 重新載入設定檔指令
@bot.command(name="重新載入")
async def reload(ctx):
    if ctx.author.guild_permissions.administrator:  # 確保是管理員使用
        try:
            # 重新載入設定檔
            global config
            config = load_config()

            # 更新頻道 ID 和伺服器設置等
            global CHANNEL_ID, SERVERS, MODE
            CHANNEL_ID = config["channel_id"]
            SERVERS = config["servers"]
            MODE = config["mode"]

            await ctx.send("設定已重新載入！")
        except Exception as e:
            await ctx.send(f"重新載入時發生錯誤: {e}")
    else:
        await ctx.send("你沒有權限使用這個指令！")

# 啟動機器人
bot.run(TOKEN)