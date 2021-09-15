#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Bot, User
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters
import logging
from telegram import ParseMode
from functools import partial
from main import extract_video_id, get_available_lang, fetch_man_chosen, fetch_auto_chosen
from py_youtube import Data

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

TOKEN = os.environ.get('BOT_TOKEN')
bot = Bot(TOKEN)

FIRST, SECOND = range(2)

URL = ''
LINK = ''
VIDEO_ID = ''
LANGS = ''
LAN_CODES = ''
STATE_LANG = ''
conv_handler = {}

def start(update, context):
    """Send message on `/start`."""
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    update.message.reply_text('Hi !\nI am a bot to extract Youtube subtitle and send it to you as a text file.\Send me a YouTube URL.')

def entry_dialog(update, context):
    global URL, LINK, VIDEO_ID, LANGS, LAN_CODES, STATE_LANG, conv_handler
    LINK = update.message.text
    yt = Data(f"{update.message.text}")
    URL = yt.title
    VIDEO_ID = extract_video_id(update.message.text)
    LANGS, LAN_CODES = get_available_lang(VIDEO_ID)
    if not LANGS:
        update.message.reply_text("Subtitles are not available for this video.")
    else:
        print(f"LANGS: {LANGS}")
        print(f"LAN_codes: {LAN_CODES}")
        reply_keyboard = form_keyboard(LANGS, LAN_CODES) + [[InlineKeyboardButton("Автоматично створені", callback_data="auto")]]

        reply_markup = InlineKeyboardMarkup(reply_keyboard)
        # Send message with text and appended InlineKeyboard\
        update.message.reply_text(
            "Select subtitle",
            reply_markup=reply_markup
        )
        print("ETAP 1 DONE")
        for lan in LAN_CODES:
            dp.add_handler(CallbackQueryHandler(partial(push_manual, lan_code=lan), pattern=f'^{lan}$'))
        dp.add_handler(CallbackQueryHandler(partial(push_auto, lan_code='uk'), pattern="^auto$"))

    return FIRST


def form_keyboard(lags, lancodes):
    res = []
    for lan, code in zip(lags, lancodes):
        res.append([InlineKeyboardButton(lan, callback_data=code)])
    return res


def push_manual(update, context, lan_code=None):
    query = update.callback_query
    query.answer()
    query.edit_message_text("Downloading...")
    print(f"CHAT_ID {update}")
    print(f"CHAT_ID {query.message.chat_id}")
    text = f"<a href='{LINK}'>Video</a>"
    bot.send_document(query.message.chat_id, document=open(fetch_man_chosen(VIDEO_ID, lan_code), 'rb'), caption=text, parse_mode=ParseMode.HTML)
    query.edit_message_text("Uploaded")

    return SECOND


def push_auto(update, context, lan_code=None):
    query = update.callback_query
    query.answer()
    res = fetch_auto_chosen(VIDEO_ID, lan_code)
    if res:
        query.edit_message_text("Downloading...")

        text = f"<a href='{LINK}'>Video</a>"
        bot.send_document(query.message.chat_id, document=open(res, 'rb'), caption=text, parse_mode=ParseMode.HTML)
        query.edit_message_text("Uploaded")
    else:
        query.edit_message_text("No subtitles available")
    return SECOND


def end(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(
        text="You can send me more URLs"
    )
    return ConversationHandler.END


def main():
    global dp, conv_handler
    yt_video_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?(?P<id>[A-Za-z0-9\-=_]{11})'
    tokenn = os.environ.get('BOT_TOKEN')
    updater = Updater(tokenn, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    #dp.add_handler(MessageHandler(Filters.regex(yt_video_regex), get_video_id))

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(yt_video_regex), entry_dialog)],
        states={
            FIRST: [],
            SECOND: [CallbackQueryHandler(end)]

        },
        fallbacks=[MessageHandler(Filters.regex(yt_video_regex), entry_dialog)]
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
