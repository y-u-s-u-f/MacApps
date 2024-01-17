import discord
import re
import datetime
import os
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

bot = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} in {len(bot.guilds)} servers!')
    await tree.sync()

@tree.command(name='ping', description="Sends the bot's latency")
async def ping(interaction: discord.Interaction):
  embed = discord.Embed(title=f"Pong! {round(bot.latency * 1000)}ms")
  await interaction.response.send_message(embed=embed, color=discord.Color.green())


class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
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

    # This one is similar to the confirmation button except sets the inner value to `False`
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



@tree.command(name='lock', description='Locks the thread')
@app_commands.describe(reason='The reason for locking the thread')
async def lock(interaction: discord.Interaction, reason:str=None):
    if not isinstance(interaction.channel, discord.Thread):
       await interaction.response.send_message(embed=discord.Embed(title='❌ This command can only be used in threads.', color=discord.Color.red()), ephemeral=True)
       return
    await interaction.response.defer(ephemeral=False)
    view = Confirm()
    if interaction.user == interaction.channel.owner or interaction.permissions.manage_threads:
        em = discord.Embed(title="🔒 Locked!", description=f"Reason: {reason}" if reason else None, color=discord.Color.green())
        await interaction.followup.send(embed=em)
        await interaction.channel.edit(name=
                                   '[🔒] ' + interaction.channel.name,
                                   locked=True,
                                   archived=True, 
                                   reason=reason if reason else None)
    else:
      await interaction.followup.send(f'<@{interaction.channel.owner_id}>',embed=discord.Embed(title='Do you want to lock this thread?', color=discord.Color.green()), view=view)

      # Wait for the View to stop listening for input...
      await view.wait()
      if view.value:
        em = discord.Embed(title="🔒 Locked!", description=f"Reason: {reason}" if reason else None, timestamp=datetime.datetime.utcnow(), color=discord.Color.green())
        await interaction.followup.send(embed=em)
        await interaction.channel.edit(name=
                                   '[🔒] ' + interaction.channel.name,
                                   locked=True,
                                   archived=True,
                                   reason=reason if reason else None)
      else:
          await interaction.followup.send(embed=discord.Embed(title="❌ Cancelled", color=discord.Color.red()))



  
@tree.command(name='unlock', description='Unlocks the thread')
@app_commands.describe(thread='The ID or link of the thread to unlock', reason='The reason for unlocking the thread')
async def unlock(interaction: discord.Interaction, thread: str=None, reason:str=None):
    await interaction.response.defer(ephemeral=False)
    if thread is None and isinstance(interaction.channel, discord.Thread):
        thread = interaction.channel
    if not thread:
        await interaction.followup.send(embed=discord.Embed(title='❌ Failed', description='Please either use this command in a thread and/or specify the thread ID/link.', color=discord.Color.red()), ephemeral=True)
        return
    if re.match(r'(https?:\/\/)?(ptb\.|canary\.)?discord(app)?\.(com|net)\/channels\/([0-9]+)\/([0-9]+)', thread):
        thread = await bot.fetch_channel(int(re.match(r'(https?:\/\/)?(ptb\.|canary\.)?discord(app)?\.(com|net)\/channels\/([0-9]+)\/([0-9]+)', thread).group(6)))
    elif thread.isdigit():
        thread = await interaction.guild.fetch_channel(int(thread))
    if not isinstance(thread, discord.Thread):
        await interaction.followup.send(embed=discord.Embed(title='❌ Failed', description='Not a thread!', color=discord.Color.red()), ephemeral=True)
        return
    if not thread.locked and not thread.archived:
        await interaction.followup.send(embed=discord.Embed(title="❌ This thread is already unlocked!", color=discord.Color.red(), ephemeral=True))
        return
    await interaction.followup.send(embed=discord.Embed(title="🔓 Unlocked!", description=f"Reason: {reason}" if reason else None, color=discord.Color.green()))
    await thread.edit(name=thread.name.replace('[🔒] ', ''), locked=False, archived=False, reason=reason or None)
    await thread.send(embed=discord.Embed(
        title="This thread has been unlocked!",
        description=f"Reason: {reason}" if reason else None,
        timestamp=datetime.datetime.utcnow(),
        footer=f"Unlocked by {interaction.user.name}",
        color=discord.Color.green()
    ))

# create the modal for partnering
class PartnerModal(discord.ui.Modal, title='Partner with us!'):
    app_name = discord.ui.TextInput(label='App Name(s)', placeholder='Your app name(s)', style=discord.TextStyle.short, required=True)
    app_desc = discord.ui.TextInput(label='Long App Description(s)', placeholder='Your app description(s)', style=discord.TextStyle.long, required=False)
    app_link = discord.ui.TextInput(label='App Link(s)', placeholder='Your app link(s)', required=True)

    async def on_submit(self, interaction: discord.Interaction):
        embed=discord.Embed(title='New Partner Application!', description=f'{interaction.user.mention} has submitted an application!', timestamp=datetime.datetime.utcnow(), color=discord.Color.green())
        embed.add_field(name='App Name(s)', value=self.app_name.value, inline=False)
        embed.add_field(name='App Description(s)', value=self.app_desc.value, inline=False)
        embed.add_field(name='App Link(s)', value=self.app_link.value, inline=False)
        await bot.get_channel(1017835578370310187).send(embed=embed)
        embed=discord.Embed(title='Your application has been submitted!', description='We will get back to you soon!', color=discord.Color.green())
        embed.add_field(name='App Name(s)', value=self.app_name.value, inline=False)
        embed.add_field(name='App Description(s)', value=self.app_desc.value, inline=False)
        embed.add_field(name='App Link(s)', value=self.app_link.value, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name='partner', description='Submit your app(s) to partner with our server')
async def partner(interaction: discord.Interaction):
    # open the partner modal
    await interaction.response.send_modal(PartnerModal())







bot.run(os.getenv('TOKEN'))