import asyncio
import random
import os
import re
from datetime import datetime
import pytz
from pyrogram import Client, enums, errors

# --- CONFIGURATION (AMBIL DARI VARIABLES RAILWAY) ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
LOG_CHANNEL = "@farinmodssv2" #

# Setting Zona Waktu Indonesia (WIB)
WIB = pytz.timezone('Asia/Jakarta') #

# --- KONTEN PROMOSI TERBARU FARIN SHOP ---
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

# Global variable untuk ID pesan Dashboard
status_msg_id = None #

app = Client(
    "farin_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
    sleep_threshold=120  # Otomatis handle FloodWait yang lama
)

async def update_dashboard(stats_content):
    """Mengedit satu pesan log agar channel tetap bersih (Dashboard Mode)"""
    global status_msg_id
    now = datetime.now(WIB).strftime("%d/%m/%Y %H:%M:%S") #
    
    header = f"🛡️ **FARIN SHOP MONITORING**\n{'─'*25}\n"
    footer = f"\n{'─'*25}\n🕒 *Last Update: {now} WIB*"
    full_text = header + stats_content + footer
    
    try:
        if status_msg_id:
            await app.edit_message_text(LOG_CHANNEL, status_msg_id, full_text) #
        else:
            msg = await app.send_message(LOG_CHANNEL, full_text)
            status_msg_id = msg.id #
    except Exception:
        try:
            msg = await app.send_message(LOG_CHANNEL, full_text)
            status_msg_id = msg.id
        except:
            pass

# --- FITUR: BULK JOIN & AUTO DELETE FOLDER ---
@app.on_message(enums.ChatType.PRIVATE)
async def handle_bulk_join(client, message):
    if message.text and message.text.lower().startswith("/join"):
        # Mengambil semua link t.me dari pesan
        links = re.findall(r'(https?://t\.me/\S+)', message.text)
        
        if not links:
            await message.reply("❌ Tidak ada link ditemukan.")
            return

        report = await message.reply(f"⏳ Memproses **{len(links)}** link sekaligus...")
        success, failed = 0, 0

        for link in links:
            try:
                if "addlist" in link:
                    await client.join_chat_invite_folder(link)
                    # Hapus Folder segera agar limit tidak penuh (Akun tetap di grup)
                    folders = await client.get_chat_invite_folders()
                    for folder in folders:
                        await client.delete_chat_invite_folder(folder.folder_id)
                else:
                    await client.join_chat(link)
                
                success += 1
                await asyncio.sleep(random.randint(5, 10)) # Jeda aman
            except:
                failed += 1

        await report.edit_text(f"✅ **Bulk Join Selesai!**\n🔥 Sukses: {success}\n❌ Gagal: {failed}\n🗑️ Folder dibersihkan.")

async def auto_promo():
    # Menangani Error 409 (Conflict) saat startup
    try:
        if not app.is_connected:
            await app.start()
    except errors.AuthKeyDuplicated:
        print("Error 409: Session bentrok! Menunggu restart...") #
        await asyncio.sleep(15)
        return

    await update_dashboard("🚀 **Status:** Userbot Online\n📡 **System:** Overpower Mode Aktif") #
    
    while True:
        await update_dashboard("🔍 **Status:** Memindai & Membersihkan Grup Sampah...") #
        
        groups = []
        try:
            async for dialog in app.get_dialogs(): #
                try:
                    if dialog.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]: #
                        groups.append(dialog.chat.id)
                except (errors.ChannelPrivate, errors.ChatAdminRequired, errors.UserBannedInChannel): #
                    try:
                        await app.leave_chat(dialog.chat.id) #
                    except: pass
                except Exception:
                    continue
        except Exception as e:
            await update_dashboard(f"⚠️ **Scan Terhambat:** {e}") #

        total_grup = len(groups) #
        if total_grup == 0:
            await update_dashboard("⚠️ **Status:** Tidak ada grup ditemukan!") #
            await asyncio.sleep(300)
            continue

        random.shuffle(groups) #
        success, failed, left = 0, 0, 0 #

        for index, chat_id in enumerate(groups):
            try:
                await app.send_message(chat_id, PROMO_TEXT)
                success += 1 #
                
            except (errors.ChatWriteForbidden, 
                    errors.UserBannedInChannel, 
                    errors.ChatAdminRequired, 
                    errors.ChannelPrivate,
                    errors.ChatInvalid,
                    errors.PeerIdInvalid): #
                try:
                    await app.leave_chat(chat_id)
                    left += 1 #
                except: pass
                
            except errors.FloodWait as e:
                await update_dashboard(f"⚠️ **FloodWait!** Limit `{e.value}` detik.") #
                await asyncio.sleep(e.value)
                try:
                    await app.send_message(chat_id, PROMO_TEXT)
                    success += 1
                except: failed += 1 #
                
            except Exception:
                failed += 1 #

            if (index + 1) % 10 == 0 or (index + 1) == total_grup:
                pct = ((index + 1) / total_grup) * 100 #
                stats = (
                    f"📤 **Status:** Promosi Massal Aktif\n\n"
                    f"📊 **Progres:** {index + 1}/{total_grup} ({pct:.1f}%)\n"
                    f"✅ **Terkirim:** {success}\n"
                    f"❌ **Gagal:** {failed}\n"
                    f"🚪 **Auto-Leave (Mati/Ban):** {left}\n\n"
                    f"ℹ️ *Grup bermasalah otomatis ditinggalkan.*"
                )
                await update_dashboard(stats) #

            # JEDA AMAN (Sangat penting agar akun tidak di-ban)
            await asyncio.sleep(random.randint(1, 6))

        await update_dashboard(
            f"🏁 **Status:** Putaran Selesai!\n\n"
            f"✅ **Total Berhasil:** {success}\n"
            f"❌ **Total Gagal:** {failed}\n"
            f"🚪 **Total Grup Dihapus:** {left}\n\n"
            f"💤 **Mode:** Istirahat (2 Jam)"
        ) #
        
        await asyncio.sleep(1200) # Istirahat 2 jam

if __name__ == "__main__":
    while True:
        try:
            app.run(auto_promo()) #
        except errors.AuthKeyDuplicated:
            print("Koneksi bentrok (409). Mematikan proses lama...") #
            asyncio.run(asyncio.sleep(15))
        except Exception as e:
            print(f"Sistem Restart: {e}") #
            asyncio.run(asyncio.sleep(10))