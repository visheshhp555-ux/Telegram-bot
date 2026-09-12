import os
import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import ChannelParticipantsKicked

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

client = TelegramClient(
    "unban_bot",
    API_ID,
    API_HASH
)


@client.on(events.NewMessage(pattern=r"^/unban$"))
async def unban_all(event):

    if not event.is_group:
        return

    # Check command user's admin status
    sender = await event.get_sender()
    perms = await client.get_permissions(event.chat_id, sender)

    if not perms.is_admin:
        await event.reply("❌ Sirf Group Admin / Owner ye command use kar sakta hai.")
        return

    # Check bot's own permission
    me = await client.get_me()
    bot_perms = await client.get_permissions(event.chat_id, me)

    if not bot_perms.is_admin or not bot_perms.ban_users:
        await event.reply(
            "❌ Mujhe Group Admin banao aur "
            "`Ban Users` permission ON karo."
        )
        return

    msg = await event.reply("🔄 Saare banned members ki list check kar raha hoon...")

    count = 0
    failed = 0

    try:
        async for user in client.iter_participants(
            event.chat_id,
            filter=ChannelParticipantsKicked
        ):
            try:
                await client.edit_permissions(
                    event.chat_id,
                    user.id,
                    view_messages=True
                )

                count += 1

                # Telegram flood limit se bachne ke liye
                await asyncio.sleep(0.3)

            except Exception:
                failed += 1

        await msg.edit(
            f"✅ **Unban Complete!**\n\n"
            f"👤 Unbanned: `{count}`\n"
            f"❌ Failed: `{failed}`"
        )

    except Exception as e:
        await msg.edit(
            f"❌ Process me error aa gaya:\n`{str(e)[:500]}`"
        )


async def main():
    print("🤖 Starting bot...")
    await client.start(bot_token=BOT_TOKEN)
    print("✅ Bot is online!")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
