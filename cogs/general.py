import discord
import datetime
from discord.ext import commands
from discord import app_commands


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='ping', description="Sends the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f"Pong! {round(self.bot.latency * 1000)}ms")
        await interaction.response.send_message(embed=embed, color=discord.Color.green())

    @commands.Cog.listener()
    async def on_ready(self):
        print('General cog loaded')



async def setup(bot):
    await bot.add_cog(General(bot))