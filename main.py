import asyncio
import random
import os
import re
from datetime import datetime
import pytz
from pyrogram import Client, enums, errors, raw

# --- CONFIGURATION ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
LOG_CHANNEL = "@farinmodssv2"
WIB = pytz.timezone('Asia/Jakarta')

# --- KONTEN PROMOSI (TETAP BERSIH) ---
PROMO_TEXT = (
"🚀 **FARIN SHOP – OTP TERCEPAT & TERMURAH!**\n\n"
"Butuh OTP cepat & murah untuk WhatsApp, Telegram, Instagram, Facebook, dan banyak aplikasi lainnya?\n"
"Farin Shop solusinya!\n\n"
"✅ **Kenapa Pilih Farin Shop?**\n"
"• Proses super cepat – OTP masuk dalam detik\n"
"• Harga terjangkau – ada yang cuma 900p!\n"
"• Banyak negara & server tersedia\n"
"• Auto Order 24/7 – bot selalu online\n"
"• Monitoring harga real-time – selalu update\n\n"
"⭐ **Fitur Bot:**\n"
"• Menu interaktif mudah digunakan\n"
"• Cek saldo & riwayat transaksi\n"
"• Notifikasi real-time\n"
"• Support 24/7\n\n"
"⚠️ **Garansi 100%** – Jika gagal, saldo dikembalikan\n\n"
"🎯 **Layanan Tersedia:**\n"
"WhatsApp, Telegram, Instagram, Facebook, dll\n"
"Berbagai negara dan operator\n\n"
"📢 **Cek Info Testimoni:**\n"
"@Farinmods\n\n"
"🤖 **Order Sekarang di Telegram:**\n"
"@FarinShop_bot\n"
"Chat & order langsung dalam 1 menit"
)

status_msg_id = None
app = Client(
    "farin_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
    sleep_threshold=180
)

def get_loading_bar(percentage):
    """Gaya loading bar dengan simbol block custom"""
    filled = int(percentage / 10)
    bar = "█" * filled + "▒" * (10 - filled)
    return f"`|{bar}|` **{percentage:.1f}%**"

async def update_dashboard(stats_content, status_type="RUNNING"):
    """Update Dashboard dengan UI Terminal Premium"""
    global status_msg_id
    now = datetime.now(WIB).strftime("%H:%M:%S")
    
    status_map = {
        "SCANNING": "🔍 [ SCANNING DATABASE ]",
        "ADVERTISING": "🛰️ [ BROADCASTING LIVE ]",
        "WAITING": "⏳ [ FLOOD RESTRICTION ]",
        "SLEEPING": "💤 [ STANDBY MODE ]"
    }
    
    status_display = status_map.get(status_type, "🟢 [ ACTIVE ]")
    
    ui_text = (
        f"        ◈ **FARIN SHOP TERMINAL v5.0** ◈\n"
        f"`──────────────────────────────`\n"
        f"⌚ **SYSTEM TIME :** `{now} WIB`\n"
        f"📡 **CORE STATUS :** `{status_display}`\n"
        f"📶 **CONNECTION  :** `SECURE (SSL/TLS)`\n"
        f"⚙️ **SERVER ID   :** `RAILWAY-NODE-01`\n"
        f"`──────────────────────────────`\n"
        f"{stats_content}\n"
        f"`──────────────────────────────`\n"
        f"⚡ **POWERED BY:** `FARINMODS CORE ENGINE`"
    )
    
    try:
        if status_msg_id:
            await app.edit_message_text(LOG_CHANNEL, status_msg_id, ui_text)
        else:
            msg = await app.send_message(LOG_CHANNEL, ui_text)
            status_msg_id = msg.id
    except:
        try:
            msg = await app.send_message(LOG_CHANNEL, ui_text)
            status_msg_id = msg.id
        except: pass

# --- JOIN HANDLER ---
@app.on_message(filters.private & ~filters.service)
async def handle_bulk_join(client, message):
    if message.text and message.text.lower().startswith("/join"):
        links = re.findall(r'(https?://t\.me/\S+)', message.text)
        if not links: return
        report = await message.reply("🚀 `BOOTING JOIN PROTOCOL...`")
        s, f = 0, 0
        for link in links:
            try:
                slug = link.split('/')[-1]
                if "addlist" in link:
                    check = await client.invoke(raw.functions.chatlists.CheckChatlistInvite(slug=slug))
                    input_peers = []
                    for chat in check.chats:
                        if isinstance(chat, (raw.types.Chat, raw.types.Channel)):
                            if isinstance(chat, raw.types.Chat):
                                input_peers.append(raw.types.InputPeerChat(chat_id=chat.id))
                            else:
                                input_peers.append(raw.types.InputPeerChannel(channel_id=chat.id, access_hash=chat.access_hash))
                    await client.invoke(raw.functions.chatlists.JoinChatlistInvite(slug=slug, peers=input_peers))
                    s += 1
                else:
                    await client.join_chat(link); s += 1
                await asyncio.sleep(5)
            except: f += 1
        await report.edit_text(f"📊 **JOIN REPORT**\n✅ SUCCESS: `{s}`\n❌ FAILED: `{f}`")

# --- PROMO HANDLER ---
async def auto_promo():
    if not app.is_connected:
        await app.start()
    
    while True:
        await update_dashboard("🛠️ `INITIALIZING DATABASE SCAN...`", "SCANNING")
        groups = []
        try:
            async for dialog in app.get_dialogs(limit=0):
                if dialog.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                    groups.append(dialog.chat.id)
        except: pass

        if not groups:
            await update_dashboard("⚠️ `DATABASE EMPTY - RE-SCANNING...`", "SLEEPING")
            await asyncio.sleep(300); continue

        random.shuffle(groups)
        s, f, l = 0, 0, 0
        total = len(groups)

        for index, chat_id in enumerate(groups):
            try:
                await app.send_message(chat_id, PROMO_TEXT)
                s += 1
            except (errors.ChatWriteForbidden, errors.UserBannedInChannel, errors.ChatInvalid, errors.PeerIdInvalid, errors.ChannelPrivate):
                try: await app.leave_chat(chat_id); l += 1
                except: pass
            except errors.FloodWait as e:
                await update_dashboard(f"☣️ `COOLING DOWN: {e.value}s`", "WAITING")
                await asyncio.sleep(e.value)
                try: await app.send_message(chat_id, PROMO_TEXT); s += 1
                except: f += 1
            except: f += 1

            if (index + 1) % 5 == 0 or (index + 1) == total:
                pct = ((index + 1) / total) * 100
                loading_bar = get_loading_bar(pct)
                remains = total - (index + 1)
                
                # Desain Statistik yang Lebih "Penuh"
                stats = (
                    f"📂 **PROGRESS STATUS**\n"
                    f"├ {loading_bar}\n"
                    f"├ `TOTAL TARGET :` {total}\n"
                    f"└ `REMAINING    :` {remains}\n\n"
                    f"📈 **OPERATIONAL LOGS**\n"
                    f"├ `SUCCESS      :` {s} ✅\n"
                    f"├ `FAILED       :` {f} ❌\n"
                    f"└ `CLEANED      :` {l} 🧹\n\n"
                    f"📡 **CURRENT ACTIVITY**\n"
                    f"└ `TARGET ID :` `{chat_id}`\n"
                    f"└ `LOAD      :` `{(index+1)}/{total} UNITS`"
                )
                await update_dashboard(stats, "ADVERTISING")
            
            await asyncio.sleep(random.randint(1, 3))

        await update_dashboard(f"🏁 **ROUND COMPLETE**\n\n✅ TOTAL BROADCAST: `{s}`\n🧹 SYSTEM CLEANED: `{l}`\n💤 NEXT REBOOT: `2 HOURS`", "SLEEPING")
        await asyncio.sleep(500)

if __name__ == "__main__":
    while True:
        try:
            app.run(auto_promo())
        except Exception:
            asyncio.run(asyncio.sleep(10))
