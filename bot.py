import discord
import asyncio
from mcstatus import JavaServer, BedrockServer

# 不要改！！！！！！！！！
def get_token():
    with open("TOKEN.txt", "r", encoding="utf-8") as file:
        return file.read().strip()

TOKEN = get_token()

SERVERS = [
    {"name": "Java 版", "ip": "ouo.freeserver.tw", "port": 24253, "type": "java"},
    {"name": "Bedrock 版", "ip": "ouo.freeserver.tw", "port": 24030, "type": "bedrock"},
    # 如果要新增一個伺服器，可以用這個方式：
    # ,{"name": "Java 版", "ip": "ouo.freeserver.tw", "port": 24253, "type": "Java"},
    # 也支援使用 Bungee 分流主機
]

CHANNEL_ID = 1335773767900594268

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"已登入為 {client.user}")
    await send_status_loop()

async def send_status_loop():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print("找不到指定的頻道，請確認 CHANNEL_ID 是否正確")
        return

    message = None
    while not client.is_closed():
        server_statuses = []
        max_latency = 0  # 記錄最高延遲值

        for server in SERVERS:
            try:
                if server["type"] == "java":
                    server_status = JavaServer.lookup(f"{server['ip']}:{server['port']}").status()
                    online = server_status.players.online
                    max_players = server_status.players.max
                    latency = int(server_status.latency)
                else:
                    server_status = BedrockServer.lookup(f"{server['ip']}:{server['port']}").status()
                    online = server_status.players.online
                    max_players = server_status.players.max
                    latency = int(server_status.latency)

                # 判斷延遲顏色
                if latency > 100:
                    latency_text = f"{latency}ms 🔴"
                    status_text = f"狀態：在線 🟢\n玩家：{online}/{max_players}\n延遲：{latency_text}"
                    embed_color = 0xff0000  # 紅色
                elif latency > 50:
                    latency_text = f"{latency}ms 🟡"
                    status_text = f"狀態：在線 🟢\n玩家：{online}/{max_players}\n延遲：{latency_text}"
                    embed_color = 0xffff00  # 黃色
                else:
                    latency_text = f"{latency}ms"
                    status_text = f"狀態：在線 🟢\n玩家：{online}/{max_players}\n延遲：{latency_text}"
                    embed_color = 0x00ff00  # 綠色

                # 記錄最大延遲
                max_latency = max(max_latency, latency)

            except Exception:
                status_text = "狀態：離線 🔴\n玩家：N/A\n延遲：N/A"
                embed_color = 0xff0000  # 紅色

            server_statuses.append({"name": server["name"], "status": status_text})

        total_players = sum(
            int(status["status"].split("\n")[1].split("：")[1].split("/")[0])
            for status in server_statuses if "在線 🟢" in status["status"]
        )

        countdown = 40
        while countdown > 0:
            embed = discord.Embed(title="Minecraft 伺服器狀態", color=embed_color)
            for status in server_statuses:
                embed.add_field(name=status["name"], value=status["status"], inline=False)
            embed.add_field(name="總在線玩家", value=f"{total_players} 位玩家在線", inline=False)
            embed.set_footer(text=f"下次刷新: {countdown} 秒後")
            # {countdown} 是倒數的數字
            if message is None:
                message = await channel.send(embed=embed)
            else:
                await message.edit(embed=embed)

            countdown -= 1
            await asyncio.sleep(1)

        await asyncio.sleep(40)

client.run(TOKEN)