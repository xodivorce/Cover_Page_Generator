import fitz
import os
from dotenv import load_dotenv
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

PDF_DIR = os.path.join(os.getcwd(), "assets/pdf")
FONT_PATH = os.path.join(os.getcwd(), "assets/font/LexendDeca-Regular.ttf")
INPUT_PDF = os.path.join(PDF_DIR, "Cover_Page.pdf")

logging.basicConfig(level=logging.INFO)

# Define states for the conversation
NAME, COLLEGE_ID = range(2)

def edit_pdf(name: str, college_id: str) -> str:
    doc = fitz.open(INPUT_PDF)
    output_pdf = os.path.join(PDF_DIR, f"Cover_for_{name}.pdf")

    college_id = college_id.upper()

    for page in doc:
        width, height = page.rect.width, page.rect.height
        font_name = "LexendDeca"
        page.insert_font(fontname=font_name, fontfile=FONT_PATH)

        text_instances = page.search_for("Name:")

        if text_instances:
            for inst in text_instances:
                x, y, w, h = inst
                text_x = min(x + w + 10, width - 239)
                text_y = min(max(y + h - 5, 20), height - 88.5)

                page.insert_text(
                    (text_x, text_y),
                    name,
                    fontsize=18,
                    color=(1, 1, 1),
                    fontname=font_name,
                    overlay=True
                )

                college_x = text_x
                college_y = text_y + 5

                page.insert_textbox(
                    fitz.Rect(college_x, college_y, college_x + 234.5, college_y + 60),
                    college_id,
                    fontsize=18,
                    color=(1, 1, 1),
                    fontname=font_name,
                    align=1,
                )

    doc.save(output_pdf)
    doc.close()
    return output_pdf

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Hi! Please send your full name:")

    return NAME

async def get_name(update: Update, context: CallbackContext):
    name = update.message.text.strip()
    context.user_data['name'] = name  # Store name in user data
    
    await update.message.reply_text(f"Got it! Now, please send your college ID:")

    return COLLEGE_ID

async def get_college_id(update: Update, context: CallbackContext):
    college_id = update.message.text.strip()
    name = context.user_data['name']  # Retrieve stored name
    
    pdf_path = edit_pdf(name, college_id)

    with open(pdf_path, "rb") as pdf_file:
        await update.message.reply_document(pdf_file, filename=f"Cover_for_{name}.pdf")

    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Conversation canceled. Send /start to begin again.")
    return ConversationHandler.END

def main():
    application = Application.builder().token(TOKEN).build()

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            COLLEGE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_college_id)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conversation_handler)

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
