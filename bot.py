cat > bot.py << 'ENDOFFILE'
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

BOT_TOKEN = "8944341939:AAFt7QP-TsrKpvPLCeX7QFl3fET2x_gcklQ"
ADMIN_ID = 7654914240

UC_PRICES = {
    "60 UC": 15000,
    "325 UC": 75000,
    "660 UC": 145000,
    "1800 UC": 380000,
    "3850 UC": 780000,
    "8100 UC": 1550000,
}

PAYMENT_CARD = "8600 1234 5678 9012"
PAYMENT_NAME = "Ismingiz"

SELECT_UC, ENTER_PLAYER_ID, CONFIRM_ORDER, WAIT_PAYMENT = range(4)
orders = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎮 UC sotib olish", callback_data="buy_uc")],
        [InlineKeyboardButton("📋 Mening buyurtmalarim", callback_data="my_orders")],
        [InlineKeyboardButton("📞 Qollab-quvvatlash", callback_data="support")],
    ]
    await update.message.reply_text(
        "🎮 PUBG UC Dokonga Xush Kelibsiz!\n\nTez va ishonchli UC yetkazib berish.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buy_uc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = []
    for uc, price in UC_PRICES.items():
        keyboard.append([InlineKeyboardButton(f"💎 {uc} — {price:,} som", callback_data=f"uc_{uc}")])
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")])
    await query.edit_message_text("💎 UC miqdorini tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_UC

async def select_uc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uc_choice = query.data.replace("uc_", "")
    context.user_data["uc"] = uc_choice
    context.user_data["price"] = UC_PRICES[uc_choice]
    await query.edit_message_text(f"✅ {uc_choice} tanladingiz.\n\nPUBG Player ID raqamingizni kiriting:")
    return ENTER_PLAYER_ID

async def enter_player_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = update.message.text.strip()
    if not player_id.isdigit():
        await update.message.reply_text("❌ Player ID faqat raqam bolishi kerak. Qaytadan kiriting:")
        return ENTER_PLAYER_ID
    context.user_data["player_id"] = player_id
    uc = context.user_data["uc"]
    price = context.user_data["price"]
    keyboard = [
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data="confirm_order")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_order")],
    ]
    await update.message.reply_text(
        f"📋 Buyurtmangiz:\n\n💎 UC: {uc}\n🎮 Player ID: {player_id}\n💰 Narx: {price:,} som\n\nTogri mi?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CONFIRM_ORDER

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    uc = context.user_data["uc"]
    price = context.user_data["price"]
    player_id = context.user_data["player_id"]
    order_id = f"ORD{user.id}{len(orders)+1:04d}"
    orders[order_id] = {"user_id": user.id, "username": user.username, "uc": uc, "price": price, "player_id": player_id, "status": "Tolov kutilmoqda"}
    context.user_data["order_id"] = order_id
    await query.edit_message_text(
        f"💳 Tolov:\n\n🏦 Karta: {PAYMENT_CARD}\n👤 Egasi: {PAYMENT_NAME}\n💰 Summa: {price:,} som\n\n📌 Buyurtma ID: {order_id}\n\nTolov chekini screenshot qilib yuboring."
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"🔔 Yangi buyurtma!\n📌 ID: {order_id}\n👤 @{user.username} ({user.id})\n💎 UC: {uc}\n🎮 Player ID: {player_id}\n💰 Narx: {price:,} som")
    return WAIT_PAYMENT

async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    order_id = context.user_data.get("order_id", "Noma'lum")
    if orders.get(order_id):
        orders[order_id]["status"] = "Chek tekshirilmoqda"
    caption = f"🧾 Tolov cheki!\n📌 {order_id}\n👤 @{user.username}\n💎 {orders.get(order_id, {}).get('uc', '-')}\n🎮 {orders.get(order_id, {}).get('player_id', '-')}"
    if update.message.photo:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=caption)
    elif update.message.document:
        await context.bot.send_document(chat_id=ADMIN_ID, document=update.message.document.file_id, caption=caption)
    await update.message.reply_text(f"✅ Chek qabul qilindi!\n📌 {order_id}\n\n⏳ 5-30 daqiqada UC hisobingizga otkaziladi.")
    return ConversationHandler.END

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_orders = {k: v for k, v in orders.items() if v["user_id"] == user_id}
    if not user_orders:
        await query.edit_message_text("📋 Sizda hali buyurtma yoq.\n\n/start")
        return
    text = "📋 Buyurtmalaringiz:\n\n"
    for oid, o in list(user_orders.items())[-5:]:
        text += f"📌 {oid}\n💎 {o['uc']} | 💰 {o['price']:,} som | {o['status']}\n\n"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")]]))

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📞 Admin: @admin_username\n\nIsh vaqti: 09:00 - 23:00", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")]]))

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🎮 UC sotib olish", callback_data="buy_uc")],
        [InlineKeyboardButton("📋 Mening buyurtmalarim", callback_data="my_orders")],
        [InlineKeyboardButton("📞 Qollab-quvvatlash", callback_data="support")],
    ]
    await query.edit_message_text("🎮 PUBG UC Dokonga Xush Kelibsiz!", reply_markup=InlineKeyboardMarkup(keyboard))

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Bekor qilindi. /start")
    return ConversationHandler.END

async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    args = context.args
    if not args:
        await update.message.reply_text("Foydalanish: /approve ORDER_ID")
        return
    order_id = args[0]
    if order_id not in orders:
        await update.message.reply_text("❌ Buyurtma topilmadi.")
        return
    orders[order_id]["status"] = "✅ Bajarildi"
    user_id = orders[order_id]["user_id"]
    uc = orders[order_id]["uc"]
    await context.bot.send_message(chat_id=user_id, text=f"🎉 Tabriklaymiz! {uc} hisobingizga otkazildi! 🎮")
    await update.message.reply_text(f"✅ {order_id} tasdiqlandi.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(buy_uc, pattern="^buy_uc$")],
        states={
            SELECT_UC: [CallbackQueryHandler(select_uc, pattern="^uc_")],
            ENTER_PLAYER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_player_id)],
            CONFIRM_ORDER: [
                CallbackQueryHandler(confirm_order, pattern="^confirm_order$"),
                CallbackQueryHandler(cancel_order, pattern="^cancel_order$"),
            ],
            WAIT_PAYMENT: [MessageHandler(filters.PHOTO | filters.Document.ALL, receive_receipt)],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", admin_approve))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(my_orders, pattern="^my_orders$"))
    app.add_handler(CallbackQueryHandler(support, pattern="^support$"))
    app.add_handler(CallbackQueryHandler(back_main, pattern="^back_main$"))
    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
ENDOFFILE
