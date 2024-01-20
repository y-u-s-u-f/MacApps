import discord
import re
import datetime
import os
import requests
import json
import asyncio
from bs4 import BeautifulSoup
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from discord.ext import tasks

load_dotenv()

bot = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(bot)



@tasks.loop(hours=24)
async def sendFreeApps():
    webhook = discord.SyncWebhook.from_url(
    f"https://discord.com/api/webhooks/1193700195322560543/1dvD02JlbTVS9Xxu0zpE3Ez2GUN95n_BVMDTC3v8vzJ7xAc1ULtNYTBSZpVMEo3NgB2e"
    )
    url = f'https://appadvice.com/apps-gone-free/{datetime.datetime.now().strftime("%Y-%m-%d")}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    free_apps = soup.find_all('div', class_='aa_app__icon aa_bg aa_bg-888--1')
    app_list = []

    for app in free_apps:
        app_name = app.find('img').get('alt')
        app_list.append(app_name)

    # Get only half of the list
    half_length = len(app_list) // 2
    app_list = app_list[:half_length]
    freeAppsEm = discord.Embed(title='Apps Gone Free Today', description="\n".join(app_list), color=discord.Color.blurple())
    freeAppsEm.set_footer(text=f'https://appadvice.com/apps-gone-free/', icon_url='https://media.licdn.com/dms/image/C560BAQGLpOtO6VB09Q/company-logo_200_200/0/1630663861224/appadvice_logo?e=2147483647&v=beta&t=wbZXD3hheDKs6TMWU3rINJCsFa0R5zufCLDlaN1tRwk')
    await webhook.send(embed=freeAppsEm)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} in {len(bot.guilds)} servers!')
    await tree.sync()
    sendFreeApps.start()

@tree.command(name='ping', description="Sends the bot's latency")
async def ping(interaction: discord.Interaction):
  embed = discord.Embed(title=f"Pong! {round(bot.latency * 1000)}ms")
  await interaction.response.send_message(embed=embed, color=discord.Color.green())


@tree.command(name='help', description='Shows a list of all the commands')
async def help(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title='Help', description='Here is a list of all the commands:', color=discord.Color.blue())
    for command in tree.get_commands():
        if not command.name == 'help':
            embed.add_field(name=command.name, value=command.description, inline=False)
        else:
            embed.add_field(name=command.name, value="You're already here!", inline=False)
    await interaction.followup.send(embed=embed)



class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green, emoji='✅')
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != interaction.channel.owner:
            await interaction.response.send_message(embed=discord.Embed(title='❌ You are not the owner of this thread.', color=discord.Color.red()), ephemeral=True)
            return
        await interaction.response.send_message(embed=discord.Embed(title='Confirming...', color=discord.Color.green()))
        button.disabled = True
        self.children[1].disabled = True
        await interaction.message.edit(view=self)

        self.value = True
        self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey, emoji='❌')
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != interaction.channel.owner:
            await interaction.response.send_message(embed=discord.Embed(title='❌ You are not the owner of this thread.', color=discord.Color.red()), ephemeral=True)
            return
        await interaction.response.send_message(embed=discord.Embed(title='Cancelling...', color=discord.Color.yellow()))
        button.disabled = True
        self.children[0].disabled = True
        await interaction.message.edit(view=self)

        self.value = False
        self.stop()

async def lock_thread(interaction: discord.Interaction, reason:str=None):
    em = discord.Embed(title="🔒 Locked!", description=f"Reason: {reason}" if reason else None, timestamp=datetime.datetime.now(), color=discord.Color.green())
    em.set_footer(text=f'Locked by {interaction.user.name}', icon_url=interaction.user.avatar.url)
    await interaction.followup.send(embed=discord.Embed(title="Locking...", color=discord.Color.green()), ephemeral=True)
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


@tree.command(name='lock', description='Locks the thread')
@app_commands.describe(reason='The reason for locking the thread')
async def lock(interaction: discord.Interaction, reason:str=None):
    await interaction.response.defer(ephemeral=True)
    if not isinstance(interaction.channel, discord.Thread):
       await interaction.response.send_message(embed=discord.Embed(title='❌ This command can only be used in threads.', color=discord.Color.red()), ephemeral=True)
       return
    view = Confirm()
    if interaction.user == interaction.channel.owner or interaction.permissions.manage_threads:
        await lock_thread(interaction, reason)
    else:
      await interaction.channel.send(f'<@{interaction.channel.owner_id}>',embed=discord.Embed(title='Do you want to lock this thread?', color=discord.Color.green(), avatar_url=interaction.user.avatar.url).set_footer(f'{interaction.user.name} is requesting to lock this thread.'), view=view)

      await view.wait()
      if view.value:
        await lock_thread(interaction, reason)
      else:
          await interaction.followup.send(embed=discord.Embed(title="❌ Cancelled", color=discord.Color.red()))



  
@tree.command(name='unlock', description='Unlocks the thread')
@app_commands.describe(thread='The ID or link of the thread to unlock', reason='The reason for unlocking the thread')
async def unlock(interaction: discord.Interaction, thread: str=None, reason:str=None):
    await interaction.response.defer(ephemeral=False)
    if thread is None and isinstance(interaction.channel, discord.Thread):
        thread = interaction.channel.id
    if not thread:
        await interaction.followup.send(embed=discord.Embed(title='❌ Failed', description='Please either use this command in a thread and/or specify the thread ID/link.', color=discord.Color.red()))
        return
    if str(thread).isdigit():
        thread = await interaction.guild.fetch_channel(int(thread))
    elif re.match(r'(https?:\/\/)?(ptb\.|canary\.)?discord(app)?\.(com|net)\/channels\/([0-9]+)\/([0-9]+)', thread):
        thread = await bot.fetch_channel(int(re.match(r'(https?:\/\/)?(ptb\.|canary\.)?discord(app)?\.(com|net)\/channels\/([0-9]+)\/([0-9]+)', thread).group(6)))

    if not isinstance(thread, discord.Thread):
        await interaction.followup.send(embed=discord.Embed(title='❌ Failed', description='Not a thread!', color=discord.Color.red()))
        return
    if not thread.locked and not thread.archived:
        await interaction.followup.send(embed=discord.Embed(title="❌ This thread is already unlocked!", color=discord.Color.red()))
        return
    await unlock_thread(interaction, thread, reason)


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
        await bot.get_channel(1017835578370310187).send(embed=embed)

        embed=discord.Embed(title='Your application has been submitted!', description='We will get back to you soon!', color=discord.Color.green())
        embed.add_field(name='App Name(s)', value=self.app_name.value, inline=False)
        embed.add_field(name='App Description(s)', value=self.app_desc.value, inline=False) if self.app_desc.value else None
        embed.add_field(name='App Link(s)', value=self.app_link.value, inline=False)
        embed.add_field(name='Notes', value=self.notes.value, inline=False) if self.notes.value else None
        await interaction.response.send_message(embed=embed, ephemeral=True)



@tree.command(name='partner', description='Submit your app(s) to partner with our server')
async def partner(interaction: discord.Interaction):

    await interaction.response.send_modal(PartnerModal())




bot.run(os.getenv('TOKEN'))