import fitz
import os
import time
import tempfile
from dotenv import load_dotenv
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

PDF_DIR = os.path.join(os.getcwd(), "assets/pdf")
FONT_PATH = os.path.join(os.getcwd(), "assets/font/LexendDeca-Regular.ttf")
INPUT_PDF = os.path.join(PDF_DIR, "Cover_Page.pdf")
HEYGION_PDF = os.path.join(PDF_DIR, "HEYGION_HEALTH_REPORT.pdf")

logging.basicConfig(level=logging.INFO)

NAME, COLLEGE_ID = range(2)

def estimate_text_width(text: str, fontsize: int, fontname: str) -> float:
    average_char_width = 0.6
    text_length = len(text) * average_char_width * fontsize
    return text_length

def edit_REPORT_pdf(name: str) -> str:
    name = name.upper()
    doc = fitz.open(HEYGION_PDF)
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    output_pdf = temp_pdf.name

    pages_to_edit = [3, 9, 13, 17, 24, 31, 33]

    font_name = "LexendDeca"
    fontsize = 14

    for page_num, page in enumerate(doc):
        width, height = page.rect.width, page.rect.height
        page.insert_font(fontname=font_name, fontfile=FONT_PATH)

        if page_num in pages_to_edit:
            text_y = 700
            text_width = estimate_text_width(name, fontsize=fontsize, fontname=font_name)
            right_gap = 100
            adjusted_text_x = width - right_gap - text_width
            page.insert_text(
                (adjusted_text_x, text_y),
                name,
                fontsize=fontsize,
                color=(0, 0, 0),
                fontname=font_name,
                overlay=True
            )

    doc.save(output_pdf)
    doc.close()

    return output_pdf

def edit_pdf(name: str, college_id: str) -> str:
    doc = fitz.open(INPUT_PDF)
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    output_pdf = temp_pdf.name

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
                text_y = min(max(y + h - 5, 20), height - 88)

                page.insert_text(
                    (text_x, text_y),
                    name,
                    fontsize=18,
                    color=(1, 1, 1),
                    fontname=font_name,
                    overlay=True
                )

                college_x = text_x
                college_y = text_y + 4

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
    await update.message.reply_text("Hi! I'm a Cover page & Report Geanerator for your major project (Group 4). Please send your full name to continue:")

    return NAME

async def get_name(update: Update, context: CallbackContext):
    name = update.message.text.strip()
    name = ' '.join(word.capitalize() for word in name.split())

    context.user_data['name'] = name
    
    await update.message.reply_text("Got it! Now, please send your College ID:")

    return COLLEGE_ID

async def get_college_id(update: Update, context: CallbackContext):
    college_id = update.message.text.strip()
    name = context.user_data['name']
    
    try:
        await update.message.reply_text("Generating your Cover page... Please wait a moment.")
        pdf_path = edit_pdf(name, college_id)
        
        with open(pdf_path, "rb") as pdf_file:
            await update.message.reply_document(pdf_file, filename=f"Cover_for_{name}.pdf")
        
        await update.message.reply_text("Generating your report pages... Please wait a moment.")
        
        try:
            report_pdf_path = edit_REPORT_pdf(name)
            
            with open(report_pdf_path, "rb") as report_pdf_file:
                await update.message.reply_document(report_pdf_file, filename=f"Health_Report_for_{name}.pdf")
            
            os.remove(pdf_path)
            os.remove(report_pdf_path)

        except Exception as e:
            await update.message.reply_text(f"Oops! Something went wrong while generating the report pages: {e} \nSend /start to regenerate again.")
            logging.error(f"Error while generating report for {name}: {e}")
            return ConversationHandler.END

    except Exception as e:
        await update.message.reply_text(f"Oops! Something went wrong while generating the report pages: {e} \nSend /start to regenerate again.")
        logging.error(f"Error while generating cover page for {name}: {e}")
        return ConversationHandler.END

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