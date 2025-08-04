#!/usr/bin/env python3

import asyncio
import discord
import logging
import os
import sys
from datetime import datetime, time, date
import pytz

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("lite_copy_bot.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

class DtuLiteCopyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.messages = True
        super().__init__(intents=intents)

        self.source_channel_id = 1389399372210503700  # Cleaned headline channel
        self.target_channel_id = 1401330865308569621  # DTU Lite feed channel
        self.upgrade_channel_id = 1132697525531443210  # Channel to upgrade
        self.allowed_window = (time(8, 0), time(10, 0))  # 8:00–10:00 AM EST
        self.timezone = pytz.timezone("US/Eastern")
        self.last_upgrade_prompt_day = None

    def is_within_posting_window(self) -> bool:
        now = datetime.now(self.timezone).time()
        start, end = self.allowed_window
        return start <= now <= end

    async def on_ready(self):
        logger.info(f"✅ DTU Lite Copy Bot connected as {self.user}")
        channel = self.get_channel(self.target_channel_id)
        if channel:
            await channel.send("📡 DTU Lite timed headline feed is active.")
        else:
            logger.warning("⚠️ Could not find target channel.")

    async def on_message(self, message):
        if message.channel.id != self.source_channel_id:
            return
        if message.author == self.user:
            return

        logger.info(f"📥 Message in source channel: {message.content[:100]}")

        now = datetime.now(self.timezone)
        current_time = now.time()
        current_day = date.today()

        target = self.get_channel(self.target_channel_id)
        if not target:
            logger.warning("⚠️ Could not find target channel.")
            return

        if self.is_within_posting_window():
            await target.send(message.content)
            logger.info("✅ Headline copied to DTU Lite channel.")
        elif current_time > self.allowed_window[1]:
            if self.last_upgrade_prompt_day != current_day:
                await target.send(
                    f"⏱️ DTU Lite feed has ended for today.\n"
                    f"Want 24/7 access to live headlines? Upgrade your membership here: <#{self.upgrade_channel_id}>"
                )
                logger.info("📢 Upgrade message sent.")
                self.last_upgrade_prompt_day = current_day
            else:
                logger.info("🕙 Outside posting hours. Upgrade message already sent today.")
        else:
            logger.info("🕙 Outside posting hours. No action taken.")

async def main():
    token = os.getenv("DISCORD_TOKEN_LITE")
    if not token:
        logger.error("❌ DISCORD_TOKEN_LITE not found in environment")
        sys.exit(1)

    bot = DtuLiteCopyBot()
    try:
        logger.info("🚀 Starting DTU Lite Copy Bot...")
        await bot.start(token, reconnect=True)
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}")
    finally:
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
