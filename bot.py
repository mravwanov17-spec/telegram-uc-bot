import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

BOT_TOKEN = "8944341939:AAGqIy6rCoEI64whBJVTLnuu0kKWSPxyBtM"
ADMIN_ID = 7654914240

UC_PRICES = {
    "30 UC": 6500,
    "60 UC": 12500,
    "325 UC": 60000,
    "660 UC": 117000,
    "1900 UC": 290000,
    "3850 UC": 580000,
}

orders = {}
SELECT_UC, ENTER_PLAYER_ID, CONFIRM_ORDER, WAIT_PAYMENT = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎮 UC sotib olish", callback_data="buy_uc")]]
    await update.message.reply_text("🎮 PUBG UC Dokonga Xush Kelibsiz!", reply_markup=InlineKeyboardMarkup(keyboard))

async def buy_uc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton(f"💎 {uc} — {UC_PRICES[uc]:,} so'm", callback_data=f"uc_{uc}")] for uc in UC_PRICES.keys()]
    await query.edit_message_text("💎 UC tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_UC

async def select_uc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uc = query.data.replace("uc_", "")
    context.user_data["uc"] = uc
    context.user_data["price"] = UC_PRICES[uc]
    await query.edit_message_text(f"Player ID raqamingizni kiriting:")
    return ENTER_PLAYER_ID

async def enter_player_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = update.message.text
    context.user_data["player_id"] = player_id
    uc = context.user_data["uc"]
    price = context.user_data["price"]
    keyboard = [[InlineKeyboardButton("✅ Tasdiqlash", callback_data="confirm")]]
    await update.message.reply_text(f"UC: {uc}\nPlayer ID: {player_id}\nNarx: {price:,} so'm\n\nTogri mi?", reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM_ORDER

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    uc = context.user_data["uc"]
    price = context.user_data["price"]
    player_id = context.user_data["player_id"]
    order_id = f"ORD{user.id}"
    orders[order_id] = {"user_id": user.id, "uc": uc, "price": price, "player_id": player_id}
    await query.edit_message_text(f"💳 To'lov:\nKarta: 8600123456789012\nSumma: {price:,} so'm\nBuyurtma ID: {order_id}\n\nChek yuborish...")
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"🔔 Yangi buyurtma: {order_id}\nUC: {uc}\nPlayer ID: {player_id}\nNarx: {price:,} so'm")
    return WAIT_PAYMENT

async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Chek qabul qilindi! Adminiga tekshiriladi.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(buy_uc, pattern="^buy_uc$")],
        states={
            SELECT_UC: [CallbackQueryHandler(select_uc, pattern="^uc_")],
            ENTER_PLAYER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_player_id)],
            CONFIRM_ORDER: [CallbackQueryHandler(confirm_order, pattern="^confirm")],
            WAIT_PAYMENT: [MessageHandler(filters.PHOTO | filters.Document.ALL, receive_receipt)],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()