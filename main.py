import os
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8639241153:AAGcL6T6bgJ1QdccyVb4fuLxq2qgTIm3wIo"

# Admin ID များကို စာရင်းလုပ်ထားခြင်း
ADMIN_LIST = [7097694897, 7311138952]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # ရိုးရိုး User များအတွက် ခလုတ်များ
    buttons = [
        ['💰 Balance', '📝 Task'],
        ['👥 Referral', '⚙️ Set Wallet'],
        ['💳 Withdrawal']
    ]
    
    # အကယ်၍ Admin List ထဲမှာပါတဲ့ ID ဆိုရင် Admin Panel ခလုတ်ကို ပေါင်းထည့်ပေးမည်
    if user_id in ADMIN_LIST:
        buttons.append(['🛠 Admin Panel'])
        
    markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    
    await update.message.reply_text(
        f"Welcome {update.message.from_user.first_name}! 🌟\nAxel Money Bot မှ ကြိုဆိုပါတယ်။ အောက်က ခလုတ်များကို အသုံးပြုပြီး point များ စုဆောင်းနိုင်ပါသည်။",
        reply_markup=markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    
    # Admin Panel ကို Admin သာ နှိပ်ခွင့်ရှိစေရန် စစ်ဆေးခြင်း
    if text == "🛠 Admin Panel":
        if user_id in ADMIN_LIST:
            await update.message.reply_text("✅ Admin Dashboard ကို ရောက်ရှိနေပါသည်။\n(User list ကြည့်ရန် နှင့် Point ပေးရန် လုပ်ဆောင်ချက်များ ထည့်သွင်းနိုင်သည်)")
        else:
            # ခလုတ် မမြင်ရသော်လည်း စာရိုက်ပို့လာပါက အကြောင်းပြန်ရန်
            await update.message.reply_text("⚠️ သင်သည် Admin မဟုတ်သဖြင့် ဤနေရာကို ဝင်ရောက်ခွင့်မရှိပါ။")
            
    elif text == "💰 Balance":
        await update.message.reply_text("💰 သင်၏ လက်ရှိ Balance မှာ 0.00 ဖြစ်ပါသည်။")
        
    elif text == "📝 Task":
        await update.message.reply_text("🎯 ယနေ့အတွက် Task အသစ်များ မရှိသေးပါ။")
        
    elif text == "👥 Referral":
        await update.message.reply_text("🔗 သင့်သူငယ်ချင်းများကို ဖိတ်ခေါ်ရန် Link ကို မကြာမီ ရရှိပါမည်။")

    elif text == "💳 Withdrawal":
        await update.message.reply_text("⚠️ ငွေထုတ်ရန် အနည်းဆုံး point 10.00 လိုအပ်ပါသည်။")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
    
