import os
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Railway ရဲ့ Variables ထဲမှာ TELEGRAM_TOKEN ဆိုတဲ့နာမည်နဲ့ Token ထည့်ထားပေးရပါမယ်
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Keyboard ခလုတ်များကို ပုံစံချခြင်း
main_keyboard = [
    ['💰 Balance', '📝 Task'],
    ['👥 Referral', '⚙️ Set Wallet'],
    ['💳 Withdrawal'],
    ['🛠 Admin Panel']
]
markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # User /start နှိပ်လိုက်ရင် ပေါ်လာမယ့်စာ
    await update.message.reply_text(
        "Welcome to Axel Money Bot! 🌟\n\nအောက်က ခလုတ်များကို အသုံးပြုပြီး point များ စုဆောင်းနိုင်ပါသည်။",
        reply_markup=markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    # ခလုတ်တစ်ခုချင်းစီအတွက် အလုပ်လုပ်ပုံ (Logic)
    if text == "💰 Balance":
        await update.message.reply_text(f"👤 User ID: {user_id}\n💰 လက်ရှိ Balance: 0.00 Point")
    
    elif text == "📝 Task":
        await update.message.reply_text("🎯 ယနေ့အတွက် Task အသစ်များ မရှိသေးပါ။")
    
    elif text == "👥 Referral":
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        await update.message.reply_text(f"🔗 သင်၏ Referral Link:\n{ref_link}\n\nသူငယ်ချင်းတစ်ယောက်ခေါ်လျှင် 100 Point ရပါမည်။")
    
    elif text == "💳 Withdrawal":
        await update.message.reply_text("⚠️ နည်းပညာပိုင်းဆိုင်ရာ ပြုပြင်နေသဖြင့် ငွေထုတ်ယူမှုကို ခေတ္တရပ်ဆိုင်းထားပါသည်။ Admin ထံ တိုက်ရိုက်ဆက်သွယ်ပါ။")
    
    elif text == "⚙️ Set Wallet":
        await update.message.reply_text("ပို့ဆောင်လိုသည့် Wallet Address (TON/Solana) ကို ပို့ပေးပါ။")
    
    else:
        await update.message.reply_text("ကျေးဇူးပြု၍ အောက်က ခလုတ်များကို အသုံးပြုပါ။", reply_markup=markup)

def main():
    if not TOKEN:
        print("Error: TELEGRAM_TOKEN variables ထဲမှာ မရှိသေးပါ!")
        return

    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot is starting on Railway...")
    app.run_polling()

if __name__ == '__main__':
    main()
                                        
