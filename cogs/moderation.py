import discord
import datetime
import re
from discord.ext import commands
from discord import app_commands
from typing import Literal



class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None
        self.interaction = None

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green, emoji='✅')
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=discord.Embed(title='Confirming...', color=discord.Color.green()))
        button.disabled = True
        self.children[1].disabled = True
        await interaction.message.edit(view=self)
        self.interaction = interaction
        self.value = True
        self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey, emoji='❌')
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=discord.Embed(title='Cancelling...', color=discord.Color.yellow()))
        button.disabled = True
        self.children[0].disabled = True
        await interaction.message.edit(view=self)
        self.interaction = interaction
        self.value = False
        self.stop()


async def lock_thread(interaction: discord.Interaction, reason:str=None, followup:bool=True):
    em = discord.Embed(title="🔒 Locked!", description=f"Reason: {reason}" if reason else None, timestamp=datetime.datetime.now(), color=discord.Color.green())
    em.set_footer(text=f'Locked by {interaction.user.name}', icon_url=interaction.user.avatar.url)
    await interaction.followup.send(embed=discord.Embed(title="Locking...", color=discord.Color.green()), ephemeral=True) if followup else await interaction.response.send_message(embed=discord.Embed(title="Locking...", color=discord.Color.green()), ephemeral=True)
    await interaction.channel.send(embed=em)
    await interaction.channel.edit(name=
                                '[🔒] ' + interaction.channel.name,
                                locked=True,
                                archived=True, 
                                reason=reason if reason else None)

async def unlock_thread(interaction: discord.Interaction, thread: discord.Thread, reason:str=None):
    await interaction.followup.send(embed=discord.Embed(title="🔓 Unlocked!", description=f"Reason: {reason}" if reason else None, color=discord.Color.green()), ephemeral=True)
    await thread.edit(name=thread.name.replace('[🔒] ', ''), locked=False, archived=False, reason=reason or None)
    embed=discord.Embed(
        title="This thread has been unlocked!",
        description=f"Reason: {reason}" if reason else None,
        timestamp=datetime.datetime.now(),
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Unlocked by {interaction.user.name}", icon_url=interaction.user.avatar.url)
    await thread.send(embed=embed)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='lock', description='Locks a thread')
    @app_commands.describe(reason='The reason for locking the thread')
    async def lock(self, interaction, reason: str = None):
        await interaction.response.defer(ephemeral=True)
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.followup.send(embed=discord.Embed(title='❌ This command can only be used in threads.', color=discord.Color.red()), ephemeral=True)
            return
        if interaction.channel.locked and interaction.channel.archived:
            await interaction.followup.send(embed=discord.Embed(title='❌ This thread is already!', color=discord.Color.red()), ephemeral=True)
            return
        view = Confirm()
        if interaction.user == interaction.channel.owner or interaction.permissions.manage_threads:
            await lock_thread(interaction, reason)
        else:
            await interaction.channel.send(f'<@{interaction.channel.owner_id}>',embed=discord.Embed(title='Do you want to lock this thread?', color=discord.Color.green()).set_footer(text=f'{interaction.user.name} is requesting to lock this thread.', icon_url=interaction.user.avatar.url), view=view)

            await view.wait()
            if view.value:
                await lock_thread(view.interaction, reason)
            else:
                await interaction.followup.send(embed=discord.Embed(title="❌ Cancelled", color=discord.Color.red()))


    @app_commands.command(name='unlock', description='Unlocks a thread')
    @app_commands.describe(thread='The ID or link of the thread to unlock', reason='The reason for unlocking the thread')
    async def unlock(self, interaction: discord.Interaction, thread: str=None, reason:str=None):
        await interaction.response.defer(ephemeral=True)
        if thread is None and isinstance(interaction.channel, discord.Thread):
            thread = interaction.channel.id
        if not thread:
            await interaction.followup.send(embed=discord.Embed(title='❌ Failed', description='Please either use this command in a thread and/or specify the thread ID/link.', color=discord.Color.red()))
            return
        if str(thread).isdigit():
            thread = await interaction.guild.fetch_channel(int(thread))
        elif re.match(r'(https?:\/\/)?(ptb\.|canary\.)?discord(app)?\.(com|net)\/channels\/([0-9]+)\/([0-9]+)', thread):
            thread = await self.bot.fetch_channel(int(re.match(r'(https?:\/\/)?(ptb\.|canary\.)?discord(app)?\.(com|net)\/channels\/([0-9]+)\/([0-9]+)', thread).group(6)))

        if not isinstance(thread, discord.Thread):
            await interaction.followup.send(embed=discord.Embed(title='❌ Failed', description='Not a thread!', color=discord.Color.red()))
            return
        if not thread.locked and not thread.archived:
            await interaction.followup.send(embed=discord.Embed(title="❌ This thread is already unlocked!", color=discord.Color.red()))
            return
        await unlock_thread(interaction, thread, reason)

    @app_commands.command(name='ticket', description='Creates a ticket to get help from the staff team')
    async def ticket(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        category = interaction.guild.get_channel(1188453953088786453)
        channel = await category.create_text_channel(name=f'{interaction.user.name}-ticket', topic=f'Ticket for {interaction.user.name}')
        overwrite = channel.overwrites_for(interaction.user)
        overwrite.update(send_messages=True, view_channel=True, read_message_history=True, read_messages=True)
        await channel.set_permissions(interaction.user, overwrite=overwrite)
        await channel.send(f'<@&1188453953088786451>', embed=discord.Embed(title='New Ticket!', description=f'{interaction.user.mention} has created a ticket!', timestamp=datetime.datetime.now(), color=discord.Color.green()).set_footer(text=f'Created by {interaction.user.name}', icon_url=interaction.user.avatar.url))
        await interaction.followup.send(embed=discord.Embed(title='Ticket created!', description=f'Please go to {channel.mention} to see your ticket!', color=discord.Color.green()))
    # sync command
    @app_commands.command(name='sync', description='Syncs the slash commands with the bot')
    @commands.is_owner()
    async def sync(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.bot.tree.sync()
        await interaction.followup.send(embed=discord.Embed(title='Synced!', color=discord.Color.green()))

    @app_commands.command(name='close', description='Closes a ticket')
    async def close(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        if not interaction.channel.category_id == 1188453953088786453:
            await interaction.followup.send(embed=discord.Embed(title='❌ Error', description='This command can only be used in tickets.', color=discord.Color.red()))
            return

        view = Confirm()
        await interaction.followup.send(embed=discord.Embed(title='Are you sure you want to close this ticket?', description='This action can not be undone.', color=discord.Color.yellow()), view=view)
        await view.wait()

        if view.value:
            await interaction.channel.delete(reason=f'Closed by {interaction.user.name}')
        else:
            await interaction.followup.send(embed=discord.Embed(title='❌ Canceled', description='Ticket closure cancelled.', timestamp=datetime.datetime.now(), color=discord.Color.red()).set_footer(text=f'Canceled by {view.interaction.user}', icon_url=view.interaction.user.avatar.url))

    @app_commands.command(name='reload', description="Reload a cog")
    @commands.is_owner()
    async def reload(self, interaction: discord.Interaction, cog: str):  
        await interaction.response.defer(ephemeral=True)
        await self.bot.reload_extension("cogs." + cog)
        await interaction.followup.send(embed=discord.Embed(title='Reloaded!', color=discord.Color.green()))
    @commands.Cog.listener()
    async def on_ready(self):
        print('Moderation cog loaded')
    
    
    
async def setup(bot):
    await bot.add_cog(Moderation(bot=bot))