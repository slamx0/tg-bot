import os, sys, json, time, signal, logging, asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode

# ⚙️ CONFIG
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8651296935:AAHNhSrpra8FPuvy4XN5RaJwmzoaRoEYen8")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "5601271475"))
DATA_FILE = "bot_data.json"

# 🎨 POMPOM STYLE
L1 = "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰"
L2 = "╔══════════════════════╗"
L3 = "╚══════════════════════╝"
SPARK = "✨🔥💎⚡🌟🎬🍿🎥"

# 🎬 LOADING ANIMATION
LOADING_FRAMES = ["⏳", "⌛", "🎬", "📽️", "🎥", "🍿", "✨", "💫"]

# 📦 STORAGE
class Storage:
    def __init__(self):
        self.welcome_text = "⚡ 𝙒𝙚𝙡𝙘𝙤𝙢𝙚 𝙩𝙤 𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝘽𝙤𝙩 ⚡"
        self.welcome_media = None
        self.welcome_media_type = None
        self.setup_media = None
        self.setup_media_type = None
        self.welcome_apks = []
        self.more_apks = []
        self.temp_file = {}
        self.waiting_type = None
        self.total_users = set()
        self.broadcast_mode = False
        self.broadcast_data = None
        self.all_chats = {}
        self.load()
    
    def save(self):
        try:
            data = {
                'welcome_text': self.welcome_text,
                'welcome_media': self.welcome_media,
                'welcome_media_type': self.welcome_media_type,
                'setup_media': self.setup_media,
                'setup_media_type': self.setup_media_type,
                'welcome_apks': self.welcome_apks,
                'more_apks': self.more_apks,
                'total_users': list(self.total_users),
                'all_chats': self.all_chats
            }
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    
    def load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'total_users' in data:
                        self.total_users = set(data['total_users'])
                    if 'all_chats' in data:
                        self.all_chats = data['all_chats']
                    if 'welcome_text' in data:
                        self.welcome_text = data['welcome_text']
                    if 'welcome_media' in data:
                        self.welcome_media = data['welcome_media']
                    if 'welcome_media_type' in data:
                        self.welcome_media_type = data['welcome_media_type']
                    if 'setup_media' in data:
                        self.setup_media = data['setup_media']
                    if 'setup_media_type' in data:
                        self.setup_media_type = data['setup_media_type']
                    if 'welcome_apks' in data:
                        self.welcome_apks = data['welcome_apks']
                    if 'more_apks' in data:
                        self.more_apks = data['more_apks']
            except Exception:
                pass
    
    def add_user(self, user_id):
        self.total_users.add(user_id)
        self.save()
    
    def add_chat(self, chat_id, chat_type):
        self.all_chats[str(chat_id)] = chat_type
        self.save()

db = Storage()

# 🎹 KEYBOARDS
def user_kb():
    return ReplyKeyboardMarkup(
        [[f"🔥 𝐒𝐄𝐓𝐔𝐏", f"💎 𝐌𝐎𝐑𝐄 𝐀𝐏𝐏𝐒"]],
        resize_keyboard=True)

def admin_kb():
    return ReplyKeyboardMarkup(
        [[f"ℹ️ 𝐇𝐄𝐋𝐏", f"⭐ 𝐒𝐓𝐀𝐓𝐒"],
         [f"👑 𝐖𝐄𝐋𝐂𝐎𝐌𝐄", f"💎 𝐒𝐄𝐓𝐔𝐏"],
         [f"🔥 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐀𝐏𝐊", f"🔒 𝐌𝐎𝐑𝐄 𝐀𝐏𝐊"],
         [f"📢 𝐁𝐑𝐎𝐀𝐃𝐂𝐀𝐒𝐓"]],
        resize_keyboard=True)

def apk_sel_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐀𝐏𝐊", callback_data="w_apk")],
        [InlineKeyboardButton("💎 𝐌𝐎𝐑𝐄 𝐀𝐏𝐊", callback_data="m_apk")],
        [InlineKeyboardButton("❌ 𝐂𝐀𝐍𝐂𝐄𝐋", callback_data="cancel")]])

def med_sel_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ 𝐖𝐄𝐋𝐂𝐎𝐌𝐄", callback_data="w_med")],
        [InlineKeyboardButton("🔥 𝐒𝐄𝐓𝐔𝐏", callback_data="s_med")],
        [InlineKeyboardButton("❌ 𝐂𝐀𝐍𝐂𝐄𝐋", callback_data="cancel")]])

def yn_kb(p):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ 𝐘𝐄𝐒", callback_data=f"y_{p}"),
         InlineKeyboardButton("❌ 𝐍𝐎", callback_data=f"n_{p}")]])

def rm_kb(c):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑️ 𝐑𝐄𝐌𝐎𝐕𝐄", callback_data=c)]])

def bc_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 𝐒𝐄𝐍𝐃 𝐓𝐎 𝐀𝐋𝐋", callback_data="b_send")],
        [InlineKeyboardButton("👁️ 𝐏𝐑𝐄𝐕𝐈𝐄𝐖", callback_data="b_preview")],
        [InlineKeyboardButton("❌ 𝐂𝐀𝐍𝐂𝐄𝐋", callback_data="b_cancel")]])

# 📝 LOGGING
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 🎬 ANIMATION LOADER
async def pom_loader(msg, text="🎬 𝙇𝙤𝙖𝙙𝙞𝙣𝙜..."):
    loader_msg = await msg.reply_text("⏳")
    for frame in LOADING_FRAMES:
        try:
            await loader_msg.edit_text(f"{frame} {text}")
            await asyncio.sleep(0.15)
        except:
            pass
    return loader_msg

# 📢 BROADCAST
async def do_broadcast(context, content):
    s = 0
    f = 0
    targets = {}
    
    for uid in db.total_users:
        targets[str(uid)] = 'private'
    
    for cid, ctype in db.all_chats.items():
        if str(cid) not in targets:
            targets[str(cid)] = ctype
    
    for chat_id_str, chat_type in targets.items():
        try:
            chat_id = int(chat_id_str)
            
            if content['type'] == 'text':
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"📢 *𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧*\n\n{content['text']}",
                    parse_mode=ParseMode.MARKDOWN)
            
            elif content['type'] == 'photo':
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=content['file_id'],
                    caption=f"📢 *𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧*\n\n{content.get('caption','')}",
                    parse_mode=ParseMode.MARKDOWN)
            
            elif content['type'] == 'video':
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=content['file_id'],
                    caption=f"📢 *𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧*\n\n{content.get('caption','')}",
                    parse_mode=ParseMode.MARKDOWN)
            
            elif content['type'] == 'document':
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=content['file_id'],
                    caption=f"📢 *𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧*\n\n{content.get('caption','')}",
                    parse_mode=ParseMode.MARKDOWN)
            
            s += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            logger.error(f"Broadcast failed: {e}")
            f += 1
    
    return s, f

# 🚀 START
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    chat = update.effective_chat
    
    if chat.type in ['group', 'supergroup', 'channel']:
        db.add_chat(chat.id, chat.type)
    
    if chat.type == 'private':
        db.add_user(u.id)
    
    # ADMIN PANEL
    if u.id == ADMIN_ID and chat.type == 'private':
        db.broadcast_mode = False
        db.broadcast_data = None
        
        loader = await pom_loader(update.message, "🎥 𝙇𝙤𝙖𝙙𝙞𝙣𝙜 𝘼𝙙𝙢𝙞𝙣 𝙋𝙖𝙣𝙚𝙡...")
        
        admin_msg = (
            f"{L2}\n"
            f"🎬 𝙋𝙊𝙈𝙋𝙊𝙈 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇 🍿\n"
            f"{L3}\n\n"
            f"👑 𝘼𝙙𝙢𝙞𝙣 : {u.first_name}\n"
            f"📊 𝙐𝙨𝙚𝙧𝙨 : {len(db.total_users)}\n"
            f"⚙️ 𝙂𝙧𝙤𝙪𝙥𝙨 : {len(db.all_chats)}\n\n"
            f"{L1}\n"
            f"❤️ 𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝘽𝙤𝙩 𝘼𝙘𝙩𝙞𝙫𝙚 ❤️\n"
            f"{SPARK}"
        )
        
        await loader.delete()
        await update.message.reply_text(
            admin_msg,
            reply_markup=admin_kb(),
            parse_mode=ParseMode.MARKDOWN)
        return
    
    # GROUP WELCOME (FIXED)
    if chat.type in ['group', 'supergroup', 'channel']:
        loader = await pom_loader(update.message, "🎬 𝘼𝙣𝙞𝙢𝙖𝙩𝙞𝙣𝙜 𝙂𝙧𝙤𝙪𝙥 𝙒𝙚𝙡𝙘𝙤𝙢𝙚...")
        
        wcap = f"{L2}\n✨ 𝙂𝙍𝘼𝙉𝘿 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 ✨\n{L3}\n\n{db.welcome_text}"
        
        if db.welcome_media:
            try:
                if db.welcome_media_type == "photo":
                    await update.message.reply_photo(photo=db.welcome_media, caption=wcap, parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_video(video=db.welcome_media, caption=wcap, parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                logger.error(f"Welcome media error: {e}")
                await update.message.reply_text(wcap, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(wcap, parse_mode=ParseMode.MARKDOWN)
        
        if db.welcome_apks:
            for i, a in enumerate(db.welcome_apks, 1):
                try:
                    await update.message.reply_document(
                        document=a["file_id"],
                        caption=f"🔥 #{i} | {a.get('caption','')}")
                    await asyncio.sleep(0.3)
                except Exception as e:
                    logger.error(f"Welcome APK error: {e}")
        
        await loader.delete()
        await update.message.reply_text(
            "💎 𝙏𝙖𝙥 𝙤𝙣 𝙗𝙚𝙡𝙤𝙬 𝙗𝙪𝙩𝙩𝙤𝙣𝙨 💎",
            reply_markup=user_kb())
        return
    
    # PRIVATE WELCOME
    loader = await pom_loader(update.message, "🎬 𝘼𝙣𝙞𝙢𝙖𝙩𝙞𝙣𝙜 𝙂𝙧𝙖𝙣𝙙 𝙒𝙚𝙡𝙘𝙤𝙢𝙚...")
    
    wcap = f"{L2}\n✨ 𝙂𝙍𝘼𝙉𝘿 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 🔥\n💎 {u.first_name} 💎\n{L3}\n\n{db.welcome_text}"
    
    if db.welcome_media:
        try:
            if db.welcome_media_type == "photo":
                await update.message.reply_photo(photo=db.welcome_media, caption=wcap, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_video(video=db.welcome_media, caption=wcap, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Private welcome media error: {e}")
            await update.message.reply_text(wcap, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(wcap, parse_mode=ParseMode.MARKDOWN)
    
    for i, a in enumerate(db.welcome_apks, 1):
        try:
            await update.message.reply_document(
                document=a["file_id"],
                caption=f"🔥 #{i} | {a.get('caption','')}")
            await asyncio.sleep(0.3)
        except Exception as e:
            logger.error(f"Private welcome APK error: {e}")
    
    await loader.delete()
    await update.message.reply_text(
        "💎 𝙏𝙖𝙥 𝙤𝙣 𝙗𝙚𝙡𝙤𝙬 𝙗𝙪𝙩𝙩𝙤𝙣𝙨 💎",
        reply_markup=user_kb())

# 📱 APK RECEIVE
async def recv_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if update.effective_chat.type != 'private':
        return
    
    d = update.message.document
    if not d:
        return
    
    if db.broadcast_mode:
        db.broadcast_data = {'type': 'document', 'file_id': d.file_id, 'file_name': d.file_name, 'caption': d.file_name}
        await update.message.reply_text(
            f"{L2}\n📢 𝘽𝙍𝙊𝘼𝘿𝘾𝘼𝙎𝙏 𝘿𝙊𝘾𝙐𝙈𝙀𝙉𝙏\n{L3}\n\n📦 {d.file_name}\n\n𝘾𝙤𝙣𝙛𝙞𝙧𝙢?",
            reply_markup=bc_kb(),
            parse_mode=ParseMode.MARKDOWN)
        return
    
    db.temp_file = {"fid": d.file_id, "fname": d.file_name, "cap": d.file_name}
    await update.message.reply_text(
        f"{L2}\n📱 𝘼𝙋𝙆 𝙍𝙀𝘾𝙀𝙄𝙑𝙀𝘿\n{L3}\n\n🔥 {d.file_name}\n\n𝙎𝙚𝙡𝙚𝙘𝙩 𝙩𝙮𝙥𝙚:",
        reply_markup=apk_sel_kb(),
        parse_mode=ParseMode.MARKDOWN)

# 🖼️ MEDIA RECEIVE
async def recv_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if update.effective_chat.type != 'private':
        return
    
    m = update.message
    
    if db.broadcast_mode:
        if m.photo:
            db.broadcast_data = {'type': 'photo', 'file_id': m.photo[-1].file_id, 'caption': m.caption or ''}
            em = "🖼️ 𝙋𝙃𝙊𝙏𝙊"
        elif m.video:
            db.broadcast_data = {'type': 'video', 'file_id': m.video.file_id, 'caption': m.caption or ''}
            em = "🎬 𝙑𝙄𝘿𝙀𝙊"
        else:
            return
        await update.message.reply_text(
            f"{L2}\n📢 𝘽𝙍𝙊𝘼𝘿𝘾𝘼𝙎𝙏 {em}\n{L3}\n\n𝘾𝙤𝙣𝙛𝙞𝙧𝙢?",
            reply_markup=bc_kb(),
            parse_mode=ParseMode.MARKDOWN)
        return
    
    if m.photo:
        db.temp_file = {"type": "photo", "fid": m.photo[-1].file_id}
        em = "🖼️ 𝙋𝙃𝙊𝙏𝙊"
    elif m.video:
        db.temp_file = {"type": "video", "fid": m.video.file_id}
        em = "🎬 𝙑𝙄𝘿𝙀𝙊"
    else:
        return
    
    await update.message.reply_text(
        f"{L2}\n{em} 𝙍𝙀𝘾𝙀𝙄𝙑𝙀𝘿\n{L3}\n\n𝙎𝙚𝙡𝙚𝙘𝙩 𝙙𝙚𝙨𝙩𝙞𝙣𝙖𝙩𝙞𝙤𝙣:",
        reply_markup=med_sel_kb(),
        parse_mode=ParseMode.MARKDOWN)

# 🔘 CALLBACKS
async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = q.data
    uid = q.from_user.id
    
    if uid != ADMIN_ID:
        await q.answer("⛔ 𝘼𝙙𝙢𝙞𝙣 𝙊𝙣𝙡𝙮!", show_alert=True)
        return
    
    if d == "cancel":
        db.waiting_type = None
        db.temp_file = {}
        await q.edit_message_text("✘ 𝙋𝙧𝙤𝙘𝙚𝙨𝙨 𝘾𝙖𝙣𝙘𝙚𝙡𝙡𝙚𝙙...")
        return
    
    if d == "b_send":
        if not db.broadcast_data:
            await q.edit_message_text("❌ 𝙉𝙤 𝙘𝙤𝙣𝙩𝙚𝙣𝙩!")
            return
        
        total = len(db.total_users) + len(db.all_chats)
        await q.edit_message_text(f"🚀 𝙎𝙚𝙣𝙙𝙞𝙣𝙜 𝙩𝙤 {total} 𝙘𝙝𝙖𝙩𝙨...")
        
        sent, failed = await do_broadcast(context, db.broadcast_data)
        
        await q.edit_message_text(
            f"{L2}\n📢 𝘽𝙍𝙊𝘼𝘿𝘾𝘼𝙎𝙏 𝘿𝙊𝙉𝙀\n{L3}\n\n"
            f"✅ 𝙎𝙚𝙣𝙩 : {sent}\n"
            f"❌ 𝙁𝙖𝙞𝙡𝙚𝙙 : {failed}\n"
            f"👥 𝙐𝙨𝙚𝙧𝙨 : {len(db.total_users)}\n"
            f"⚙️ 𝙂𝙧𝙤𝙪𝙥𝙨 : {len(db.all_chats)}",
            parse_mode=ParseMode.MARKDOWN)
        
        db.broadcast_mode = False
        db.broadcast_data = None
        return
    
    if d == "b_preview":
        if not db.broadcast_data:
            await q.edit_message_text("❌ 𝙉𝙤 𝙘𝙤𝙣𝙩𝙚𝙣𝙩!")
            return
        try:
            if db.broadcast_data['type'] == 'text':
                await q.message.reply_text(f"👁️ *𝙋𝙍𝙀𝙑𝙄𝙀𝙒*\n\n{db.broadcast_data['text']}", parse_mode=ParseMode.MARKDOWN)
            elif db.broadcast_data['type'] == 'photo':
                await q.message.reply_photo(photo=db.broadcast_data['file_id'], caption=f"👁️ *𝙋𝙍𝙀𝙑𝙄𝙀𝙒*", parse_mode=ParseMode.MARKDOWN)
            elif db.broadcast_data['type'] == 'video':
                await q.message.reply_video(video=db.broadcast_data['file_id'], caption=f"👁️ *𝙋𝙍𝙀𝙑𝙄𝙀𝙒*", parse_mode=ParseMode.MARKDOWN)
            elif db.broadcast_data['type'] == 'document':
                await q.message.reply_document(document=db.broadcast_data['file_id'], caption=f"👁️ *𝙋𝙍𝙀𝙑𝙄𝙀𝙒*", parse_mode=ParseMode.MARKDOWN)
            await q.answer("👁️ 𝙋𝙧𝙚𝙫𝙞𝙚𝙬 𝙨𝙚𝙣𝙩!", show_alert=True)
        except:
            await q.answer("❌ 𝙀𝙧𝙧𝙤𝙧!", show_alert=True)
        return
    
    if d == "b_cancel":
        db.broadcast_mode = False
        db.broadcast_data = None
        await q.edit_message_text("✘ 𝘽𝙧𝙤𝙖𝙙𝙘𝙖𝙨𝙩 𝘾𝙖𝙣𝙘𝙚𝙡𝙡𝙚𝙙...")
        return
    
    if d == "w_apk":
        await q.edit_message_text(
            f"{L2}\n📱 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝘼𝙋𝙆 𝙎𝙀𝙏𝙐𝙋\n{L3}\n\n𝘼𝙙𝙙 𝙘𝙪𝙨𝙩𝙤𝙢 𝙢𝙚𝙨𝙨𝙖𝙜𝙚?",
            reply_markup=yn_kb("w_apk"), parse_mode=ParseMode.MARKDOWN)
    
    elif d == "y_w_apk":
        db.waiting_type = "w_apk"
        await q.edit_message_text(
            f"{L2}\n✎ 𝙎𝙀𝙉𝘿 𝙔𝙊𝙐𝙍 𝙈𝙀𝙎𝙎𝘼𝙂𝙀\n{L3}\n\n𝙉𝙤𝙬 𝙨𝙚𝙣𝙙 𝙩𝙝𝙚 𝙢𝙚𝙨𝙨𝙖𝙜𝙚...",
            parse_mode=ParseMode.MARKDOWN)
    
    elif d == "n_w_apk":
        db.welcome_apks.append({"file_id": db.temp_file["fid"], "caption": db.temp_file["cap"]})
        db.save()
        db.waiting_type = None
        db.temp_file = {}
        await q.edit_message_text(
            f"{L2}\n✅ 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝘼𝙋𝙆 𝘼𝘿𝘿𝙀𝘿\n{L3}\n\n𝙎𝙖𝙫𝙚𝙙 𝙨𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡𝙡𝙮.",
            parse_mode=ParseMode.MARKDOWN)
    
    elif d == "m_apk":
        await q.edit_message_text(
            f"{L2}\n📱 𝙈𝙊𝙍𝙀 𝘼𝙋𝙆 𝙎𝙀𝙏𝙐𝙋\n{L3}\n\n𝘼𝙙𝙙 𝙘𝙪𝙨𝙩𝙤𝙢 𝙢𝙚𝙨𝙨𝙖𝙜𝙚?",
            reply_markup=yn_kb("m_apk"), parse_mode=ParseMode.MARKDOWN)
    
    elif d == "y_m_apk":
        db.waiting_type = "m_apk"
        await q.edit_message_text(
            f"{L2}\n✎ 𝙎𝙀𝙉𝘿 𝙔𝙊𝙐𝙍 𝙈𝙀𝙎𝙎𝘼𝙂𝙀\n{L3}\n\n𝙉𝙤𝙬 𝙨𝙚𝙣𝙙 𝙩𝙝𝙚 𝙢𝙚𝙨𝙨𝙖𝙜𝙚...",
            parse_mode=ParseMode.MARKDOWN)
    
    elif d == "n_m_apk":
        db.more_apks.append({"file_id": db.temp_file["fid"], "caption": db.temp_file["cap"]})
        db.save()
        db.waiting_type = None
        db.temp_file = {}
        await q.edit_message_text(
            f"{L2}\n✅ 𝙈𝙊𝙍𝙀 𝘼𝙋𝙆 𝘼𝘿𝘿𝙀𝘿\n{L3}\n\n𝙎𝙖𝙫𝙚𝙙 𝙨𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡𝙡𝙮.",
            parse_mode=ParseMode.MARKDOWN)
    
    elif d == "w_med":
        await q.edit_message_text(
            f"{L2}\n⭐ 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝙈𝙀𝘿𝙄𝘼\n{L3}\n\n𝘼𝙙𝙙 𝙒𝙚𝙡𝙘𝙤𝙢𝙚 𝙢𝙚𝙨𝙨𝙖𝙜𝙚?",
            reply_markup=yn_kb("w_med"), parse_mode=ParseMode.MARKDOWN)
    
    elif d == "y_w_med":
        db.waiting_type = "w_med"
        await q.edit_message_text(
            f"{L2}\n✎ 𝙎𝙀𝙉𝘿 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝙈𝙀𝙎𝙎𝘼𝙂𝙀\n{L3}\n\n𝙉𝙤𝙬 𝙨𝙚𝙣𝙙 𝙩𝙝𝙚 𝙮𝙚...",
            parse_mode=ParseMode.MARKDOWN)
    
    elif d == "n_w_med":
        db.welcome_media = db.temp_file["fid"]
        db.welcome_media_type = db.temp_file["type"]
        db.save()
        db.waiting_type = None
        db.temp_file = {}
        await q.edit_message_text(
            f"{L2}\n✅ 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝙈𝙀𝘿𝙄𝘼 𝙐𝙋𝘿𝘼𝙏𝙀𝘿\n{L3}\n\n𝙎𝙖𝙫𝙚𝙙 𝙨𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡𝙡𝙮.",
            parse_mode=ParseMode.MARKDOWN)
    
    elif d == "s_med":
        db.setup_media = db.temp_file["fid"]
        db.setup_media_type = db.temp_file["type"]
        db.save()
        db.waiting_type = None
        db.temp_file = {}
        await q.edit_message_text(
            f"{L2}\n✅ 𝙎𝙀𝙏𝙐𝙋 𝙈𝙀𝘿𝙄𝘼 𝙐𝙋𝘿𝘼𝙏𝙀𝘿\n{L3}\n\n𝙎𝙖𝙫𝙚𝙙 𝙨𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡𝙡𝙮.",
            parse_mode=ParseMode.MARKDOWN)
    
    elif d == "rm_w":
        db.welcome_media = None
        db.welcome_media_type = None
        db.save()
        await q.message.delete()
    
    elif d == "rm_s":
        db.setup_media = None
        db.setup_media_type = None
        db.save()
        await q.message.delete()
    
    elif d.startswith("rmw_"):
        try:
            idx = int(d.split("_")[1])
            db.welcome_apks.pop(idx)
            db.save()
            await q.message.delete()
        except:
            await q.answer("❌ 𝙍𝙚𝙢𝙤𝙫𝙚 𝙛𝙖𝙞𝙡𝙚𝙙!", show_alert=True)
    
    elif d.startswith("rmm_"):
        try:
            idx = int(d.split("_")[1])
            db.more_apks.pop(idx)
            db.save()
            await q.message.delete()
        except:
            await q.answer("❌ 𝙍𝙚𝙢𝙤𝙫𝙚 𝙛𝙖𝙞𝙡𝙚𝙙!", show_alert=True)

# 💬 TEXT HANDLER
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    txt = update.message.text
    chat = update.effective_chat
    
    if chat.type in ['group', 'supergroup', 'channel']:
        db.add_chat(chat.id, chat.type)
        
        if "𝐒𝐄𝐓𝐔𝐏" in txt:
            if db.setup_media:
                if db.setup_media_type == "photo":
                    await update.message.reply_photo(
                        photo=db.setup_media,
                        caption=f"{L2}\n🔥 𝙎𝙀𝙏𝙐𝙋 𝙂𝙐𝙄𝘿𝙀\n{L3}\n\n✨ 𝙁𝙤𝙡𝙡𝙤𝙬 𝙨𝙩𝙚𝙥𝙨 ✓",
                        parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_video(
                        video=db.setup_media,
                        caption=f"{L2}\n🔥 𝙎𝙀𝙏𝙐𝙋 𝙑𝙄𝘿𝙀𝙊\n{L3}\n\n✨ 𝙒𝙝𝙖𝙩sapp 𝙛𝙪𝙡𝙡 𝙫𝙞𝙙𝙚𝙤 ✓",
                        parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(
                    f"⚠️ 𝙎𝙀𝙏𝙐𝙋 𝙉𝙊𝙏 𝘼𝙑𝘼𝙄𝙇𝘼𝘽𝙇𝙀\n\nℹ️ 𝙏𝙧𝙮 𝙖𝙜𝙖𝙞𝙣 𝙡𝙖𝙩𝙚𝙧.",
                    parse_mode=ParseMode.MARKDOWN)

        elif "𝐌𝐎𝐑𝐄 𝐀𝐏𝐏𝐒" in txt:
            if db.more_apks:
                for i, a in enumerate(db.more_apks, 1):
                    try:
                        await update.message.reply_document(
                            document=a["file_id"],
                            caption=f"{L2}\n💎 𝙋𝙍𝙀𝙈𝙄𝙐𝙈 𝘼𝙋𝙋 #{i}\n{L3}\n\n➥ {a.get('caption', '𝙉𝙤 𝘾𝙖𝙥𝙩𝙞𝙤𝙣')}",
                            parse_mode=ParseMode.MARKDOWN)
                    except:
                        pass
            else:
                await update.message.reply_text(
                    f"⚠️ 𝙉𝙊 𝘼𝙋𝙋𝙎 𝘼𝙑𝘼𝙄𝙇𝘼𝘽𝙇𝙀\n\nℹ️ 𝙉𝙚𝙬 𝙖𝙥𝙥𝙨 𝙘𝙤𝙢𝙞𝙣𝙜 𝙨𝙤𝙤𝙣.",
                    parse_mode=ParseMode.MARKDOWN)
        return
    
    if uid == ADMIN_ID:
        if db.waiting_type:
            await handle_input(update, context)
            return
        
        if db.broadcast_mode:
            db.broadcast_data = {'type': 'text', 'text': txt}
            await update.message.reply_text(
                f"{L2}\n📢 𝘽𝙍𝙊𝘼𝘿𝘾𝘼𝙎𝙏 𝙏𝙀𝙓𝙏\n{L3}\n\n✨ {txt[:200]}\n\n𝘾𝙤𝙣𝙛𝙞𝙧𝙢?",
                reply_markup=bc_kb(), parse_mode=ParseMode.MARKDOWN)
            return
        
        if "𝐇𝐄𝐋𝐏" in txt:
            await update.message.reply_text(
                f"{L2}\n📚 𝘼𝘿𝙈𝙄𝙉 𝙃𝙀𝙇𝙋\n{L3}\n\n"
                f"🚀 𝙎𝙚𝙣𝙙 𝘼𝙋𝙆 - 𝘽𝙤𝙩 𝙖𝙨𝙠𝙨 𝙩𝙮𝙥𝙚\n"
                f"🖼️ 𝙎𝙚𝙣𝙙 𝙋𝙝𝙤𝙩𝙤/𝙑𝙞𝙙𝙚𝙤 - 𝘽𝙤𝙩 𝙖𝙨𝙠𝙨 𝙙𝙚𝙨𝙩\n"
                f"⚙️ 𝘽𝙪𝙩𝙩𝙤𝙣𝙨 - 𝙈𝙖𝙣𝙖𝙜𝙚 𝙘𝙤𝙣𝙩𝙚𝙣𝙩\n"
                f"📢 𝘽𝙍𝙊𝘼𝘿𝘾𝘼𝙎𝙏 - 𝙎𝙚𝙣𝙙 𝙩𝙤 𝙖𝙡𝙡\n\n"
                f"❤️ 𝙋𝙍𝙀𝙈𝙄𝙐𝙈 𝘽𝙊𝙏",
                parse_mode=ParseMode.MARKDOWN)
        
        elif "𝐒𝐓𝐀𝐓𝐒" in txt:
            await update.message.reply_text(
                f"{L2}\n📊 𝘽𝙊𝙏 𝙎𝙏𝘼𝙏𝙎\n{L3}\n\n"
                f"🔥 𝙒𝙚𝙡𝙘𝙤𝙢𝙚 𝘼𝙋𝙆𝙨 : {len(db.welcome_apks)}\n"
                f"💎 𝙈𝙤𝙧𝙚 𝘼𝙋𝙆𝙨 : {len(db.more_apks)}\n"
                f"👥 𝙐𝙨𝙚𝙧𝙨 : {len(db.total_users)}\n"
                f"⚙️ 𝙂𝙧𝙤𝙪𝙥𝙨 : {len(db.all_chats)}\n\n"
                f"🚀 𝙎𝙔𝙎𝙏𝙀𝙈 𝙊𝙉𝙇𝙄𝙉𝙀",
                parse_mode=ParseMode.MARKDOWN)
        
        elif "𝐁𝐑𝐎𝐀𝐃𝐂𝐀𝐒𝐓" in txt:
            db.broadcast_mode = True
            db.broadcast_data = None
            await update.message.reply_text(
                f"{L2}\n📢 𝘽𝙍𝙊𝘼𝘿𝘾𝘼𝙎𝙏 𝙈𝙊𝘿𝙀\n{L3}\n\n"
                f"ℹ️ 𝙉𝙤𝙬 𝙨𝙚𝙣𝙙:\n"
                f"✨ • 𝙏𝙚𝙭𝙩\n"
                f"🖼️ • 𝙋𝙝𝙤𝙩𝙤\n"
                f"🎬 • 𝙑𝙞𝙙𝙚𝙤\n"
                f"📦 • 𝘿𝙤𝙘𝙪𝙢𝙚𝙣𝙩\n\n"
                f"⚠️ /start 𝙩𝙤 𝙘𝙖𝙣𝙘𝙚𝙡",
                parse_mode=ParseMode.MARKDOWN)
        
        elif "𝐖𝐄𝐋𝐂𝐎𝐌𝐄" in txt and "𝐀𝐏𝐊" not in txt:
            if db.welcome_media:
                if db.welcome_media_type == "photo":
                    await update.message.reply_photo(
                        photo=db.welcome_media,
                        caption=f"{L2}\n⭐ 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝙋𝙍𝙀𝙑𝙄𝙀𝙒\n{L3}\n\n{db.welcome_text}\n\n✅ 𝘼𝙘𝙩𝙞𝙫𝙚",
                        reply_markup=rm_kb("rm_w"), parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_video(
                        video=db.welcome_media,
                        caption=f"{L2}\n⭐ 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝙋𝙍𝙀𝙑𝙄𝙀𝙒\n{L3}\n\n{db.welcome_text}\n\n✅ 𝘼𝙘𝙩𝙞𝙫𝙚",
                        reply_markup=rm_kb("rm_w"), parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(
                    f"⚠️ 𝙉𝙊 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝙈𝙀𝘿𝙄𝘼\n\nℹ️ 𝙐𝙥𝙡𝙤𝙖𝙙 𝙛𝙞𝙧𝙨𝙩.",
                    parse_mode=ParseMode.MARKDOWN)
        
        elif "𝐒𝐄𝐓𝐔𝐏" in txt:
            if db.setup_media:
                if db.setup_media_type == "photo":
                    await update.message.reply_photo(
                        photo=db.setup_media,
                        caption=f"{L2}\n🔥 𝙎𝙀𝙏𝙐𝙋 𝙋𝙍𝙀𝙑𝙄𝙀𝙒\n{L3}\n\n✅ 𝘼𝙘𝙩𝙞𝙫𝙚",
                        reply_markup=rm_kb("rm_s"), parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_video(
                        video=db.setup_media,
                        caption=f"{L2}\n🔥 𝙎𝙀𝙏𝙐𝙋 𝙑𝙄𝘿𝙀𝙊\n{L3}\n\n✅ 𝘼𝙘𝙩𝙞𝙫𝙚",
                        reply_markup=rm_kb("rm_s"), parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(
                    f"⚠️ 𝙉𝙊 𝙎𝙀𝙏𝙐𝙋 𝙈𝙀𝘿𝙄𝘼\n\nℹ️ 𝙐𝙥𝙡𝙤𝙖𝙙 𝙛𝙞𝙧𝙨𝙩.",
                    parse_mode=ParseMode.MARKDOWN)
        
        elif "𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐀𝐏𝐊" in txt:
            if db.welcome_apks:
                for i, a in enumerate(db.welcome_apks):
                    try:
                        await update.message.reply_document(
                            document=a["file_id"],
                            caption=f"{L2}\n🔥 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝘼𝙋𝙆 #{i+1}\n{L3}\n\n➥ {a.get('caption', '𝙉𝙤 𝘾𝙖𝙥𝙩𝙞𝙤𝙣')}",
                            reply_markup=rm_kb(f"rmw_{i}"), parse_mode=ParseMode.MARKDOWN)
                    except:
                        pass
            else:
                await update.message.reply_text(
                    f"⚠️ 𝙉𝙊 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝘼𝙋𝙆𝙎\n\nℹ️ 𝙎𝙚𝙣𝙙 𝘼𝙋𝙆 𝙩𝙤 𝙖𝙙𝙙.",
                    parse_mode=ParseMode.MARKDOWN)
        
        elif "𝐌𝐎𝐑𝐄 𝐀𝐏𝐊" in txt:
            if db.more_apks:
                for i, a in enumerate(db.more_apks):
                    try:
                        await update.message.reply_document(
                            document=a["file_id"],
                            caption=f"{L2}\n💎 𝙈𝙊𝙍𝙀 𝘼𝙋𝙆 #{i+1}\n{L3}\n\n➥ {a.get('caption', '𝙉𝙤 𝘾𝙖𝙥𝙩𝙞𝙤𝙣')}",
                            reply_markup=rm_kb(f"rmm_{i}"), parse_mode=ParseMode.MARKDOWN)
                    except:
                        pass
            else:
                await update.message.reply_text(
                    f"⚠️ 𝙉𝙊 𝙈𝙊𝙍𝙀 𝘼𝙋𝙆𝙎\n\nℹ️ 𝙎𝙚𝙣𝙙 𝘼𝙋𝙆 𝙩𝙤 𝙖𝙙𝙙.",
                    parse_mode=ParseMode.MARKDOWN)
    
    else:
        if "𝐒𝐄𝐓𝐔𝐏" in txt:
            if db.setup_media:
                if db.setup_media_type == "photo":
                    await update.message.reply_photo(
                        photo=db.setup_media,
                        caption=f"{L2}\n🔥 𝙎𝙀𝙏𝙐𝙋 𝙂𝙐𝙄𝘿𝙀\n{L3}\n\n✨ 𝙁𝙤𝙡𝙡𝙤𝙬 𝙨𝙩𝙚𝙥𝙨 ✓",
                        parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_video(
                        video=db.setup_media,
                        caption=f"{L2}\n🔥 𝙎𝙀𝙏𝙐𝙋 𝙑𝙄𝘿𝙀𝙊\n{L3}\n\n✨ 𝙒𝙝𝙖𝙩sapp 𝙛𝙪𝙡𝙡 𝙫𝙞𝙙𝙚𝙤 ✓",
                        parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(
                    f"⚠️ 𝙎𝙀𝙏𝙐𝙋 𝙉𝙊𝙏 𝘼𝙑𝘼𝙄𝙇𝘼𝘽𝙇𝙀\n\nℹ️ 𝙏𝙧𝙮 𝙖𝙜𝙖𝙞𝙣 𝙡𝙖𝙩𝙚𝙧.",
                    parse_mode=ParseMode.MARKDOWN)

        elif "𝐌𝐎𝐑𝐄 𝐀𝐏𝐏𝐒" in txt:
            if db.more_apks:
                for i, a in enumerate(db.more_apks, 1):
                    try:
                        await update.message.reply_document(
                            document=a["file_id"],
                            caption=f"{L2}\n💎 𝙋𝙍𝙀𝙈𝙄𝙐𝙈 𝘼𝙋𝙋 #{i}\n{L3}\n\n➥ {a.get('caption', '𝙉𝙤 𝘾𝙖𝙥𝙩𝙞𝙤𝙣')}",
                            parse_mode=ParseMode.MARKDOWN)
                    except:
                        pass
            else:
                await update.message.reply_text(
                    f"⚠️ 𝙉𝙊 𝘼𝙋𝙋𝙎 𝘼𝙑𝘼𝙄𝙇𝘼𝘽𝙇𝙀\n\nℹ️ 𝙉𝙚𝙬 𝙖𝙥𝙥𝙨 𝙘𝙤𝙢𝙞𝙣𝙜 𝙨𝙤𝙤𝙣.",
                    parse_mode=ParseMode.MARKDOWN)

# ✏️ INPUT HANDLER
async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text
    wt = db.waiting_type
    
    if wt == "w_med":
        db.welcome_text = txt
        db.welcome_media = db.temp_file["fid"]
        db.welcome_media_type = db.temp_file["type"]
        db.save()
        await update.message.reply_text(
            f"{L2}\n✅ 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝙐𝙋𝘿𝘼𝙏𝙀𝘿\n{L3}\n\n✨ 𝙎𝙖𝙫𝙚𝙙 𝙨𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡𝙡𝙮 ✅",
            parse_mode=ParseMode.MARKDOWN)
    
    elif wt == "w_apk":
        db.welcome_apks.append({"file_id": db.temp_file["fid"], "caption": txt})
        db.save()
        await update.message.reply_text(
            f"{L2}\n✅ 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝘼𝙋𝙆 𝘼𝘿𝘿𝙀𝘿\n{L3}\n\n🔥 𝙎𝙖𝙫𝙚𝙙 𝙩𝙤 𝙡𝙞𝙨𝙩 ✅",
            parse_mode=ParseMode.MARKDOWN)
    
    elif wt == "m_apk":
        db.more_apks.append({"file_id": db.temp_file["fid"], "caption": txt})
        db.save()
        await update.message.reply_text(
            f"{L2}\n✅ 𝙈𝙊𝙍𝙀 𝘼𝙋𝙆 𝘼𝘿𝘿𝙀𝘿\n{L3}\n\n💎 𝙎𝙖𝙫𝙚𝙙 𝙩𝙤 𝙡𝙞𝙨𝙩 ✅",
            parse_mode=ParseMode.MARKDOWN)
    
    db.waiting_type = None
    db.temp_file = {}

# 🏃 MAIN FUNCTION - SIMPLE AND CLEAN
def main():
    print(f"\n🎬 𝙋𝙊𝙈𝙋𝙊𝙈 𝙋𝙍𝙀𝙈𝙄𝙐𝙈 𝘽𝙊𝙏 🍿\n")
    print(f"⏰ Start time: {datetime.now()}\n")
    
    # Create Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CallbackQueryHandler(callbacks))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, recv_media))
    application.add_handler(MessageHandler(filters.Document.ALL, recv_apk))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    print("✅ Bot Running...\n")
    
    # Run bot - SIMPLE POLLING
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
