import discord
import asyncio
from mcstatus import JavaServer, BedrockServer

# ==================== 配置区 ====================

TOKEN_FILE = "TOKEN.txt"  # Discord Bot Token 存放位置
CHANNEL_ID = 1335773767900594268  # 设置要发送状态的频道 ID
UPDATE_INTERVAL = 10  # 更新间隔（秒）

# Minecraft 服务器列表
SERVERS = [
    {"name": "Java 版", "ip": "ouo.freeserver.tw", "port": 24030, "type": "java"},
    {"name": "Bedrock 版", "ip": "be.whitecloud.us.kg", "port": 24030, "type": "bedrock"},
]

# ==================== 读取 TOKEN ====================

def get_token():
    """ 从 TOKEN.txt 读取 Bot Token """
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as file:
            return file.read().strip()
    except FileNotFoundError:
        print("❌ 错误：找不到 TOKEN.txt，请确认文件是否存在！")
        exit(1)

TOKEN = get_token()

# ==================== Discord Bot 初始化 ====================

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ==================== 服务器查询功能 ====================

async def fetch_server_status(server):
    """ 查询 Minecraft 服务器状态（Java / Bedrock）"""
    try:
        if server["type"] == "java":
            srv = JavaServer.lookup(f"{server['ip']}:{server['port']}")
            status = await srv.async_status()
        else:
            srv = BedrockServer.lookup(f"{server['ip']}:{server['port']}")
            status = await srv.async_status()

        return {
            "status": "在线 🟢",
            "online": status.players.online,
            "max_players": status.players.max,
            "latency": int(status.latency)
        }

    except Exception:
        return {"status": "离线 🔴", "online": "N/A", "max_players": "N/A", "latency": "N/A"}

# ==================== 生成嵌入消息 ====================

def generate_embed(server_statuses, countdown):
    """ 根据查询结果生成 Discord 的 Embed 消息 """
    embed_color = 0x00ff00  # 默认绿色
    total_players = sum(
        int(status["online"]) if status["status"] == "在线 🟢" and isinstance(status["online"], int) else 0
        for status in server_statuses
    )

    embed = discord.Embed(title="☁️白云生存服☁️ 服务器状态", color=embed_color)

    for server, status in zip(SERVERS, server_statuses):
        latency_text = f"{status['latency']}ms" if isinstance(status["latency"], int) else "N/A"
        embed.add_field(
            name=server["name"],
            value=f"状态：{status['status']}\n玩家：{status['online']}/{status['max_players']}\n延迟：{latency_text}",
            inline=False
        )

    embed.add_field(name="总在线玩家", value=f"{total_players} 位玩家在线", inline=False)
    embed.set_footer(text=f"下次刷新: {countdown} 秒后")

    return embed

# ==================== Bot 启动事件 ====================

@client.event
async def on_ready():
    """ Bot 启动时执行 """
    print(f"✅ 已登录 Discord，Bot 名称：{client.user}")
    await send_status_loop()

async def send_status_loop():
    """ 定期更新 Minecraft 服务器状态 """
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    if not channel:
        print("❌ 错误：找不到指定的频道，请确认 CHANNEL_ID 是否正确！")
        return

    message = None

    while not client.is_closed():
        # 查询所有服务器状态
        server_statuses = await asyncio.gather(*(fetch_server_status(server) for server in SERVERS))

        # 倒计时显示
        for countdown in range(UPDATE_INTERVAL, 0, -1):
            embed = generate_embed(server_statuses, countdown)

            if message is None:
                message = await channel.send(embed=embed)
            else:
                await message.edit(embed=embed)

            await asyncio.sleep(1)

        await asyncio.sleep(UPDATE_INTERVAL)  # 间隔时间

client.run(TOKEN)
