import os
import pymongo
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- CONFIG ---
TOKEN = os.getenv("8639241153:AAGcL6T6bgJ1QdccyVb4fuLxq2qgTIm3wIo")
MONGO_URI = os.getenv("mongodb+srv://hein:heinhein2007@cluster0.ehhc6my.mongodb.net/")
ADMIN_LIST = [int(id) for id in os.getenv("7311138952", "7097694897").split(",") if id]

client = pymongo.MongoClient(MONGO_URI)
db = client["axel_money_bot"]
users_col = db["users"]
tasks_col = db["tasks"]
settings_col = db["settings"]

if not settings_col.find_one():
    settings_col.insert_one({"ref_bonus": 500, "min_withdraw": 5000})

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id, user_name = update.message.from_user.id, update.message.from_user.first_name
    if not users_col.find_one({"user_id": user_id}):
        ref_by = int(context.args[0]) if context.args and context.args[0].isdigit() else None
        users_col.insert_one({"user_id": user_id, "name": user_name, "balance": 0, "tasks_done": [], "ref_by": ref_by, "wallet": None})
        if ref_by:
            bonus = settings_col.find_one()["ref_bonus"]
            users_col.update_one({"user_id": ref_by}, {"$inc": {"balance": bonus}})
    
    buttons = [['💰 Balance', '📝 Task'], ['👥 Referral', '⚙️ Set Wallet'], ['💳 Withdrawal']]
    if user_id in ADMIN_LIST: buttons.append(['🛠 Admin Panel'])
    await update.message.reply_text(f"Axel Money Bot မှ ကြိုဆိုပါတယ် {user_name}!", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id, text = update.message.from_user.id, update.message.text
    user = users_col.find_one({"user_id": user_id})

    if text == "💰 Balance":
        await update.message.reply_text(f"💰 လက်ကျန်- {user['balance']} Points")

    elif text == "📝 Task":
        available = [t for t in tasks_col.find() if t["id"] not in user["tasks_done"]]
        if not available: return await update.message.reply_text("🎯 Task အားလုံး ပြီးပါပြီ။")
        for t in available:
            kb = [[InlineKeyboardButton("🔗 Link", url=t['url'])], [InlineKeyboardButton("✅ Done", callback_data=f"done_{t['id']}")]]
            await update.message.reply_text(f"📌 {t['name']}\n💰 {t['points']} Points", reply_markup=InlineKeyboardMarkup(kb))

    elif text == "⚙️ Set Wallet":
        await update.message.reply_text("📱 သင်၏ ငွေထုတ်ယူမည့် Wallet (သို့) ဖုန်းနံပါတ်ကို ပေးပို့ပါ။\nဥပမာ- `Kpay 09xxxxxxxxx` သို့မဟုတ် `Wave 09xxxxxxxxx`", parse_mode="Markdown")
        context.user_data['state'] = 'SET_WALLET'

    elif text == "💳 Withdrawal":
        min_w = settings_col.find_one()["min_withdraw"]
        if not user['wallet']:
            await update.message.reply_text("❌ အရင်ဆုံး '⚙️ Set Wallet' မှာ Wallet အရင်ထည့်ပေးပါ။")
        elif user['balance'] < min_w:
            await update.message.reply_text(f"⚠️ ငွေထုတ်ရန် အနည်းဆုံး {min_w} Points လိုအပ်ပါသည်။")
        else:
            # ငွေထုတ်ခွင့်တောင်းဆိုမှုကို Admin ဆီ ပို့ခြင်း
            for admin in ADMIN_LIST:
                await context.bot.send_message(chat_id=admin, text=f"🔔 **ငွေထုတ်ရန်တောင်းဆိုမှု**\n\nID: `{user_id}`\nအမည်: {user['name']}\nWallet: `{user['wallet']}`\nPoints: {user['balance']}", parse_mode="Markdown")
            users_col.update_one({"user_id": user_id}, {"$set": {"balance": 0}}) # Balance ကို 0 ပြန်လုပ် (သို့မဟုတ် လိုသလောက်နုတ်)
            await update.message.reply_text("✅ ငွေထုတ်ရန် တောင်းဆိုမှု အောင်မြင်ပါသည်။ Admin မှ စစ်ဆေးပြီး 24 နာရီအတွင်း ပို့ပေးပါလိမ့်မည်။")

    elif text == "🛠 Admin Panel" and user_id in ADMIN_LIST:
        await update.message.reply_text("🛠 Admin Commands:\n/addtask Name|URL|Points\n/setref Points\n/setmin Points\n/send UserID|Message")

# --- အထွေထွေ စာတိုများ (Wallet သိမ်းဆည်းရန်) ---
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if context.user_data.get('state') == 'SET_WALLET':
        wallet_info = update.message.text
        users_col.update_one({"user_id": user_id}, {"$set": {"wallet": wallet_info}})
        await update.message.reply_text(f"✅ Wallet အချက်အလက်ကို `{wallet_info}` အဖြစ် သိမ်းဆည်းပြီးပါပြီ။", parse_mode="Markdown")
        context.user_data['state'] = None
    else:
        await handle_buttons(update, context)

# --- Task Callback ---
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id, task_id = query.from_user.id, int(query.data.split("_")[1])
    task = tasks_col.find_one({"id": task_id})
    user = users_col.find_one({"user_id": user_id})

    if task and task_id not in user["tasks_done"]:
        users_col.update_one({"user_id": user_id}, {"$push": {"tasks_done": task_id}, "$inc": {"balance": task["points"]}})
        await query.answer("✅ Point ရရှိပါပြီ!")
        await query.edit_message_text(f"✅ {task['name']} ပြီးမြောက်ကြောင်း အတည်ပြုပြီး။")

async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_LIST: return
    text = update.message.text
    if text.startswith("/setmin"):
        min_p = int(context.args[0])
        settings_col.update_one({}, {"$set": {"min_withdraw": min_p}})
        await update.message.reply_text(f"✅ အနည်းဆုံး ငွေထုတ်ယူနိုင်သည့် Point ကို {min_p} ပြောင်းလိုက်ပါပြီ။")
    # (တခြား addtask, send commands များ ဒီမှာ ဆက်ရှိပါမယ်)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^/"), admin_commands)) # Admin commands
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()

if __name__ == "__main__": main()
            
