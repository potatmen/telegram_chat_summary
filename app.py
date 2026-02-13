import os
import logging
import asyncio

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram_summarizer import TelegramSummarizer

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler('bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Telegram Channel Summarizer Bot\n\n"
        "Usage: /summarize @channelname\n"
        "Summarizes the last 24 hours of messages from a channel."
    )


async def summarize_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /summarize @channelname\n"
            "Example: /summarize @technews"
        )
        return

    channel = ' '.join(context.args)
    processing_msg = await update.message.reply_text(f"Summarizing {channel}...")

    try:
        summary = await summarizer.get_channel_summary(channel)
        await update.message.reply_text(f"Summary: {channel}\n\n{summary}")
    except Exception as e:
        logger.error(f"Error summarizing {channel}: {e}", exc_info=True)
        await update.message.reply_text(
            "Failed to summarize the channel.\n\n"
            "Make sure you:\n"
            "- Are a member of the channel\n"
            "- Used the correct channel name (e.g., @channelname)"
        )
    finally:
        try:
            await processing_msg.delete()
        except Exception:
            pass


def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in .env file")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    global summarizer
    summarizer = TelegramSummarizer()
    loop.run_until_complete(summarizer.connect_if_needed())

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("summarize", summarize_command))

    logger.info("Bot started")
    app.run_polling()


if __name__ == '__main__':
    main()
