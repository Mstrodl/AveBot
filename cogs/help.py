import discord
from discord.ext import commands
# config, check_level, get_git_commit_text, get_git_revision_short_hash

import time
import datetime

import socket


class Help:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def helplong(self):
        """Links to a longer, better help file."""
        await self.bot.say("See the proper help file at: https://github.com/ardaozkal/AveBot/blob/rewrite/helplong.md")

    @commands.command()
    async def servercount(self):
        """Returns the amount of servers AveBot is in."""
        await self.bot.say("AveBot is in {} servers.".format(str(len(self.bot.servers))))

    @commands.command(pass_context=True)
    async def whoami(self, contx):
        """Returns your information."""
        await self.bot.say(
            "You are {} (`{}`) and your permission level is {} (0 = banned, 1 = normal, 2 = authenticated, 8 = mod, 9 = owner).".format(
                contx.message.author.name, contx.message.author.id, check_level(contx.message.author.id)))

    @commands.command(pass_context=True)
    async def info(self, contx):
        """Returns bot's info."""
        st = str(datetime.datetime.now()).split('.')[0]
        em = discord.Embed(title='AveBot Info',
                           description='You\'re running AveBot Rewrite.\nGit hash: `{}`\nLast git message: `{}`\nHostname: `{}`\nLocal Time: `{}`'
                           .format(get_git_revision_short_hash(), get_git_commit_text(), socket.gethostname(), st),
                           colour=0xDEADBF)
        em.set_author(name='AveBot', icon_url='https://s.ave.zone/c7d.png')
        await self.bot.send_message(contx.message.channel, embed=em)

    @commands.command(pass_context=True)
    async def ping(self, contx):
        """Calculates the ping between the bot and the discord server."""
        before = time.monotonic()
        tmp = await self.bot.send_message(contx.message.channel, 'Calculating...')
        after = time.monotonic()
        ping_ms = (after - before) * 1000
        message_text = ':ping_pong: Ping is {}ms'.format(ping_ms[:6])
        await self.bot.edit_message(tmp, message_text)

    @commands.command(pass_context=True)
    async def contact(self, contx, *, contact_text: str):
        """Contacts developers with a message."""
        em = discord.Embed(title='Contact received!',
                           description='**Message by:** {} ({})\n on {} at {}\n**Message content:** {}'.format(str(
                               contx.message.author), contx.message.author.id, contx.message.channel.name,
                               contx.message.server.name, contact_text),
                           colour=0xDEADBF)
        em.set_author(name='AveBot', icon_url='https://s.ave.zone/c7d.png')
        await self.bot.send_message(discord.Object(id=config['base']['support-channel']), embed=em)

        em = discord.Embed(title='Contact sent!',
                           description='Your message has been delivered to the developers.',
                           colour=0xDEADBF)
        em.set_author(name='AveBot', icon_url='https://s.ave.zone/c7d.png')
        await self.bot.send_message(contx.message.channel, embed=em)


def setup(bot):
    bot.add_cog(Help(bot))
