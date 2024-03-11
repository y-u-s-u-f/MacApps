import discord
from discord.ext import commands
from discord import app_commands
import requests
import datetime

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='ping', description="Sends the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f"Pong!", description=f"Latency: {round(self.bot.latency * 1000)}ms", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='info', description="Provides information about the bot")
    async def info(self, interaction: discord.Interaction):
        response = requests.get("https://api.github.com/repos/y-u-s-u-f/MacApps/releases/latest")
        version = response.json()["tag_name"]

        embed = discord.Embed(title="Bot Information", color=discord.Color.blue())
        embed.add_field(name="Name", value="MacApps", inline=False)
        embed.add_field(name="Version", value=version, inline=False)
        embed.add_field(name="Uptime", value=self.get_uptime(), inline=False)
        embed.set_footer(text="Made with love by @yusuf.md")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='help', description="Provides a list of all commands and their descriptions")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Help", color=discord.Color.blue())

        excluded_commands = ['sync', 'reload', 'purge', 'kick', 'ban', 'mute', 'unmute', 'warn']

        for cog in self.bot.cogs.values():
            for command in cog.get_app_commands():
                if command.name not in excluded_commands:
                    embed.add_field(name=command.name, value=command.description, inline=True)
        
        await interaction.response.send_message(embed=embed)

    def get_uptime(self):
        since = self.bot.start_time
        now = datetime.datetime.now()
        diff = now - since
        minutes, seconds = divmod(int(diff.total_seconds()), 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        uptime = f"{days} days, {hours} hours, {minutes} minutes, and {seconds} seconds"
        return uptime

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.start_time = datetime.datetime.now()
        print('General cog loaded')

async def setup(bot):
    await bot.add_cog(General(bot))