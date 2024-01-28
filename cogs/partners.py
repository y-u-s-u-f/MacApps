import discord
import datetime
from discord.ext import commands
from discord import app_commands


class PartnerModal(discord.ui.Modal, title='Partner with us!'):
    app_name = discord.ui.TextInput(label='App Name(s)', placeholder='Your app name(s)', style=discord.TextStyle.short, required=True)
    app_desc = discord.ui.TextInput(label='Long App Description(s)', placeholder='Your app description(s)', style=discord.TextStyle.long, required=False)
    app_link = discord.ui.TextInput(label='App Link(s)', placeholder='Your app link(s)', required=True)
    notes = discord.ui.TextInput(label='Notes', placeholder='Any additional information you would like to provide', style=discord.TextStyle.long, required=False)

    async def on_submit(self, interaction: discord.Interaction):
        embed=discord.Embed(title='New Partner Application!', description=f'{interaction.user.mention} has submitted an application!', timestamp=datetime.datetime.now(), color=discord.Color.green())
        embed.set_footer(text=f'Submitted by {interaction.user.name}', icon_url=interaction.user.avatar.url)
        embed.add_field(name='App Name(s)', value=self.app_name.value, inline=False)
        embed.add_field(name='App Description(s)', value=self.app_desc.value, inline=False) if self.app_desc.value else None
        embed.add_field(name='App Link(s)', value=self.app_link.value, inline=False)
        embed.add_field(name='Notes', value=self.notes.value, inline=False) if self.notes.value else None
        # Create a channel for that partner submission:
        category = interaction.guild.get_channel(1188453953088786453)
        channel = await category.create_text_channel(name=f'{interaction.user.name}-partner-application', topic=f'Partner application for {interaction.user.name}')
        overwrite = channel.overwrites_for(interaction.user)
        overwrite.update(send_messages=True, view_channel=True, read_message_history=True, read_messages=True)
        await channel.set_permissions(interaction.user, overwrite=overwrite)
        await channel.send(embed=embed)



        embed=discord.Embed(title='Your application has been submitted!', description=f'We will contact you in {channel.mention}', color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)

class Partners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(name='partner', description='Apply to partner with us!')
    async def partner(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.response.send_modal(view=PartnerModal())
    
    @app_commands.command(name='partners', description='Shows a list of our partners')
    async def partners(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        forum = interaction.guild.get_channel(1188457026859319326)
        threadList = ""
        for thread in forum.threads:
            threadList += f'{thread.mention}\n'
        await interaction.followup.send(embed=discord.Embed(title='Our Amazing Partners!', description=threadList ,color=discord.Color.green()))
    
    @commands.Cog.listener()
    async def on_ready(self):
        print('Partners cog loaded')



async def setup(bot):
    await bot.add_cog(Partners(bot=bot))