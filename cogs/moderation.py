import discord
import datetime
import re
from discord.ext import commands
from discord import app_commands
from typing import Literal
import re


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
    em.set_footer(text=f'Locked by {interaction.user.name}', icon_url=interaction.user.display_avatar.url)
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
    embed.set_footer(text=f"Unlocked by {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
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
            await interaction.channel.send(f'<@{interaction.channel.owner_id}>',embed=discord.Embed(title='Do you want to lock this thread?', color=discord.Color.green()).set_footer(text=f'{interaction.user.name} is requesting to lock this thread.', icon_url=interaction.user.display_avatar.url), view=view)

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
        await interaction.response.defer(ephemeral=True)
        category = interaction.guild.get_channel(1188453953088786453)
        channel = await category.create_text_channel(name=f'{interaction.user.name}-ticket', topic=f'Ticket for {interaction.user.name}')
        overwrite = channel.overwrites_for(interaction.user)
        overwrite.update(send_messages=True, view_channel=True, read_message_history=True, read_messages=True)
        await channel.set_permissions(interaction.user, overwrite=overwrite)
        await channel.send(embed=discord.Embed(title='New Ticket!', description=f'{interaction.user.mention} has created a ticket!', timestamp=datetime.datetime.now(), color=discord.Color.green()).set_footer(text=f'Created by {interaction.user.name}', icon_url=interaction.user.display_avatar.url))
        await interaction.followup.send(embed=discord.Embed(title='Ticket created!', description=f'Please go to {channel.mention} to see your ticket!', color=discord.Color.green()))

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
            await interaction.channel.edit(name=f'closed-ticket')
            for member in interaction.channel.members:
                if member.guild_permissions.administrator:
                    continue
                await interaction.channel.set_permissions(member, overwrite=None)
        else:
            await interaction.followup.send(embed=discord.Embed(title='❌ Canceled', description='Ticket closure cancelled.', timestamp=datetime.datetime.now(), color=discord.Color.red()).set_footer(text=f'Canceled by {view.interaction.user}', icon_url=view.interaction.user.display_avatar.url))

    @app_commands.command(name='reload', description="Reload a cog")
    @commands.is_owner()
    async def reload(self, interaction: discord.Interaction, cog: str):  
        await interaction.response.defer(ephemeral=True)
        await self.bot.reload_extension("cogs." + cog)
        await interaction.followup.send(embed=discord.Embed(title='Reloaded!', color=discord.Color.green()))
    @commands.Cog.listener()
    async def on_ready(self):
        print('Moderation cog loaded')

    @app_commands.command(name='purge', description='Purges messages')
    @app_commands.describe(amount='The amount of messages to purge', user='The user to purge messages from', reason='The reason for purging messages')
    @app_commands.default_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: int, user: discord.Member = None, reason: str = None):
        await interaction.response.defer(ephemeral=True)
        if amount > 100:
            await interaction.followup.send(embed=discord.Embed(title='❌ Error', description='You can only purge up to 100 messages at a time.', color=discord.Color.red()))
            return
        if user:
            await interaction.channel.purge(limit=amount, check=lambda m: m.author == user, reason=reason)
        else:
            await interaction.channel.purge(limit=amount, reason=reason)
        await interaction.followup.send(embed=discord.Embed(title='Purged!', description=f'Purged {amount} messages.', color=discord.Color.green()))

    @app_commands.command(name='kick', description='Kicks a user')
    @app_commands.describe(member='The user to kick', reason='The reason for kicking the user')
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        await interaction.response.defer(ephemeral=True)
        await member.send(embed=discord.Embed(title='Kicked!', description=f'You have been kicked from MacApps', color=discord.Color.red()))
        await member.kick(reason=reason)
        await interaction.followup.send(embed=discord.Embed(title='Kicked!', description=f'Kicked {member.mention}.', color=discord.Color.green()))

    @app_commands.command(name='ban', description='Bans a user')
    @app_commands.describe(member='The user to ban', reason='The reason for banning the user')
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        await interaction.response.defer(ephemeral=True)
        await member.send(embed=discord.Embed(title='Banned!', description=f'You have been banned from MacApps', color=discord.Color.red()))
        await member.ban(reason=reason)
        await interaction.followup.send(embed=discord.Embed(title='Banned!', description=f'Banned {member.mention}', color=discord.Color.green()))

    @app_commands.command(name='mute', description='Timeouts a user')
    @app_commands.default_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, seconds: int = 0, minutes: int = 0, hours: int = 0, days: int = 0, reason: str = None):
        duration = datetime.timedelta(seconds=seconds, minutes=minutes, hours= hours, days=days)
        await member.timeout(duration, reason=reason)

        await member.send(embed=discord.Embed(title='Timed out!', description=f'You have been timed out in MacApps for {duration}', color=discord.Color.red()))
        await interaction.response.send_message(embed=discord.Embed(title='Timed out!', description=f'Timed out {member.mention} for {duration}', color=discord.Color.green()), ephemeral=True)

    @app_commands.command(name='unmute', description='Unmutes a user')
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(member='The member to unmute')
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        await member.unmute()
        await interaction.response.send_message(embed=discord.Embed(title='Unmuted!', description=f'Unmuted {member.mention}', color=discord.Color.green()), ephemeral=True)
        await member.send(embed=discord.Embed(title='Unmuted!', description=f'You have been unmuted in MacApps', color=discord.Color.green()))

    @app_commands.command(name='warn', description='Warns a user')
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(member='The member to warn', reason='The reason for warning the member')
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        await interaction.response.defer(ephemeral=True)
        await member.send(embed=discord.Embed(title='Warned!', description=f'You have been warned in MacApps for reason: {reason}', color=discord.Color.red()))
        await interaction.followup.send(embed=discord.Embed(title='Warned!', description=f'Warned {member.mention}', color=discord.Color.green()))

    
    

    
    
    
async def setup(bot):
    await bot.add_cog(Moderation(bot=bot))