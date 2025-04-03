import logging
import fitz  # PyMuPDF
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ConversationHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# PDF Configuration
PDF_DIR = os.path.join(os.getcwd(), "assets/pdf")  # Ensure assets/pdf exists
INPUT_PDF = os.path.join(PDF_DIR, "Cover_Page.pdf")
OLD_NAME = "Prasid Mandal"

# Conversation states
NAME = 1

def ensure_pdf_exists():
    """Check if the input PDF exists; raise error otherwise."""
    if not os.path.exists(INPUT_PDF):
        raise FileNotFoundError(f"Error: The PDF file was not found at {INPUT_PDF}")

async def start(update: Update, context: CallbackContext) -> int:
    """Initiate conversation, ask for the user's name."""
    await update.message.reply_text(
        "Hey! Send me your name, and I'll edit the PDF for you. 😊"
    )
    return NAME

def edit_pdf(name: str) -> str:
    """Edits the PDF, replacing OLD_NAME with the provided name."""
    ensure_pdf_exists()
    
    output_pdf = os.path.join(PDF_DIR, f"output_{name}.pdf")

    doc = fitz.open(INPUT_PDF)
    replaced = False

    for page in doc:
        text_instances = page.search_for(OLD_NAME)
        if text_instances:
            replaced = True
            for inst in text_instances:
                page.insert_textbox(inst, name, fontsize=12, color=(0, 0, 0))

    if not replaced:
        logging.warning("No occurrences of the name were found in the PDF.")

    doc.save(output_pdf)
    doc.close()

    return output_pdf

async def get_name(update: Update, context: CallbackContext) -> int:
    """Handles name input, edits PDF, and sends back the modified file."""
    user_name = update.message.text.strip()

    if not user_name:
        await update.message.reply_text("Please enter a valid name! ❌")
        return NAME

    await update.message.reply_text(f"Editing PDF with your name: {user_name}... ⏳")

    try:
        modified_pdf = edit_pdf(user_name)
        with open(modified_pdf, "rb") as pdf:
            await update.message.reply_document(pdf, filename=f"{user_name}_edited.pdf")
        await update.message.reply_text("Here’s your personalized PDF! 🎉")
    except FileNotFoundError as e:
        await update.message.reply_text(str(e))
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        await update.message.reply_text("Oops! Something went wrong. Try again later. 😢")

    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    """Cancel the process."""
    await update.message.reply_text("Cancelled. Type /start to try again.")
    return ConversationHandler.END

def main():
    """Run the Telegram bot."""
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is missing from the .env file.")

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    logging.info("Bot is running... 🚀")
    app.run_polling()

if __name__ == "__main__":
    main()
