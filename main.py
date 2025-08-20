#!/usr/bin/env python3

import asyncio
import discord
import logging
import os
import sys
from datetime import datetime, time
import pytz

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("lite_copy_bot.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("dtu-lite")

EASTERN = pytz.timezone("US/Eastern")


class DtuLiteCopyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.messages = True
        super().__init__(intents=intents)

        # Channels
        self.source_channel_id = 1389399372210503700  # DTU Pro (cleaned) feed
        self.target_channel_id = 1401330865308569621  # DTU Lite feed

        # Time window (Eastern)
        self.window_start = time(8, 0)   # 8:00 AM ET
        self.window_end   = time(10, 0)  # 10:00 AM ET

    # ---- helpers ----
    def now_et(self) -> datetime:
        return datetime.now(EASTERN)

    def is_weekday(self) -> bool:
        # Monday = 0, Sunday = 6
        return self.now_et().weekday() < 5

    def within_window(self) -> bool:
        t = self.now_et().time()
        return self.window_start <= t <= self.window_end

    # ---- events ----
    async def on_ready(self):
        logger.info(f"✅ DTU Lite Copy Bot connected as {self.user}")
        logger.info(f"Monitoring (source): {self.source_channel_id}")
        logger.info(f"Relaying to (target): {self.target_channel_id}")

    async def on_message(self, message: discord.Message):
        # Only relay from Pro/cleaned source
        if message.channel.id != self.source_channel_id:
            return
        if message.author == self.user:
            return

        # Weekend: ignore
        if not self.is_weekday():
            logger.debug("Weekend; ignoring.")
            return

        # Only relay during window
        if not self.within_window():
            logger.debug("Outside posting window; ignoring.")
            return

        target = self.get_channel(self.target_channel_id)
        if not target:
            logger.warning("⚠️ Target channel not found.")
            return

        try:
            await target.send(message.content)
            logger.info("🟢 Relayed headline to DTU Lite.")
        except discord.Forbidden:
            logger.error("🚫 Missing permission to send in target channel.")
        except discord.HTTPException as e:
            logger.error(f"🌐 HTTP error sending to target: {e}")


# ---- main ----
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
