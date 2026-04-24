import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# --- CONFIGURATION ---
TOKEN = '8639241153:AAGcL6T6bgJ1QdccyVb4fuLxq2qgTIm3wIo'
ADMIN_ID = 7311138952  
JOIN_REWARD = 5
REF_REWARD = 30
MIN_WITHDRAW = 100

# --- DATABASE SETUP ---
conn = sqlite3.connect('axel_v10_final.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0, wallet_type TEXT, wallet_num TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS completed_tasks (user_id INTEGER, task_id INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS referrals (user_id INTEGER PRIMARY KEY, referred_by INTEGER)''')

# ဒီနေရာမှာ AUTOINCREMENT ကို ပုံစံအမှန် ပြင်လိုက်ပါပြီ
cursor.execute('''CREATE TABLE IF NOT EXISTS tasks 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, username TEXT)''')
conn.commit()

def ensure_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0)", (user_id,))
    conn.commit()

async def is_joined(user_id, channel_username, context):
    try:
        member = await context.bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

async def main_menu(update, context):
    text = "🔥 **Axel Earning System** 🔥\nအောက်က ခလုတ်များကို သုံးပြီး ငွေရှာပါ။"
    keyboard = [
        [InlineKeyboardButton("💰 Balance", callback_data="balance"), InlineKeyboardButton("📝 Task", callback_data="list_tasks")],
        [InlineKeyboardButton("👥 Referral", callback_data="ref_link"), InlineKeyboardButton("⚙️ Set Wallet", callback_data="set_wallet")],
        [InlineKeyboardButton("💳 Withdrawal", callback_data="withdraw")]
    ]
    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🛠 Admin Panel", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)
    if context.args and context.args[0].isdigit():
        ref_id = int(context.args[0])
        if ref_id != user_id:
            cursor.execute("INSERT OR IGNORE INTO referrals (user_id, referred_by) VALUES (?, ?)", (user_id, ref_id))
            conn.commit()
    await main_menu(update, context)

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    ensure_user(user_id)
    await query.answer()

    if query.data == "admin_panel" and user_id == ADMIN_ID:
        kb = [[InlineKeyboardButton("➕ Add Task", callback_data="add_task")],
              [InlineKeyboardButton("❌ Clear All Tasks", callback_data="clear_tasks")],
              [InlineKeyboardButton("⬅️ Back", callback_data="back")]]
        await query.edit_message_text("🛠 **Admin Control Panel**", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "add_task" and user_id == ADMIN_ID:
        context.user_data['waiting_task'] = True
        await query.message.reply_text("📝 ပုံစံအတိုင်း ပို့ပေးပါ။\n\n`ChannelName @username` \n(ဥပမာ- `Channel1 @maxbfselling`)")

    elif query.data == "clear_tasks" and user_id == ADMIN_ID:
        cursor.execute("DELETE FROM tasks")
        conn.commit()
        await query.answer("✅ Task အားလုံး ဖျက်ပြီးပါပြီ။", show_alert=True)
        await main_menu(update, context)

    elif query.data == "list_tasks":
        cursor.execute("SELECT task_id FROM completed_tasks WHERE user_id = ?", (user_id,))
        done = [r[0] for r in cursor.fetchall()]
        cursor.execute("SELECT id, name, username FROM tasks")
        all_tasks = cursor.fetchall()
        kb = [[InlineKeyboardButton(f"🚀 {t[1]}", callback_data=f"view_{t[0]}")] for t in all_tasks if t[0] not in done]
        if not kb:
            await query.edit_message_text("✅ Task အားလုံး ပြီးပါပြီ။", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back")]]))
        else:
            kb.append([InlineKeyboardButton("⬅️ Back", callback_data="back")])
            await query.edit_message_text("📝 **လက်ရှိလုပ်ရန် Task များ**", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data.startswith("view_"):
        task_id = query.data.split("_")[1]
        cursor.execute("SELECT name, username FROM tasks WHERE id = ?", (task_id,))
        tinfo = cursor.fetchone()
        if tinfo:
            kb = [[InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{tinfo[1].replace('@','')}")],
                  [InlineKeyboardButton("✅ Verify", callback_data=f"verify_{task_id}")],
                  [InlineKeyboardButton("⬅️ Back", callback_data="list_tasks")]]
            await query.edit_message_text(f"📍 Join: {tinfo[1]}", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data.startswith("verify_"):
        task_id = query.data.split("_")[1]
        cursor.execute("SELECT username FROM tasks WHERE id = ?", (task_id,))
        tinfo = cursor.fetchone()
        if tinfo and await is_joined(user_id, tinfo[0], context):
            cursor.execute("INSERT OR IGNORE INTO completed_tasks (user_id, task_id) VALUES (?, ?)", (user_id, task_id))
            cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (JOIN_REWARD, user_id))
            cursor.execute("SELECT referred_by FROM referrals WHERE user_id = ?", (user_id,))
            ref = cursor.fetchone()
            if ref:
                cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (REF_REWARD, ref[0]))
                cursor.execute("DELETE FROM referrals WHERE user_id = ?", (user_id,))
                try: await context.bot.send_message(chat_id=ref[0], text=f"🔔 Ref Bonus {REF_REWARD} Ks!")
                except: pass
            conn.commit()
            await query.message.reply_text(f"✅ +{JOIN_REWARD} Ks!")
            await main_menu(update, context)
        else: await query.answer("❌ မ Join ရသေးပါ။", show_alert=True)

    elif query.data == "withdraw":
        cursor.execute("SELECT balance, wallet_type, wallet_num FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row is None or row[1] is None or row[2] is None:
            await query.message.reply_text("⚠️ ကျေးဇူးပြု၍ 'Set Wallet' အရင်လုပ်ပါ။")
        elif row[0] < MIN_WITHDRAW:
            await query.answer(f"❌ အနည်းဆုံး {MIN_WITHDRAW} Ks လိုအပ်သည်။", show_alert=True)
        else:
            user_link = f"[{query.from_user.first_name}](tg://user?id={user_id})"
            notice = f"📩 **Withdraw Alert!**\n👤: {user_link}\n🆔: `{user_id}`\n💵: {row[0]} Ks\n🏦: {row[1]}\n📝: {row[2]}"
            try:
                await context.bot.send_message(chat_id=ADMIN_ID, text=notice, parse_mode="Markdown")
                cursor.execute("UPDATE users SET balance = 0 WHERE user_id = ?", (user_id,))
                conn.commit()
                await query.edit_message_text("✅ အောင်မြင်ပါသည်။ Admin ထံ Notice ပို့ပြီးပါပြီ။", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back")]]))
            except: await query.message.reply_text("❌ Admin ထံ Notice ပို့မရပါ။")

    elif query.data == "ref_link":
        bot_info = await context.bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={user_id}"
        await query.edit_message_text(f"👥 **Referral Link:**\n`{link}`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back")]]), parse_mode="Markdown")

    elif query.data == "balance":
        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        bal = cursor.fetchone()[0]
        await query.edit_message_text(f"💰 Balance: {bal} Ks", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back")]]))

    elif query.data == "set_wallet":
        kb = [[InlineKeyboardButton("Kpay", callback_data="w_Kpay"), InlineKeyboardButton("WavePay", callback_data="w_Wave")], [InlineKeyboardButton("⬅️ Back", callback_data="back")]]
        await query.edit_message_text("🏧 **Wallet ရွေးပါ**", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data.startswith("w_"):
        context.user_data['wtype'] = query.data.split("_")[1]
        await query.message.reply_text("📍 ဖုန်းနံပါတ် နှင့် အမည် ပို့ပေးပါ။")

    elif query.data == "back": await main_menu(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID and context.user_data.get('waiting_task'):
        try:
            parts = update.message.text.split(" ")
            name = parts[0]
            username = parts[1] if parts[1].startswith("@") else f"@{parts[1]}"
            cursor.execute("INSERT INTO tasks (name, username) VALUES (?, ?)", (name, username))
            conn.commit()
            context.user_data['waiting_task'] = False
            await update.message.reply_text(f"✅ Task အသစ် ထည့်သွင်းပြီးပါပြီ။")
            await main_menu(update, context)
        except:
            await update.message.reply_text("❌ ပုံစံမှားနေပါသည်။ ပြန်ပို့ပေးပါ။\nပုံစံ- `ChannelName @username`")
    elif 'wtype' in context.user_data:
        cursor.execute("UPDATE users SET wallet_type = ?, wallet_num = ? WHERE user_id = ?", (context.user_data['wtype'], update.message.text, user_id))
        conn.commit()
        del context.user_data['wtype']
        await update.message.reply_text("✅ Wallet ချိတ်ဆက်ပြီးပါပြီ။")
        await main_menu(update, context)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is ready Axel!")
    app.run_polling()
