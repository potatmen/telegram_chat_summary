import os
import re
import logging
from datetime import datetime, timezone, timedelta

import requests
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError  # kept for 2FA fallback

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash-lite"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
MAX_TEXT_LENGTH = 10000
MAX_OUTPUT_TOKENS = 2048
MESSAGE_FETCH_LIMIT = 100
MESSAGE_AGE_DAYS = 1

SUMMARIZE_PROMPT = (
    "Из следующего списка сообщений выбери только самые важные и значимые новости "
    "— те, которые имеют наибольшее влияние или значение. Мелкие, второстепенные "
    "и малозначительные сообщения пропускай. Кратко изложи только отобранные важные "
    "новости. Отвечай только на русском языке. Не добавляй вступление — сразу начинай "
    "с сути. Используй • для буллет-поинтов. Никакого HTML, никакого Markdown — только "
    "чистый текст.\n\nСообщения:\n{text}"
)


class TelegramSummarizer:
    def __init__(self):
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')

        if not all([self.api_id, self.api_hash, self.phone]):
            raise ValueError("Missing Telegram credentials in .env file")
        if not self.gemini_api_key:
            raise ValueError("Missing GEMINI_API_KEY in .env file")

        self.client = TelegramClient('session_name', int(self.api_id), self.api_hash)
        logger.info("TelegramSummarizer initialized")

    async def connect_if_needed(self):
        try:
            is_authorized = await self.client.is_user_authorized()
            if is_authorized:
                if not self.client.is_connected():
                    await self.client.connect()
                return
        except Exception:
            pass

        await self.client.connect()

        if not await self.client.is_user_authorized():
            logger.info("Not authorized, starting login...")
            await self.client.send_code_request(self.phone)
            code = input('\nEnter the verification code: ')
            try:
                await self.client.sign_in(self.phone, code)
            except SessionPasswordNeededError:
                password = input('\nEnter your 2FA password: ')
                await self.client.sign_in(password=password)

        logger.info("Telegram authenticated")

    async def get_channel_summary(self, channel_identifier):
        if not self.client.is_connected():
            await self.client.connect()

        entity = await self.client.get_entity(channel_identifier)
        logger.info(f"Fetching messages from {channel_identifier}")

        cutoff = datetime.now(timezone.utc) - timedelta(days=MESSAGE_AGE_DAYS)
        messages = await self.client.get_messages(entity, limit=MESSAGE_FETCH_LIMIT)

        text_messages = []
        for msg in messages:
            if msg.date and msg.date < cutoff:
                break
            if msg.text:
                text_messages.append(msg.text)

        if not text_messages:
            return "No messages found in this channel for the last 24 hours."

        text_content = '\n'.join(text_messages)
        logger.info(f"Summarizing {len(text_messages)} messages ({len(text_content)} chars)")

        return self._summarize_text(text_content)

    def _summarize_text(self, text):
        if len(text) > MAX_TEXT_LENGTH:
            logger.warning(f"Text exceeds {MAX_TEXT_LENGTH} chars ({len(text)}), truncating")
            text = text[:MAX_TEXT_LENGTH]

        payload = {
            "contents": [{"parts": [{"text": SUMMARIZE_PROMPT.format(text=text)}]}],
            "generationConfig": {
                "maxOutputTokens": MAX_OUTPUT_TOKENS,
                "temperature": 0.7
            }
        }

        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": self.gemini_api_key
        }

        try:
            response = requests.post(GEMINI_API_URL, json=payload, headers=headers, timeout=30)
        except requests.exceptions.Timeout:
            return "Error: Request timeout. Please try again."

        if response.status_code != 200:
            logger.error(f"Gemini API error: {response.status_code}")
            return f"Error: Gemini API returned {response.status_code}"

        result = response.json()
        candidates = result.get('candidates', [])
        if not candidates:
            return "No summary generated."

        try:
            summary = candidates[0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            return "No summary generated."
        summary = re.sub(r'<[^>]+>', '', summary)
        return summary
