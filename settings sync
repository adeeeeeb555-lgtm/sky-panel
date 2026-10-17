"""
settings_sync.py  —  Cog للبوت يستقبل تعديلات لوحة التحكم (Sky Universe)
متوافق بالكامل مع app.py
"""
import asyncio
import os
import aiohttp
from discord.ext import commands, tasks

DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "https://sky-panel-z0b2.onrender.com").rstrip("/")
BOT_API_KEY = os.environ.get("BOT_API_KEY", "YOUR_SECRET_API_KEY")
POLL_SECONDS = 10  # فحص التحديثات كل 10 ثوانٍ

class SettingsSync(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None
        self.cache: dict[str, dict] = {}  # guild_id -> settings dict
        self.ready = False

    async def cog_load(self):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bot {BOT_API_KEY}"},
            timeout=aiohttp.ClientTimeout(total=10),
        )
        self.poll.start()

    async def cog_unload(self):
        self.poll.cancel()
        if self.session:
            await self.session.close()

    async def _fetch_guild_settings(self, guild_id: int):
        try:
            async with self.session.get(f"{DASHBOARD_URL}/api/bot/settings/{guild_id}") as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get("settings", {})
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            print(f"[sync] connection error for guild {guild_id}: {e}")
        return None

    @tasks.loop(seconds=POLL_SECONDS)
    async def poll(self):
        # تحديث إعدادات كل السيرفرات المتصل بها البوت دورياً
        for guild in self.bot.guilds:
            settings = await self._fetch_guild_settings(guild.id)
            if settings is not None:
                old_settings = self.cache.get(str(guild.id))
                if old_settings != settings:
                    self.cache[str(guild.id)] = settings
                    self.bot.dispatch("dashboard_settings_update", guild.id, settings)
        self.ready = True

    @poll.before_loop
    async def _before_poll(self):
        await self.bot.wait_until_ready()

    # ---------- أدوات مساعدة للـ Cogs الأخرى ----------
    def get_settings(self, guild_id: int) -> dict:
        """الحصول على كافة إعدادات السيرفر"""
        return self.cache.get(str(guild_id), {})

    def get(self, guild_id: int, key: str, default=None):
        """الحصول على قيمة إعداد معين مباشرة"""
        settings = self.get_settings(guild_id)
        return settings.get(key, default)

    def feature_enabled(self, guild_id: int, checkbox_key: str, default=True) -> bool:
        """التحقق مما إذا كان الخيار (Checkbox) مفعلًا"""
        settings = self.get_settings(guild_id)
        if not settings:
            return default
        return checkbox_key in settings

    # ---------- الحدث عند تغير الإعدادات ----------
    @commands.Cog.listener()
    async def on_dashboard_settings_update(self, guild_id: int, new_settings: dict):
        guild = self.bot.get_guild(guild_id)
        name = guild.name if guild else guild_id
        print(f"[sync] تم تحديث إعدادات السيرفر: {name}")

async def setup(bot: commands.Bot):
    await bot.add_cog(SettingsSync(bot))
