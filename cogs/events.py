import dhooks
import discord
import traceback
import psutil
import os
import random

from collections import deque
from datetime import datetime
from dhooks import Webhook
from discord.ext.commands import errors
from utils import default, lists


class SnipeHistory(deque):
    def __init__(self):
        super().__init__(maxlen=5)

    def __repr__(self):
        return "Pawbot Snipe History"


async def send_cmd_help(ctx):
    if ctx.invoked_subcommand:
        _help = await ctx.bot.formatter.format_help_for(ctx, ctx.invoked_subcommand)
    else:
        _help = await ctx.bot.formatter.format_help_for(ctx, ctx.command)

    for page in _help:
        await ctx.send(page)


class Events:
    def __init__(self, bot):
        self.bot = bot
        self.config = default.get("config.json")
        self.process = psutil.Process(os.getpid())

    async def getserverstuff(self, member):
        query = "SELECT * FROM adminpanel WHERE serverid = $1;"
        row = await self.bot.db.fetchrow(query, member.guild.id)
        if row is None:
            query = "INSERT INTO adminpanel VALUES ($1, $2, $3, $4, $5, $6, $7);"
            await self.bot.db.execute(query, member.guild.id, 0, 0, 1, 0, 0, 0)
            query = "SELECT * FROM adminpanel WHERE serverid = $1;"
            row = await self.bot.db.fetchrow(query, member.guild.id)
        return row

    async def getautomod(self, member):
        query = "SELECT * FROM automod WHERE serverid = $1;"
        row = await self.bot.db.fetchrow(query, member.guild.id)
        if row is None:
            query = "INSERT INTO automod VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9);"
            await self.bot.db.execute(query, member.guild.id, 0, 0, 0, 0, 10, 10, 0, 0)
            query = "SELECT * FROM automod WHERE serverid = $1;"
            row = await self.bot.db.fetchrow(query, member.guild.id)
        return row

    async def getstorestuff(self, member):
        storequery = "SELECT * FROM idstore WHERE serverid = $1;"
        storerow = await self.bot.db.fetchrow(storequery, member.guild.id)
        if storerow is None:
            query = "INSERT INTO idstore VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9);"
            await self.bot.db.execute(
                query, member.guild.id, "Default", "Default", 0, 0, 0, 0, 0, 0
            )
            query = "SELECT * FROM idstore WHERE serverid = $1;"
            storerow = await self.bot.db.fetchrow(query, member.guild.id)
        return storerow

    async def on_command_error(self, ctx, err):
        if isinstance(err, (errors.BadArgument, errors.MissingRequiredArgument)):
            await send_cmd_help(ctx)

        elif isinstance(err, errors.CommandInvokeError):
            err = err.original

            _traceback = traceback.format_tb(err.__traceback__)
            _traceback = "".join(_traceback)
            error = "```py\n{2}{0}: {3}\n```".format(
                type(err).__name__, ctx.message.content, _traceback, err
            )
            logchannel = self.bot.get_channel(508_420_200_815_656_966)
            await ctx.send(
                "There was an error in processing the command, our staff team have been notified, and will be in contact soon."
            )
            await logchannel.send(
                f"`ERROR`\n{error}\nRoot Server: {ctx.guild.name} ({ctx.guild.id})\nRoot Channel: {ctx.channel.name} ({ctx.channel.id})\nRoot User: {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})"
            )

        elif isinstance(err, errors.CheckFailure):
            pass

        elif isinstance(err, errors.CommandOnCooldown):
            await ctx.send(
                f"This command is on cooldown... try again in {err.retry_after:.0f} seconds."
            )

        elif isinstance(err, errors.CommandNotFound):
            pass

    async def on_ready(self):
        if not hasattr(self.bot, "uptime"):
            self.bot.uptime = datetime.utcnow()
        webhook = Webhook(self.config.readywebhook, is_async=True)
        embed = dhooks.Embed(
            title=f"Reconnected, Online and Operational!",
            description="Ready Info",
            color=5_810_826,
            timestamp=True,
        )
        embed.set_author(
            name=f"PawBot",
            url="https://discordapp.com/oauth2/authorize?client_id=460383314973556756&scope=bot&permissions=469888118",
            icon_url="https://cdn.discordapp.com/avatars/460383314973556756/d96ff7682f89483c4864f7af4b3a096c.png?size=2048",
        )
        embed.add_field(name="Guilds", value=f"**{len(self.bot.guilds)}**", inline=True)
        embed.add_field(name="Users", value=f"**{len(self.bot.users)}**", inline=True)
        await webhook.execute(embeds=embed)
        await webhook.close()
        await self.bot.change_presence(
            activity=discord.Game(type=0, name=random.choice(lists.randomPlayings)),
            status=discord.Status.online,
        )

    async def on_guild_join(self, guild):
        if not guild.icon_url:
            guildicon = "https://cdn.discordapp.com/attachments/443347566231289856/513380120451350541/2mt196.jpg"
        else:
            guildicon = guild.icon_url
        findbots = sum(1 for member in guild.members if member.bot)
        findusers = sum(1 for member in guild.members if not member.bot)
        webhook = Webhook(self.config.guildjoinwebhook, is_async=True)
        embed = dhooks.Embed(
            description=f"I've joined {guild.name}!", color=5_810_826, timestamp=True
        )
        embed.set_author(
            name=f"{guild.name}",
            url="https://discordapp.com/oauth2/authorize?client_id=460383314973556756&scope=bot&permissions=469888118",
            icon_url=guildicon,
        )
        embed.set_thumbnail(url=guildicon)
        embed.add_field(
            name="Info",
            value=f"New guild count: **{len(self.bot.guilds)}**\nOwner: **{guild.owner}**\nUsers/Bot Ratio: **{findusers}/{findbots}**",
        )
        await webhook.execute(embeds=embed, username=guild.name, avatar_url=guildicon)
        await webhook.close()

    async def on_guild_remove(self, guild):
        if not guild.icon_url:
            guildicon = "https://cdn.discordapp.com/attachments/443347566231289856/513380120451350541/2mt196.jpg"
        else:
            guildicon = guild.icon_url
        findbots = sum(1 for member in guild.members if member.bot)
        findusers = sum(1 for member in guild.members if not member.bot)
        webhook = Webhook(self.config.guildleavewebhook, is_async=True)
        embed = dhooks.Embed(
            description=f"I've left {guild.name}...", color=5_810_826, timestamp=True
        )
        embed.set_author(
            name=f"{guild.name}",
            url="https://discordapp.com/oauth2/authorize?client_id=460383314973556756&scope=bot&permissions=469888118",
            icon_url=guildicon,
        )
        embed.set_thumbnail(url=guildicon)
        embed.add_field(
            name="Info",
            value=f"New guild count: **{len(self.bot.guilds)}**\nOwner: **{guild.owner}**\nUsers/Bot Ratio: **{findusers}/{findbots}**",
        )
        await webhook.execute(embeds=embed, username=guild.name, avatar_url=guildicon)
        await webhook.close()

    async def on_member_join(self, member):
        adminpanelcheck = await self.getserverstuff(member)
        serverstorecheck = await self.getstorestuff(member)
        automodcheck = await self.getautomod(member)
        if adminpanelcheck["automod"] is 1:
            if automodcheck["lockdown"] is 1:
                await member.send(
                    f"Sorry but **{member.guild.name}** is currently on lockdown, try again later! >.<"
                )
                return await member.kick(reason="[Automod] Lockdown Enabled")
            if automodcheck["autorole"] is 1:
                try:
                    autorolerole = member.guild.get_role(
                        serverstorecheck["autorolerole"]
                    )
                    await member.add_roles(autorolerole)
                except discord.Forbidden:
                    pass
        if adminpanelcheck["joins"] is 1:
            try:
                welcomechannel = member.guild.get_channel(serverstorecheck["joinchan"])
                welcomemsg = (
                    serverstorecheck["joinmsg"]
                    .replace("%member%", f"{member.name}#{member.discriminator}")
                    .replace(
                        "Default",
                        f"Please welcome **{member.name}#{member.discriminator}!**",
                    )
                )
                await welcomechannel.send(welcomemsg)
            except discord.Forbidden:
                pass

    async def on_member_remove(self, member):
        adminpanelcheck = await self.getserverstuff(member)
        serverstorecheck = await self.getstorestuff(member)
        if adminpanelcheck["leaves"] is 1:
            try:
                byechan = member.guild.get_channel(serverstorecheck["leavechan"])
                byemsg = (
                    serverstorecheck["leavemsg"]
                    .replace("%member%", f"{member.name}#{member.discriminator}")
                    .replace(
                        "Default",
                        f"Goodbye **{member.name}#{member.discriminator}** we'll miss you...",
                    )
                )
                await byechan.send(byemsg)
            except discord.Forbidden:
                pass

    async def on_message_delete(self, message):
        try:
            self.bot.snipes[message.channel.id].appendleft(message)
        except:
            self.bot.snipes[message.channel.id] = SnipeHistory()
            self.bot.snipes[message.channel.id].appendleft(message)

        adminpanelcheck = await self.getserverstuff(message)
        serverstorecheck = await self.getstorestuff(message)


def setup(bot):
    bot.add_cog(Events(bot))
