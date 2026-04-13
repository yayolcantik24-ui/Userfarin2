import asyncio
import random
import os
import re
from datetime import datetime
import pytz
from pyrogram import Client, enums, errors, raw

# --- CONFIGURATION (RAILWAY) ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
LOG_CHANNEL = "@farinmodssv2"
WIB = pytz.timezone('Asia/Jakarta')

# --- KONTEN PROMOSI TERBARU FARIN SHOP ---
PROMO_TEXT = (
"🚀 **FARIN SHOP – LAYANAN OTP TERCEPAT & TERMURAH!**\n\n"
"Butuh OTP cepat & murah untuk WhatsApp, Telegram, Instagram, Facebook, dan banyak aplikasi lainnya?\n"
"**Farin Shop solusinya!**\n\n"
"✅ **Kenapa Pilih Farin Shop?**\n"
"• Proses super cepat – OTP masuk dalam detik\n"
"• Harga terjangkau – ada yang cuma 900p!\n"
"• Banyak negara & server tersedia\n"
"• Auto Order 24/7 – bot selalu online\n\n"
"⚠️ **Garansi 100%** – Jika gagal, saldo dikembalikan\n\n"
"🤖 **Order Sekarang di Telegram:**\n"
"@FarinShop_bot\n\n"
"**BOT CEK ID TELEGRAM NIH:**\n"
"@cekid_kubot"
)

status_msg_id = None
promo_log_id = None # Khusus untuk edit log progres promo

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

async def update_promo_log(content):
    """Fungsi khusus untuk edit pesan log agar tidak spam"""
    global promo_log_id
    try:
        if promo_log_id:
            await app.edit_message_text(LOG_CHANNEL, promo_log_id, content)
        else:
            msg = await app.send_message(LOG_CHANNEL, content)
            promo_log_id = msg.id
    except:
        try:
            msg = await app.send_message(LOG_CHANNEL, content)
            promo_log_id = msg.id
        except: pass

# --- FITUR: BULK JOIN ---
@app.on_message(enums.ChatType.PRIVATE)
async def handle_bulk_join(client, message):
    if message.text and message.text.lower().startswith("/join"):
        links = re.findall(r'(https?://t\.me/\S+)', message.text)
        if not links:
            await message.reply("❌ Tidak ada link ditemukan.")
            return

        report = await message.reply(f"⏳ Memproses **{len(links)}** link...")
        success, failed = 0, 0
        error_logs = ""

        for link in links:
            try:
                slug = link.split('/')[-1]
                if "addlist" in link:
                    check = await client.invoke(raw.functions.chatlists.CheckChatlistInvite(slug=slug))
                    input_peers = []
                    for chat in check.chats:
                        if isinstance(chat, raw.types.Chat) or isinstance(chat, raw.types.Channel):
                            if isinstance(chat, raw.types.Chat):
                                input_peers.append(raw.types.InputPeerChat(chat_id=chat.id))
                            else:
                                input_peers.append(raw.types.InputPeerChannel(channel_id=chat.id, access_hash=chat.access_hash))
                    await client.invoke(raw.functions.chatlists.JoinChatlistInvite(slug=slug, peers=input_peers))
                    await asyncio.sleep(2)
                    try:
                        res = await client.invoke(raw.functions.messages.GetDialogFilters())
                        for filt in res:
                            if hasattr(filt, "id") and filt.id != 0:
                                await client.invoke(raw.functions.messages.UpdateDialogFilter(id=filt.id))
                    except: pass
                    success += 1
                else:
                    await client.join_chat(link)
                    success += 1
                await asyncio.sleep(random.randint(3, 7))
            except errors.FloodWait as e:
                error_logs += f"• {link}: FloodWait {e.value}s\n"
                failed += 1
            except Exception as e:
                error_logs += f"• {link}: {str(e)}\n"
                failed += 1

        final_msg = f"✅ **Bulk Join Selesai!**\n🔥 Sukses: {success}\n❌ Gagal: {failed}\n"
        if error_logs:
            final_msg += f"\n**Detail Error:**\n{error_logs}"
        await report.edit_text(final_msg)

# --- FITUR: AUTO PROMO (dengan log error lengkap) ---
async def auto_promo():
    global promo_log_id
    try:
        if not app.is_connected:
            await app.start()
    except: pass

    await update_dashboard("🚀 **Status:** Online\n📡 **System:** Fixed Join Folder Mode")
    
    while True:
        promo_log_id = None
        await update_dashboard("🔍 **Status:** Scanning Groups...")
        groups = []
        try:
            async for dialog in app.get_dialogs():
                if dialog.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                    groups.append(dialog.chat.id)
        except: pass

        if not groups:
            await update_dashboard("⚠️ **Status:** Grup Kosong.")
            await asyncio.sleep(300)
            continue

        random.shuffle(groups)
        s, f, l = 0, 0, 0
        
        # Cooldown untuk error log (agar tidak spam channel)
        last_error_log_time = 0

        for index, chat_id in enumerate(groups):
            try:
                await app.send_message(chat_id, PROMO_TEXT)
                s += 1
                
                current_time = datetime.now(WIB).strftime("%H:%M:%S")
                log_text = (
                    f"📤 **PROMO PROGRESS**\n"
                    f"{'─'*20}\n"
                    f"✅ Sukses: **{s}**\n"
                    f"❌ Gagal: **{f}**\n"
                    f"🚪 Keluar: **{l}**\n\n"
                    f"📍 Last: `{chat_id}`\n"
                    f"📊 Progress: {index+1}/{len(groups)}\n"
                    f"🕒 Time: {current_time} WIB"
                )
                await update_promo_log(log_text)

            except (errors.ChatWriteForbidden, errors.UserBannedInChannel, errors.ChannelPrivate):
                try:
                    await app.leave_chat(chat_id)
                    l += 1
                    # NOTIFIKASI DIHAPUS (tidak kirim pesan ke channel)
                except: pass

            except errors.FloodWait as e:
                await app.send_message(LOG_CHANNEL, f"⏳ **FLOODWAIT**\nMenunggu {e.value} detik...")
                await asyncio.sleep(e.value)
                try:
                    await app.send_message(chat_id, PROMO_TEXT)
                    s += 1
                except:
                    f += 1

            # ========== PENANGANAN ERROR LENGKAP ==========
            except errors.PeerIdInvalid:
                f += 1
                now_ts = datetime.now().timestamp()
                if now_ts - last_error_log_time >= 5:
                    await app.send_message(LOG_CHANNEL, f"⚠️ **PeerIdInvalid**\nGrup `{chat_id}` tidak valid atau bot tidak pernah join.")
                    last_error_log_time = now_ts

            except errors.ChatAdminRequired:
                f += 1
                try:
                    await app.leave_chat(chat_id)
                    l += 1
                    # NOTIFIKASI DIHAPUS
                except:
                    pass

            except errors.RPCError as e:
                f += 1
                error_str = str(e)
                
                # 1. Grup di-restrict oleh Telegram -> leave tanpa notif
                if "CHAT_RESTRICTED" in error_str:
                    try:
                        await app.leave_chat(chat_id)
                        l += 1
                        # NOTIFIKASI DIHAPUS
                    except:
                        pass
                
                # 2. Grup hanya admin / plain text dilarang -> leave tanpa notif
                elif "CHAT_SEND_PLAIN_FORBIDDEN" in error_str or "SEND_PLAIN" in error_str:
                    try:
                        await app.leave_chat(chat_id)
                        l += 1
                        # NOTIFIKASI DIHAPUS
                    except:
                        pass
                
                # 3. Slowmode -> tidak leave, hanya log (biarkan tetap ada untuk monitoring)
                elif "SLOWMODE_WAIT" in error_str:
                    import re
                    wait_match = re.search(r'wait of (\d+) seconds', error_str)
                    wait_time = wait_match.group(1) if wait_match else "?"
                    await app.send_message(LOG_CHANNEL, f"🐢 **SLOWMODE DETECTED**\nGrup `{chat_id}` memiliki jeda {wait_time} detik. Bot skip (tidak keluar).")
                
                # 4. FloodWait sudah ditangani di atas, jika masih masuk sini abaikan
                elif "FLOOD_WAIT" not in error_str:
                    now_ts = datetime.now().timestamp()
                    if now_ts - last_error_log_time >= 5:
                        await app.send_message(LOG_CHANNEL, f"❌ **RPCError (unhandled)**\nGrup: `{chat_id}`\nDetail: `{e}`")
                        last_error_log_time = now_ts

            except Exception as e:
                f += 1
                now_ts = datetime.now().timestamp()
                if now_ts - last_error_log_time >= 5:
                    await app.send_message(LOG_CHANNEL, f"🔥 **UNKNOWN ERROR**\nGrup: `{chat_id}`\nError: `{type(e).__name__}: {e}`")
                    last_error_log_time = now_ts
            # ===================================================

            # Update Dashboard Utama setiap 10 grup
            if (index + 1) % 10 == 0 or (index + 1) == len(groups):
                pct = ((index + 1) / len(groups)) * 100
                await update_dashboard(f"📤 **Promo Aktif**\n📊 {index+1}/{len(groups)} ({pct:.1f}%)\n✅ {s} | ❌ {f} | 🚪 {l}")

            await asyncio.sleep(random.uniform(1.5, 5.0))
            
        await update_dashboard(f"🏁 **Selesai!**\n✅ {s} | 🚪 {l}\n💤 Istirahat: 10 menit")
        await app.send_message(LOG_CHANNEL, f"🏁 **PROMO SELESAI**\nBerhasil promosi ke {s} grup. Bot istirahat dulu.")
        await asyncio.sleep(2000)

if __name__ == "__main__":
    while True:
        try:
            app.run(auto_promo())
        except Exception:
            asyncio.run(asyncio.sleep(10))