import os, subprocess, sys, asyncio, json, time
from threading import Thread
from flask import Flask

# 1. السيرفر الوهمي (Uptime)
app = Flask('')
@app.route('/')
def home(): return "System Online"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# 2. إدارة المكتبات
local_dir = os.path.join(os.getcwd(), ".local_libs")
if not os.path.exists(local_dir): os.makedirs(local_dir)
sys.path.insert(0, local_dir)

try:
    import discord
    from discord.ext import commands
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "discord.py-self", "pynacl", "flask", "--target", local_dir])
    import discord
    from discord.ext import commands

# --- الإعدادات ---
TOKEN = 'MTM2MTI2OTYxMTc0Nzc0MTcxNg.GC1mNa.O_CoXgy9IfDsoDCsXOrBXd6o3lx4hTmI7Zt4p0' 
PREFIX = '!'
LAST_ROOM_FILE = 'last_room.json'

bot = commands.Bot(command_prefix=PREFIX, self_bot=True, help_command=None)
is_manual_stopping = False 

@bot.event
async def on_ready():
    print(f'✅ متصل: {bot.user}')
    # الحالة 1: إعادة الاتصال عند تشغيل السكربت (Boot-Rejoin)
    if os.path.exists(LAST_ROOM_FILE):
        try:
            with open(LAST_ROOM_FILE, 'r') as f:
                data = json.load(f)
                channel = await bot.fetch_channel(data['channel_id'])
                if channel: 
                    await channel.connect(self_deaf=True, self_mute=True)
                    print(f"🎙️ عودة تلقائية: {channel.name}")
        except: pass

@bot.event
async def on_voice_state_update(member, before, after):
    global is_manual_stopping
    if member.id == bot.user.id:
        # الحالة 2: إعادة الاتصال عند الخروج المفاجئ (Auto-Rejoin)
        if before.channel and after.channel is None:
            if not is_manual_stopping:
                print(f"⚠️ خروج مفاجئ.. محاولة العودة بعد 7 ثوانٍ.")
                await asyncio.sleep(7)
                if os.path.exists(LAST_ROOM_FILE):
                    try:
                        with open(LAST_ROOM_FILE, 'r') as f: data = json.load(f)
                        ch = await bot.fetch_channel(data['channel_id'])
                        await ch.connect(self_deaf=True, self_mute=True)
                    except: pass

@bot.command(name='voice')
async def voice_join(ctx, arg: str):
    global is_manual_stopping
    is_manual_stopping = False
    try:
        channel = await bot.fetch_channel(int(arg))
        await channel.connect(self_deaf=True, self_mute=True)
        # حفظ المعرف في الذاكرة
        with open(LAST_ROOM_FILE, 'w') as f: json.dump({'channel_id': int(arg)}, f)
        await ctx.send(f"🎙️ دخلت: {channel.name}")
    except Exception as e: await ctx.send(f"❌ خطأ: {e}")

@bot.command(name='stop')
async def voice_stop(ctx):
    global is_manual_stopping
    is_manual_stopping = True
    if os.path.exists(LAST_ROOM_FILE): os.remove(LAST_ROOM_FILE)
    for vc in bot.voice_clients: await vc.disconnect(force=True)
    await ctx.send("🛑 تم الخروج وحذف الذاكرة.")
    await asyncio.sleep(2)
    is_manual_stopping = False

keep_alive()
try:
    bot.run(TOKEN)
except Exception as e:
    print(f"❌ فشل: التوكن قد يكون خطأ. {e}")
