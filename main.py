import os
import json
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- CONFIGURATION ---
TOKEN = "8639241153:AAGcL6T6bgJ1QdccyVb4fuLxq2qgTIm3wIo"
ADMIN_LIST = [7097694897, 7311138952]
DATA_FILE = "user_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f: return json.load(f)
        except: pass
    return {"users": {}, "tasks": [], "settings": {"ref_bonus": 500}}

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=4)

db = load_data()

# --- USER FUNCTIONS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    user_name = update.message.from_user.first_name
    
    if user_id not in db["users"]:
        referrer = context.args[0] if context.args else None
        db["users"][user_id] = {"name": user_name, "balance": 0, "tasks_done": [], "ref_by": referrer}
        
        if referrer and referrer in db["users"] and referrer != user_id:
            db["users"][referrer]["balance"] += db["settings"]["ref_bonus"]
            try:
                await context.bot.send_message(chat_id=int(referrer), text=f"👥 အဖွဲ့ဝင်သစ်တိုးလာပါပြီ! +{db['settings']['ref_bonus']} Points ရရှိပါတယ်။")
            except: pass
        save_data(db)

    buttons = [['💰 Balance', '📝 Task'], ['👥 Referral', '⚙️ Set Wallet'], ['💳 Withdrawal']]
    if int(user_id) in ADMIN_LIST: buttons.append(['🛠 Admin Panel'])
    
    await update.message.reply_text(
        f"Axel Money Bot မှ ကြိုဆိုပါတယ် {user_name}! ✨",
        reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text

    if text == "💰 Balance":
        bal = db["users"][user_id]["balance"]
        await update.message.reply_text(f"💰 သင်၏လက်ရှိလက်ကျန်- {bal} Points")

    elif text == "📝 Task":
        done_list = db["users"][user_id]["tasks_done"]
        available = [t for t in db["tasks"] if t["id"] not in done_list]
        
        if not available:
            await update.message.reply_text("🎯 ယနေ့အတွက် Task အကုန်ပြီးပါပြီ။")
            return

        for t in available:
            kb = [[InlineKeyboardButton("🔗 Join Link", url=t['url'])],
                  [InlineKeyboardButton("✅ အတည်ပြုမည်", callback_data=f"done_{t['id']}")]]
            await update.message.reply_text(f"📌 {t['name']}\n💰 ရရှိမည်- {t['points']} Points", reply_markup=InlineKeyboardMarkup(kb))

    elif text == "👥 Referral":
        bot_user = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_user}?start={user_id}"
        await update.message.reply_text(f"👥 သင့်ရဲ့ Invite Link:\n`{link}`\n\nတစ်ယောက်ခေါ်လျှင် {db['settings']['ref_bonus']} Points ရမည်။", parse_mode="Markdown")

    elif text == "🛠 Admin Panel" and int(user_id) in ADMIN_LIST:
        await update.message.reply_text(
            "🛠 **Admin Control Panel**\n\n"
            "• `/addtask နာမည် | Link | Points` - Task အသစ်ထည့်ရန်\n"
            "• `/setref အမှတ်` - Ref Bonus ပြောင်းရန်\n"
            "• `/send UserID | စာသား` - User ထံစာပို့ရန်\n"
            "• `/users` - User စုစုပေါင်းကြည့်ရန်",
            parse_mode="Markdown"
        )

# --- CALLBACKS ---
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    task_id = int(query.data.split("_")[1])
    
    task = next((t for t in db["tasks"] if t["id"] == task_id), None)
    if task and task_id not in db["users"][user_id]["tasks_done"]:
        db["users"][user_id]["tasks_done"].append(task_id)
        db["users"][user_id]["balance"] += task["points"]
        save_data(db)
        await query.answer("✅ Point ထည့်သွင်းပြီးပါပြီ!")
        await query.edit_message_text(f"✅ {task['name']} ပြီးမြောက်ကြောင်း အတည်ပြုပြီး။")

# --- ADMIN COMMANDS ---
async def admin_cmds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_LIST: return
    text = update.message.text
    
    if text.startswith("/addtask"):
        try:
            parts = text.replace("/addtask ", "").split("|")
            new_id = len(db["tasks"]) + 1
            db["tasks"].append({"id": new_id, "name": parts[0].strip(), "url": parts[1].strip(), "points": int(parts[2].strip())})
            save_data(db); await update.message.reply_text("✅ Task ထည့်ပြီးပါပြီ။")
        except: await update.message.reply_text("ပုံစံမှားနေပါသည်။")

    elif text.startswith("/setref"):
        db["settings"]["ref_bonus"] = int(context.args[0])
        save_data(db); await update.message.reply_text("✅ Ref Bonus ပြောင်းပြီးပါပြီ။")

    elif text.startswith("/send"):
        try:
            parts = text.replace("/send ", "").split("|")
            await context.bot.send_message(chat_id=int(parts[0].strip()), text=f"📩 Admin မှ စာပို့လိုက်ပါသည်-\n\n{parts[1].strip()}")
            await update.message.reply_text("✅ စာပို့ပြီးပါပြီ။")
        except: await update.message.reply_text("ပို့မရပါ။ User ID မှားနိုင်ပါတယ်။")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^(/addtask|/setref|/send|/users)"), admin_cmds))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()

if __name__ == "__main__": main()
