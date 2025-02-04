import discord
import asyncio
from mcstatus import JavaServer, BedrockServer

# ==================== 配置區 ====================

TOKEN_FILE = "TOKEN.txt"  # Discord Bot Token 存放位置
CHANNEL_ID = 1335773767900594268  # 設定要發送狀態的頻道 ID
UPDATE_INTERVAL = 10  # 更新間隔（秒）

# Minecraft 伺服器列表
SERVERS = [
    {"name": "Java 版", "ip": "ouo.freeserver.tw", "port": 24030, "type": "java"},
    {"name": "Bedrock 版", "ip": "be.whitecloud.us.kg", "port": 24030, "type": "bedrock"},
]

# ==================== 讀取 TOKEN ====================

def get_token():
    """ 從 TOKEN.txt 讀取 Bot Token """
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as file:
            return file.read().strip()
    except FileNotFoundError:
        print("❌ 錯誤：找不到 TOKEN.txt，請確認檔案是否存在！")
        exit(1)

TOKEN = get_token()

# ==================== Discord Bot 初始化 ====================

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ==================== 伺服器查詢功能 ====================

async def fetch_server_status(server):
    """ 查詢 Minecraft 伺服器狀態（Java / Bedrock）"""
    try:
        if server["type"] == "java":
            srv = JavaServer.lookup(f"{server['ip']}:{server['port']}")
            status = await srv.async_status()
        else:
            srv = BedrockServer.lookup(f"{server['ip']}:{server['port']}")
            status = await srv.async_status()

        return {
            "status": "在線 🟢",
            "online": status.players.online,
            "max_players": status.players.max,
            "latency": int(status.latency)
        }

    except Exception:
        return {"status": "離線 🔴", "online": "N/A", "max_players": "N/A", "latency": "N/A"}

# ==================== 產生嵌入訊息 ====================

def generate_embed(server_statuses, countdown):
    """ 根據查詢結果產生 Discord 的 Embed 訊息 """
    embed_color = 0x00ff00  # 預設綠色
    total_players = sum(
        int(status["online"]) if status["status"] == "在線 🟢" and isinstance(status["online"], int) else 0
        for status in server_statuses
    )

    embed = discord.Embed(title="☁️白雲生存服☁️ 伺服器狀態", color=embed_color)

    for server, status in zip(SERVERS, server_statuses):
        latency_text = f"{status['latency']}ms" if isinstance(status["latency"], int) else "N/A"
        embed.add_field(
            name=server["name"],
            value=f"狀態：{status['status']}\n玩家：{status['online']}/{status['max_players']}\n延遲：{latency_text}",
            inline=False
        )

    embed.add_field(name="總在線玩家", value=f"{total_players} 位玩家在線", inline=False)
    embed.set_footer(text=f"下次刷新: {countdown} 秒後")

    return embed

# ==================== Bot 啟動事件 ====================

@client.event
async def on_ready():
    """ Bot 啟動時執行 """
    print(f"✅ 已登入 Discord，Bot 名稱：{client.user}")
    await send_status_loop()

async def send_status_loop():
    """ 定期更新 Minecraft 伺服器狀態 """
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    if not channel:
        print("❌ 錯誤：找不到指定的頻道，請確認 CHANNEL_ID 是否正確！")
        return

    message = None

    while not client.is_closed():
        # 查詢所有伺服器狀態
        server_statuses = await asyncio.gather(*(fetch_server_status(server) for server in SERVERS))

        # 倒數計時顯示
        for countdown in range(UPDATE_INTERVAL, 0, -1):
            embed = generate_embed(server_statuses, countdown)

            if message is None:
                message = await channel.send(embed=embed)
            else:
                await message.edit(embed=embed)

            await asyncio.sleep(1)

        await asyncio.sleep(UPDATE_INTERVAL)  # 間隔時間

client.run(TOKEN)
