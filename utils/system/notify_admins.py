from data.loader import Bot
from data.config import admins_id


async def on_startup_notify(bot: Bot):
    """уведомление админа"""
    for admin in admins_id:
        try:
            text = 'Bot was started\!'
            await bot.send_message(admin, text)
        except Exception as err:
            ...
