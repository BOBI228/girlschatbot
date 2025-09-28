from __future__ import annotations

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from .config import settings, AppInfo
from .persona import build_system_prompt
from .ai_provider import ai
from .memory import memory
from .safety import is_crisis, is_nsfw_request, crisis_response, nsfw_refusal, moderate_text


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("companion-bot")


ADULT_Q_TEXT = (
    "Привет! Меня зовут Лина 😊 Я общаюсь только с совершеннолетними. Подтверди, пожалуйста, что тебе 18+?"
)


def ensure_event_loop_policy() -> None:
    try:
        if sys.platform.startswith("linux"):
            import uvloop

            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except Exception:
        pass


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id  # type: ignore[assignment]
    memory.clear(chat_id)
    if not memory.is_adult(chat_id):
        await ask_adult_gate(update, context)
        return
    await update.message.reply_text(
        "Привет! Я Лина. Расскажи, как ты? Чем живёшь? 😊",
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Я здесь, чтобы поддержать, послушать и немного пофлиртовать (без пошлостей). Напиши, что у тебя на душе."
    )


async def ask_adult_gate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Да, мне 18+", callback_data="adult_yes"), InlineKeyboardButton("Нет", callback_data="adult_no")]]
    )
    target = update.message or update.callback_query.message  # type: ignore[assignment]
    if target:
        await target.reply_text(ADULT_Q_TEXT, reply_markup=keyboard)


async def handle_adult_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    chat_id = query.message.chat_id  # type: ignore[assignment]
    if query.data == "adult_yes":
        memory.set_adult(chat_id, True)
        await query.edit_message_text("Спасибо за подтверждение! Расскажи, как проходит твой день? 🌸")
    else:
        memory.set_adult(chat_id, False)
        await query.edit_message_text("Мне можно общаться только со взрослыми. Если тебе нет 18, давай вернёмся позже.")


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    chat_id = update.effective_chat.id  # type: ignore[assignment]
    text = update.message.text or ""

    if not memory.is_adult(chat_id):
        await ask_adult_gate(update, context)
        return

    # Safety checks
    if is_crisis(text):
        await update.message.reply_text(crisis_response())
        return

    if is_nsfw_request(text):
        await update.message.reply_text(nsfw_refusal())
        return

    flagged, reason = await moderate_text(text)
    if flagged:
        await update.message.reply_text(nsfw_refusal())
        return

    # AI conversation
    memory.append(chat_id, "user", text)
    system_prompt = build_system_prompt()
    messages = memory.get_messages(chat_id)

    try:
        reply = await ai.generate_reply(system_prompt=system_prompt, messages=messages, temperature=0.7, max_tokens=300)
    except Exception as e:
        logger.exception("AI generation failed: %s", e)
        await update.message.reply_text("Ой! Немного устала. Давай попробуем ещё раз попозже.")
        return

    reply = (reply or "").strip()
    if not reply:
        reply = "Мм, я задумалась... Расскажешь ещё чуть-чуть?"

    memory.append(chat_id, "assistant", reply)
    await update.message.reply_text(reply, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


def main() -> None:
    load_dotenv(override=False)
    ensure_event_loop_policy()
    info = AppInfo()
    logger.info("Starting %s v%s", info.name, info.version)
    app = (
        ApplicationBuilder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .parse_mode(ParseMode.HTML)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(handle_adult_callback, pattern=r"^adult_(yes|no)$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    logger.info("Bot is starting polling…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
