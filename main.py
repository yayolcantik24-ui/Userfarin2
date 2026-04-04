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

# --- KONTEN PROMOSI TERBARU ---
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
    sleep_threshold=120
)

async def update_dashboard(stats_content):
    global status_msg_id
    now = datetime.now(WIB).strftime("%d/%m/%Y %H:%M:%S")
    header = f"🛡️ **FARIN SHOP MONITORING**\n{'─'*25}\n"
    footer = f"\n{'─'*25}\n🕒 *Last Update: {now} WIB*"
    full_text = header + stats_content + footer
    try:
        if status_msg_id:
            await app.edit_message_text(LOG_CHANNEL, status_msg_id, full_text)
        else:
            msg = await app.send_message(LOG_CHANNEL, full_text)
            status_msg_id = msg.id
    except:
        try:
            msg = await app.send_message(LOG_CHANNEL, full_text)
            status_msg_id = msg.id
        except: pass

# --- FITUR: BULK JOIN (SOLUSI RAW API UNTUK SEMUA VERSI PYROGRAM) ---
@app.on_message(enums.ChatType.PRIVATE)
async def handle_bulk_join(client, message):
    if message.text and message.text.lower().startswith("/join"):
        links = re.findall(r'(https?://t\.me/\S+)', message.text)
        if not links:
            await message.reply("❌ Tidak ada link ditemukan.")
            return

        report = await message.reply(f"⏳ Memproses **{len(links)}** link dengan Raw API...")
        success, failed = 0, 0
        error_logs = ""

        for link in links:
            try:
                # Mengambil 'slug' (kode unik setelah addlist/ atau joinchat/)
                slug = link.split('/')[-1]
                
                if "addlist" in link:
                    # Menggunakan Raw Invoke agar tidak kena 'AttributeError'
                    # Join ke Chatlist/Folder
                    await client.invoke(
                        raw.functions.chatlists.CheckChatlistInvite(slug=slug)
                    )
                    await client.invoke(
                        raw.functions.chatlists.JoinChatlistInvite(slug=slug, peers=[])
                    )
                    await asyncio.sleep(3)
                    
                    # Hapus Folder segera agar limit aman
                    try:
                        folder_data = await client.invoke(raw.functions.messages.GetDialogFilters())
                        for filt in folder_data:
                            if isinstance(filt, raw.types.DialogFilter):
                                await client.invoke(raw.functions.messages.UpdateDialogFilter(id=filt.id, filter=None))
                    except: pass
                    
                else:
                    # Join Grup/Channel biasa
                    await client.join_chat(link)
                
                success += 1
                await asyncio.sleep(random.randint(5, 10))
                
            except errors.FloodWait as e:
                error_logs += f"• {link}: Limit {e.value}s\n"
                failed += 1
            except Exception as e:
                error_logs += f"• {link}: {str(e)}\n"
                failed += 1

        final_msg = f"✅ **Bulk Join Selesai!**\n🔥 Sukses: {success}\n❌ Gagal: {failed}\n"
        if error_logs:
            final_msg += f"\n**Detail Error:**\n{error_logs}"
        
        await report.edit_text(final_msg)

async def auto_promo():
    try:
        if not app.is_connected:
            await app.start()
    except Exception: pass

    await update_dashboard("🚀 **Status:** Online\n📡 **System:** Raw API Mode Aktif")
    
    while True:
        await update_dashboard("🔍 **Status:** Scanning Groups...")
        groups = []
        try:
            async for dialog in app.get_dialogs():
                try:
                    if dialog.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                        groups.append(dialog.chat.id)
                except:
                    try: await app.leave_chat(dialog.chat.id)
                    except: pass
        except: pass

        if not groups:
            await update_dashboard("⚠️ **Status:** Grup Kosong."); await asyncio.sleep(300); continue

        random.shuffle(groups)
        s, f, l = 0, 0, 0

        for index, chat_id in enumerate(groups):
            try:
                await app.send_message(chat_id, PROMO_TEXT)
                s += 1
            except (errors.ChatWriteForbidden, errors.UserBannedInChannel, errors.ChannelPrivate):
                try: await app.leave_chat(chat_id); l += 1
                except: pass
            except errors.FloodWait as e:
                await asyncio.sleep(e.value)
                try: await app.send_message(chat_id, PROMO_TEXT); s += 1
                except: f += 1
            except: f += 1

            if (index + 1) % 10 == 0 or (index + 1) == len(groups):
                pct = ((index + 1) / len(groups)) * 100
                await update_dashboard(f"📤 **Promo Aktif**\n📊 {index+1}/{len(groups)} ({pct:.1f}%)\n✅ {s} | ❌ {f} | 🚪 {l}")

            await asyncio.sleep(random.randint(1, 3))

        await update_dashboard(f"🏁 **Selesai!**\n✅ {s} | 🚪 {l}\n💤 Istirahat 2 Jam")
        await asyncio.sleep(600)

if __name__ == "__main__":
    while True:
        try:
            app.run(auto_promo())
        except Exception as e:
            print(f"Restart: {e}")
            asyncio.run(asyncio.sleep(10))