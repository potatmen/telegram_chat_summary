# Telegram Channel Summarizer Bot

Summarizes the last 24 hours of messages from any Telegram channel using Google Gemini AI.

## Setup

### 1. Get credentials

- **Telegram Bot Token**: Create a bot via [@BotFather](https://t.me/BotFather) on Telegram
- **Telegram API ID & Hash**: Register an app at [my.telegram.org/apps](https://my.telegram.org/apps)
- **Gemini API Key**: Get one at [aistudio.google.com](https://aistudio.google.com/app/apikey)

### 2. Configure

```bash
cp .env.example .env
```

Fill in `.env` with your credentials:

```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_API_ID=...
TELEGRAM_API_HASH=...
TELEGRAM_PHONE=+1234567890
GEMINI_API_KEY=...
```

### 3. Install and run

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

On first run you'll be asked for a Telegram verification code. After that the session is saved locally.

## Usage

Open your bot in Telegram and send:

```
/summarize @channelname
/summarize https://t.me/channelname
```

The bot fetches messages from the last 24 hours, sends them to Gemini for summarization, and returns the result.

### Commands

- `/start` or `/help` — show usage info
- `/summarize @channel` or `/summarise @channel` — summarize a channel (both spellings work)
- Also accepts `https://t.me/channel` links

## Project structure

```
app.py                  — bot entry point and command handlers
telegram_summarizer.py  — Telegram client + Gemini API integration
requirements.txt        — dependencies
.env.example            — environment variable template
```
