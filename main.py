import os
import json
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN = "8639241153:AAGcL6T6bgJ1QdccyVb4fuLxq2qgTIm3wIo"
ADMIN_LIST = [7097694897, 7311138952]

# Data သိမ်းဆည်းရန် (ရိုးရှင်းအောင် JSON နဲ့ မှတ်ပါမယ်)
DATA_FILE = "user_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f: return json.load(f)
    return {"users": {}, "tasks": [], "settings": {"ref_bonus": 500, "min_withdraw": 5000}}

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=4)

data = load_data()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    user_name = update.message.from_user.first_name
    
    # User အသစ်ဆိုရင် Register လုပ်မယ်
    if user_id not in data["users"]:
        referrer = context.args[0] if context.args else None
        data["users"][user_id] = {"name": user_name, "balance": 0, "completed_tasks": [], "ref_by": referrer}
        if referrer and referrer in data["users"]:
            data["users"][referrer]["balance"] += data["settings"]["ref_bonus"]
        save_data(data)

    buttons = [['💰 Balance', '📝 Task'], ['👥 Referral', '⚙️ Set Wallet'], ['💳 Withdrawal']]
    if int(user_id) in ADMIN_LIST: buttons.append(['🛠 Admin Panel'])
    
    markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    await update.message.reply_text(f"Axel Money Bot မှ ကြိုဆိုပါတယ် {user_name}!", reply_markup=markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text

    if text == "📝 Task":
        user_tasks = data["users"][user_id]["completed_tasks"]
        available_tasks = [t for t in data["tasks"] if t["id"] not in user_tasks]
        
        if not available_tasks:
            await update.message.reply_text("🎯 လုပ်စရာ Task မရှိတော့ပါ။")
            return

        for task in available_tasks:
            keyboard = [[InlineKeyboardButton("Join Channel", url=task['url'])],
                        [InlineKeyboardButton("✅ Done", callback_data=f"done_{task['id']}")]]
            await update.message.reply_text(f"📌 {task['name']}\n💰 {task['points']} Points", reply_markup=InlineKeyboardMarkup(keyboard))

    elif text == "👥 Referral":
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        await update.message.reply_text(f"👥 သင့်ရဲ့ Invite Link:\n{ref_link}\n\nတစ်ယောက်ခေါ်လျှင် {data['settings']['ref_bonus']} Points ရမည်။")

    elif text == "🛠 Admin Panel" and int(user_id) in ADMIN_LIST:
        msg = (f"🛠 Admin Dashboard\n\n"
               f"1. Task ထည့်ရန်: `/addtask နာမည် | URL | အမှတ်` \n"
               f"2. Ref Bonus ပြောင်းရန်: `/setref အမှတ်` \n"
               f"3. User ဆီ စာပို့ရန်: `/send ID | စာသား` \n"
               f"4. User List: `/users`")
        await update.message.reply_text(msg)

# Callback for Task Completion
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    task_id = int(query.data.split("_")[1])
    
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task and task_id not in data["users"][user_id]["completed_tasks"]:
        data["users"][user_id]["completed_tasks"].append(task_id)
        data["users"][user_id]["balance"] += task["points"]
        save_data(data)
        await query.answer("✅ Task အောင်မြင်ပါတယ်။ Point ပေါင်းထည့်ပြီးပါပြီ။")
        await query.edit_message_text(f"✅ {task['name']} ကို လုပ်ဆောင်ပြီးပါပြီ။")

# Admin Commands
async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_LIST: return
    cmd = update.message.text.split()[0]
    
    if cmd == "/addtask":
        args = " ".join(context.args).split("|")
        new_task = {"id": len(data["tasks"])+1, "name": args[0].strip(), "url": args[1].strip(), "points": int(args[2].strip())}
        data["tasks"].append(new_task); save_data(data)
        await update.message.reply_text("✅ Task ထည့်ပြီးပါပြီ။")
    
    elif cmd == "/setref":
        data["settings"]["ref_bonus"] = int(context.args[0]); save_data(data)
        await update.message.reply_text(f"✅ Referral Bonus ကို {context.args[0]} ပြောင်းလိုက်ပါပြီ။")

    elif cmd == "/send":
        args = " ".join(context.args).split("|")
        target_id, message = args[0].strip(), args[1].strip()
        await context.bot.send_message(chat_id=target_id, text=f"📩 Admin ထံမှ စာရောက်လာပါသည်:\n\n{message}")
        await update.message.reply_text("✅ စာပို့ပြီးပါပြီ။")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(["addtask", "setref", "send", "users"], admin_commands))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.run_polling()

if __name__ == '__main__': main()
