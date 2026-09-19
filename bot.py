import asyncio
import html
import logging
import time
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message, ChatMemberUpdated, InlineKeyboardMarkup,
    InlineKeyboardButton, CallbackQuery
)
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

from config import BOT_TOKEN, OWNER_ID, DEFAULT_AD_INTERVAL_HOURS
from storage import (
    init_db, get_setting, set_setting,
    add_ban, bans_last_24h, add_quiz_result, get_leaderboard, get_user_stats
)

logging.basicConfig(level=logging.INFO)
router = Router()
QUIZZES = {}


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


async def require_owner(message: Message) -> bool:
    if not message.from_user or not is_owner(message.from_user.id):
        await message.reply("❌ Ye command sirf Owner use kar sakta hai.")
        return False
    return True


async def is_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in {
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
        }
    except Exception:
        return False


def render_template(template: str, name: str, username: str) -> str:
    return (
        template
        .replace("{GROUP_NAME}", name)
        .replace("{GROUP_USERNAME}", username)
    )


async def make_ad() -> str:
    template = await get_setting(
        "ad_text",
        "📚 {GROUP_NAME}\n"
        "🎯 Class 12 Study Group\n"
        "📖 Notes • Doubts • MCQs • PYQs\n"
        "🔗 @{GROUP_USERNAME}"
    )
    name = await get_setting("ad_name", "RWA Doubt Group")
    username = await get_setting(
        "ad_username", "RWA_DOUBT_GROUP_CLASS_12TH_2027"
    )
    return render_template(template, name, username)


@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🛡️ <b>RWA Protection Bot</b>\n\n"
        "👑 Owner commands:\n"
        "/setname NAME\n"
        "/setusername USERNAME\n"
        "/setad TEXT\n"
        "/setadgroup CHAT_ID\n"
        "/adtime 6h / 12h / 24h\n"
        "/adnow\n"
        "/adstop\n"
        "/quiztime 30 / 60\n"
        "/quiz QUESTION | A | B | C | D | A\n"
        "/leaderboard\n"
        "/mystats\n"
        "/setgroupname NAME",
        parse_mode="HTML",
    )


@router.message(Command("setname"))
async def setname(message: Message, command: CommandObject):
    if not await require_owner(message):
        return
    value = (command.args or "").strip()
    if not value:
        await message.reply("Usage: /setname RWA Doubt Group")
        return
    await set_setting("ad_name", value)
    await message.reply("✅ Ad ka group name update ho gaya.")


@router.message(Command("setusername"))
async def setusername(message: Message, command: CommandObject):
    if not await require_owner(message):
        return
    value = (command.args or "").strip().lstrip("@")
    if not value:
        await message.reply("Usage: /setusername RWA_DOUBT_GROUP")
        return
    await set_setting("ad_username", value)
    await message.reply("✅ Ad ka @username update ho gaya.")


@router.message(Command("setad"))
async def setad(message: Message, command: CommandObject):
    if not await require_owner(message):
        return
    value = (command.args or "").strip()
    if not value:
        await message.reply(
            "Example:\n"
            "/setad 📚 {GROUP_NAME}\n"
            "🎯 Class 12 Study Group\n"
            "🔗 @{GROUP_USERNAME}"
        )
        return
    await set_setting("ad_text", value)
    await message.reply("✅ Advertisement template save ho gaya.")


@router.message(Command("setadgroup"))
async def setadgroup(message: Message, command: CommandObject):
    if not await require_owner(message):
        return

    value = (command.args or "").strip()
    if not value:
        await message.reply(
            "Usage: /setadgroup -1001234567890\n"
            "Group ID nikalne ke liye bot ko group me add karke /id command use kar sakte ho."
        )
        return

    try:
        int(value)
    except ValueError:
        await message.reply("❌ Valid numeric chat ID do.")
        return

    await set_setting("ad_chat_ids", value)
    await message.reply("✅ Auto-ad ke liye group set ho gaya.")


@router.message(Command("id"))
async def get_id(message: Message):
    await message.reply(f"🆔 Chat ID: <code>{message.chat.id}</code>", parse_mode="HTML")


@router.message(Command("adtime"))
async def adtime(message: Message, command: CommandObject):
    if not await require_owner(message):
        return

    raw = (command.args or "").strip().lower()

    try:
        if raw.endswith("h"):
            hours = float(raw[:-1])
        elif raw.endswith("m"):
            hours = float(raw[:-1]) / 60
        else:
            hours = float(raw)

        if hours <= 0:
            raise ValueError
    except ValueError:
        await message.reply("Usage: /adtime 6h | /adtime 12h | /adtime 24h")
        return

    await set_setting("ad_interval_hours", str(hours))
    await set_setting("ad_enabled", "1")
    await message.reply(f"✅ Auto-ad: har {hours:g} hour(s).")


@router.message(Command("adstop"))
async def adstop(message: Message):
    if not await require_owner(message):
        return

    await set_setting("ad_enabled", "0")
    await message.reply("🛑 Auto-ad band.")


@router.message(Command("adnow"))
async def adnow(message: Message):
    if not await require_owner(message):
        return

    await message.answer(await make_ad())


@router.message(Command("setgroupname"))
async def setgroupname(
    message: Message,
    command: CommandObject,
    bot: Bot
):
    if not await require_owner(message):
        return

    value = (command.args or "").strip()
    if not value:
        await message.reply("Usage: /setgroupname RWA Doubt Group")
        return

    try:
        await bot.set_chat_title(message.chat.id, value)
        await message.reply("✅ Actual group name change ho gaya.")
    except TelegramBadRequest as e:
        await message.reply(f"❌ Group name change nahi hua: {e}")


@router.message(Command("quiztime"))
async def quiztime(message: Message, command: CommandObject):
    if not await require_owner(message):
        return

    raw = (command.args or "").strip()

    if raw not in {"30", "60"}:
        await message.reply("Sirf /quiztime 30 ya /quiztime 60 use karo.")
        return

    await set_setting("quiz_seconds", raw)
    await message.reply(f"⏱️ Quiz timer {raw} seconds/question set hai.")


@router.message(Command("quiz"))
async def quiz(
    message: Message,
    command: CommandObject,
    bot: Bot
):
    if not await require_owner(message):
        return

    raw = (command.args or "").strip()
    parts = [p.strip() for p in raw.split("|")]

    if len(parts) != 6:
        await message.reply(
            "Format:\n"
            "/quiz Question | Option A | Option B | Option C | Option D | A"
        )
        return

    question = parts[0]
    options = parts[1:5]
    correct = parts[5].upper()

    if correct not in {"A", "B", "C", "D"}:
        await message.reply("❌ Correct answer A/B/C/D hona chahiye.")
        return

    seconds = int(await get_setting("quiz_seconds", "30"))

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"A) {options[0]}",
                    callback_data="quiz:A"
                ),
                InlineKeyboardButton(
                    text=f"B) {options[1]}",
                    callback_data="quiz:B"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"C) {options[2]}",
                    callback_data="quiz:C"
                ),
                InlineKeyboardButton(
                    text=f"D) {options[3]}",
                    callback_data="quiz:D"
                ),
            ],
        ]
    )

    safe_question = html.escape(question)

    sent = await message.answer(
        f"🧠 <b>Quiz</b>\n\n"
        f"{safe_question}\n\n"
        f"⏱️ Time: {seconds} sec",
        reply_markup=keyboard,
        parse_mode="HTML",
    )

    QUIZZES[(message.chat.id, sent.message_id)] = {
        "correct": correct,
        "ends": time.time() + seconds,
        "answers": {},
    }

    asyncio.create_task(
        close_quiz(bot, message.chat.id, sent.message_id, seconds)
    )


async def close_quiz(
    bot: Bot,
    chat_id: int,
    message_id: int,
    seconds: int
):
    await asyncio.sleep(seconds)

    data = QUIZZES.pop((chat_id, message_id), None)
    if not data:
        return

    try:
        await bot.edit_message_reply_markup(
            chat_id,
            message_id,
            reply_markup=None
        )
        await bot.send_message(
            chat_id,
            f"⏰ <b>Quiz time over!</b>\n"
            f"Correct answer: <b>{data['correct']}</b>",
            parse_mode="HTML",
        )
    except Exception:
        logging.exception("Could not close quiz")


@router.callback_query(F.data.startswith("quiz:"))
async def quiz_answer(callback: CallbackQuery):
    if not callback.message:
        await callback.answer()
        return

    key = (callback.message.chat.id, callback.message.message_id)
    data = QUIZZES.get(key)

    if not data:
        await callback.answer("⏰ Quiz khatam ho gaya.", show_alert=True)
        return

    if time.time() >= data["ends"]:
        await callback.answer("⏰ Time over.", show_alert=True)
        return

    user_id = callback.from_user.id

    if user_id in data["answers"]:
        await callback.answer(
            "⚠️ Aap already answer de chuke ho.",
            show_alert=True
        )
        return

    choice = callback.data.split(":", 1)[1]
    correct = choice == data["correct"]
    data["answers"][user_id] = choice

    await add_quiz_result(
        callback.message.chat.id,
        user_id,
        callback.from_user.full_name,
        callback.from_user.username,
        correct
    )

    if correct:
        await callback.answer("✅ Sahi! +1 point", show_alert=True)
    else:
        await callback.answer("❌ Galat. +0 point", show_alert=True)


@router.message(Command("leaderboard"))
async def leaderboard(message: Message):
    rows = await get_leaderboard(message.chat.id, 10)

    if not rows:
        await message.answer("🏆 Abhi leaderboard empty hai.")
        return

    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 <b>Quiz Leaderboard — Top 10</b>\n"]

    for index, row in enumerate(rows, start=1):
        user_id, name, username, points, correct, answered = row
        display = f"@{html.escape(username)}" if username else html.escape(name)
        medal = medals[index - 1] if index <= 3 else f"{index}."
        lines.append(
            f"{medal} {display} — <b>{points} pts</b> "
            f"({correct} correct / {answered} answered)"
        )

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("mystats"))
async def mystats(message: Message):
    if not message.from_user:
        return

    row = await get_user_stats(
        message.chat.id,
        message.from_user.id
    )

    if not row:
        await message.answer(
            "📊 Aapne abhi koi quiz answer nahi kiya."
        )
        return

    name, username, points, correct, answered = row

    await message.answer(
        "📊 <b>Your Quiz Stats</b>\n\n"
        f"🏆 Points: <b>{points}</b>\n"
        f"✅ Correct: <b>{correct}</b>\n"
        f"📝 Answered: <b>{answered}</b>",
        parse_mode="HTML"
    )


@router.chat_member()
async def ban_guard(event: ChatMemberUpdated, bot: Bot):
    if event.chat.type not in {"group", "supergroup"}:
        return

    old = event.old_chat_member.status
    new = event.new_chat_member.status

    if new != ChatMemberStatus.KICKED or old == ChatMemberStatus.KICKED:
        return

    actor_id = event.from_user.id

    # Owner and bot are exempt.
    if is_owner(actor_id) or actor_id == bot.id:
        return

    # The actor must currently be an admin.
    if not await is_admin(bot, event.chat.id, actor_id):
        return

    used = await bans_last_24h(event.chat.id, actor_id)

    if used >= 2:
        try:
            await bot.unban_chat_member(
                event.chat.id,
                event.new_chat_member.user.id,
                only_if_banned=True
            )
            await bot.send_message(
                event.chat.id,
                "⚠️ Is admin ka 24-hour ban limit (2) complete hai.\n"
                "Third ban reverse kar diya gaya."
            )
        except Exception:
            logging.exception("Could not reverse third ban")
        return

    await add_ban(
        event.chat.id,
        actor_id,
        event.new_chat_member.user.id
    )


@router.message(F.document)
async def pdf_notice(message: Message):
    mime = (message.document.mime_type or "").lower()

    if mime == "application/pdf":
        await message.reply(
            "📄 PDF detected.\n"
            "🔒 Forward/save restriction ke liye Telegram group ki "
            "Content Protection setting ON rakho."
        )


@router.message(F.photo)
async def photo_notice(message: Message):
    await message.reply(
        "🖼️ Photo detected.\n"
        "🔒 Forward/save restriction ke liye Telegram group ki "
        "Content Protection setting ON rakho."
    )


async def ad_loop(bot: Bot):
    while True:
        try:
            enabled = await get_setting("ad_enabled", "0")

            if enabled != "1":
                await asyncio.sleep(60)
                continue

            interval = float(
                await get_setting(
                    "ad_interval_hours",
                    str(DEFAULT_AD_INTERVAL_HOURS)
                )
            )

            await asyncio.sleep(max(60, interval * 3600))

            if await get_setting("ad_enabled", "0") != "1":
                continue

            chat_ids = await get_setting("ad_chat_ids", "")
            ad = await make_ad()

            for item in chat_ids.split(","):
                item = item.strip()

                if not item:
                    continue

                try:
                    await bot.send_message(int(item), ad)
                except Exception:
                    logging.exception(
                        "Could not send ad to chat %s",
                        item
                    )

        except Exception:
            logging.exception("Ad loop error")
            await asyncio.sleep(60)


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN missing")

    if not OWNER_ID:
        raise RuntimeError("OWNER_ID missing")

    await init_db()

    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    asyncio.create_task(ad_loop(bot))

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )


if __name__ == "__main__":
    asyncio.run(main())
