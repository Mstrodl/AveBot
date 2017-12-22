import asyncio
import datetime
import os
import re
import socket
import subprocess
import time
import traceback
import inspect
import locale

from pathlib import Path
from decimal import *
from dateutil import parser

import random
import requests

import discord
from discord.ext import commands

import configparser

import PIL.Image
import PIL.ImageFilter
import PIL.ImageOps

import logging
import logging.handlers
import sys

# TODO: COGS https://gist.github.com/leovoel/46cd89ed6a8f41fd09c5
# TODO: >get >dget size and timeouts

config_file_name = "avebot.ini"
log_file_name = "avebot.log"

perm_names = {'0': 'Banned', '1': 'Regular User', '2': 'Privileged User', '8': 'Mod', '9': 'Owner'}

max_file_size = 1000 * 1000 * 8 # Limit of discord (non-nitro) is 8MB (not MiB)
backup_count = 10000 # random big number
file_handler = logging.handlers.RotatingFileHandler(filename=log_file_name, maxBytes=max_file_size, backupCount=backup_count)
stdout_handler = logging.StreamHandler(sys.stdout)
handlers = [file_handler, stdout_handler]

old_commands = [">roll", ">info", ">govegan", ">helplong", ">help", ">trump", ">erdogan", ">servercount", ">serverlist", ">whoami", ">sbahjify", ">jpegify", ">ultrajpegify", ">mazeify", ">ultramazeify", ">joelify", ">ultrajoelify", ">unfurl", ">addavebot", ">contact", ">sinfo", ">uinfo", ">dig", ">resolve", ">!", ">unixtime", ">epoch", ">ping", ">exit", ">pull", ">addpriv", ">rmpriv", ">addmod", ">rmmod", ">fetchlog", ">ban", ">unban", ">eval", ">say", ">material", ">get", ">dget", ">xkcd", ">xkcdlatest", ">copypasta", ">copypastasell", ">stockchart", ">chart", ">c", ">render", ">bigly", ">howmanymessages", ">log", ">logall", ">similar", ">typo", ">soundslike", ">rhyme", ">howold", ">stock", ">s", ">fetchlog"]

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=handlers
)

config = configparser.ConfigParser()

if not Path(config_file_name).is_file():
    logging.warning("No config file ({}) found, please create one from avebot.ini.example file.".format(config_file_name))
    exit(3)

config.read(config_file_name)

prefix = config['base']['prefix']
locale.setlocale(locale.LC_ALL, '')

def get_git_commit_text():
    return str(subprocess.check_output(['git', 'log', '-1', '--pretty=%B']).strip())[2:-1]


def git_pull():
    subprocess.call(["git", "pull"])


def get_git_revision_short_hash():
    return str(subprocess.check_output(['git', 'log', '-1', '--pretty=%h']).strip())[2:-1]


description = 'AveBot Rewrite\nGit Hash: {}\nLast Commit: {}' \
    .format(get_git_revision_short_hash(), get_git_commit_text())
bot = commands.Bot(command_prefix=prefix, description=description)


def check_level(discord_id: str):
    #  = banned, 1 = regular user, 2 = privileged, 8 = mod, 9 = owner
    try:
        perm = config['permissions'][discord_id]
        if perm:
            return perm
        else:
            return "1"
    except KeyError:
        return "1"


def save_config():
    with open(config_file_name, 'w') as configfile:
        config.write(configfile)


def download_file(url,
                  local_filename):  # This function is based on https://stackoverflow.com/a/16696317/3286892 by Poman Podlinov (https://stackoverflow.com/users/427457/roman-podlinov), modified by Avery (https://github.com/aveao), licensed CC-BY-SA 3.0
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                # f.flush() commented by recommendation from J.F.Sebastian


@bot.event
async def on_ready():
    st = str(datetime.datetime.now()).split('.')[0]
    logging.info('Logged in as')
    logging.info(bot.user.name)
    logging.info(bot.user.id)
    logging.info('------')
    try:
        await asyncio.sleep(3)
        await bot.change_presence(game=discord.Game(name='{}help | {}'.format(prefix, get_git_revision_short_hash())))
        em = discord.Embed(title='AveBot initialized!',
                           description='Git hash: `{}`\nLast git message: `{}`\nHostname: `{}`\nLocal Time: `{}`\nLogs are below.'
                           .format(get_git_revision_short_hash(), get_git_commit_text(), socket.gethostname(), st),
                           colour=0xDEADBF)
        await bot.send_message(discord.Object(id=config['base']['main-channel']), embed=em)
        await bot.send_file(discord.Object(id=config['base']['main-channel']), log_file_name)
        #open(log_file_name, 'w').close()  # Clears log
    except Exception:
        logging.error(traceback.format_exc())
        bot.close()
        exit(1)

async def catch_error(text):
    logging.error("Error: " + text)
    em = discord.Embed(title="An error happened", description=text,
                       colour=0xcc0000)
    await bot.send_message(discord.Object(id=config['base']['main-channel']), embed=em)

@bot.command(pass_context=True)
async def roll(contx, dice: str):
    """Rolls a dice in NdN format."""

    modification = 0
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await catch_error(traceback.format_exc())
        await bot.say('Format has to be in NdN!')
        return

    try:
        modifier = contx.message.content.replace(prefix+"roll "+dice, "").replace(" ", "")
        logging.error("modifier is " + modifier)
        if modifier.startswith("+"):
            modification = int(modifier.replace("+", ""))
        elif modifier.startswith("-"):
            modification = -int(modifier.replace("-", ""))
    except Exception:
        await catch_error(traceback.format_exc())
        await bot.say('Exception during modifier stuff!')
        return

    result = ', '.join(str(random.randint(1, limit)+modification) for r in range(rolls))
    await bot.say("{} (Modifier: {})".format(result, modification))


@bot.command(pass_context=True)
async def info(contx):
    """Returns bot's info."""
    st = str(datetime.datetime.now()).split('.')[0]
    em = discord.Embed(title='AveBot Info',
                       description='You\'re running AveBot Rewrite.\nGit hash: `{}`\nLast git message: `{}`\nHostname: `{}`\nLocal Time: `{}`'
                       .format(get_git_revision_short_hash(), get_git_commit_text(), socket.gethostname(), st),
                       colour=0xDEADBF)
    em.set_author(name='AveBot Rewrite', icon_url='https://s.ave.zone/c7d.png')
    await bot.send_message(contx.message.channel, embed=em)


@bot.command(hidden=True)
async def govegan():
    """Links a resource that'll make you reconsider eating meat."""
    await bot.say("https://zhangyijiang.github.io/puppies-and-chocolate/")


@bot.command(hidden=True)
async def trump():
    """Reveals some stuff about my political leaning."""
    await bot.say("**Did you mean:** `Misogynist`")


@bot.command(hidden=True)
async def erdogan():
    """Reveals some stuff about my political leaning."""
    await bot.say("**Did you mean:** `Dictator`")


@bot.command()
async def servercount():
    """Returns the amount of servers AveBot is in."""
    await bot.say("AveBot is in {} servers.".format(str(len(bot.servers))))


@bot.command()
async def serverlist():
    """Returns the list of servers AveBot is in."""
    avebot_servers = bot.servers
    text_to_post = "**AveBot is in {} servers:**\n".format(str(len(avebot_servers)))
    total_user_count = 0
    for server in avebot_servers:
        text_to_post += "• **{}** (**{} members**)\n".format(server.name.replace("@", ""), str(server.member_count))
        total_user_count += server.member_count
    text_to_post += "In total, AveBot is servicing **{} users**.".format(str(total_user_count))
    sliced_message = slice_message(text_to_post, 2000)
    for msg in sliced_message:
        await bot.say(msg)


@bot.command(pass_context=True)
async def whoami(contx):
    """Returns your information."""
    await bot.say(
        "You are {} (`{}`) and your permission level is {}.".format(
            contx.message.author.name, contx.message.author.id, perm_names[check_level(contx.message.author.id)]))

async def get_images(contx, caller_command):
    images_to_process = []
    for attach in contx.message.attachments:
        extension = os.path.splitext(attach['filename'])[1]
        filename = "files/powered-by-avebot-bot.ave.zone-{}att{}".format(contx.message.id, extension).split('?')[0]
        download_file(attach['proxy_url'], filename)
        if extension != ".jpg" or extension != ".jpeg":
            im = PIL.Image.open(filename)
            new_name = filename.replace(extension, ".jpg")
            im.save(new_name, "JPEG")
            filename = new_name
        images_to_process.append(filename)
    stuff_after = contx.message.content.replace(prefix + caller_command, "").replace(" ", "")
    if stuff_after != "" and stuff_after.startswith("http"):
        extension = str(os.path.splitext(stuff_after)[1].split('?')[0])
        filename = "files/powered-by-avebot-bot.ave.zone-{}txt{}".format(contx.message.id, extension)
        download_file(stuff_after, filename)
        if extension != ".jpg" or extension != ".jpeg":
            im = PIL.Image.open(filename)
            new_name = filename.replace(extension, ".jpg")
            im.save(new_name, "JPEG")
            filename = new_name
        images_to_process.append(filename)
    return images_to_process


async def get_image_links(contx, caller_command):
    image_links = []
    for attach in contx.message.attachments:
        image_links.append(attach['proxy_url'])
    stuff_after = contx.message.content.replace(prefix + caller_command, "").replace(" ", "")
    if stuff_after != "" and stuff_after.startswith("http"):
        image_links.append(stuff_after)
    return image_links

@bot.command(pass_context=True)
async def sbahjify(contx):
    """Makes images hella and sweet."""
    images_to_process = await get_images(contx, "sbahjify")
    msg_to_send = 'Processing image(s).' if len(
        images_to_process) != 0 else '{}: No images found. Try linking them or uploading them directly through discord.'.format(contx.message.author.mention)
    tmp = await bot.send_message(contx.message.channel, msg_to_send)
    for imgtp in images_to_process:
        logging.info("Processing {} for sbahj".format(imgtp))
        im = PIL.Image.open(imgtp)

        for _ in range(2):
            im = PIL.ImageOps.equalize(im)  # Drab-ify, but embellish otherwise hidden artifacts
            im = PIL.ImageOps.solarize(im, 250)  # Create weird blotchy artifacts, but inverts huge swaths
            im = PIL.ImageOps.posterize(im, 2)  # Flatten colors
            for _ in range(2):
                im = im.filter(PIL.ImageFilter.SHARPEN)
                im = im.filter(PIL.ImageFilter.SMOOTH)
                im = im.filter(PIL.ImageFilter.SHARPEN)
        w, h = im.size
        im = im.resize((w, int(h * 0.7)))
        im = PIL.ImageOps.equalize(im)  # Drab-ify, but embellish otherwise hidden artifacts
        im = im.filter(PIL.ImageFilter.SHARPEN)
        im = im.filter(PIL.ImageFilter.SHARPEN)
        out_filename = "files/sbahjify-{}".format(imgtp.replace("files/", ""))
        im.save(out_filename, quality=0, optimize=False, progressive=False)
        await bot.send_file(contx.message.channel, out_filename,
                            content="{}: Here's your image, hella and sweetened:".format(contx.message.author.mention))
    await asyncio.sleep(5)
    await bot.delete_message(tmp)


@bot.command(pass_context=True)
async def jpegify(contx):
    """Makes images jaypeg."""
    images_to_process = await get_images(contx, "jpegify")
    msg_to_send = 'Processing image(s).' if len(
        images_to_process) != 0 else '{}: No images found. Try linking them or uploading them directly through discord.'.format(contx.message.author.mention)
    tmp = await bot.send_message(contx.message.channel, msg_to_send)
    for imgtp in images_to_process:
        logging.info("Processing {} for jpeg".format(imgtp))
        im = PIL.Image.open(imgtp)

        im = im.filter(PIL.ImageFilter.SHARPEN)
        im = im.filter(PIL.ImageFilter.SMOOTH)
        out_filename = "files/jpegify-{}".format(imgtp.replace("files/", ""))
        im.save(out_filename, quality=0, optimize=False, progressive=False)
        await bot.send_file(contx.message.channel, out_filename,
                            content="{}: Here's your image, jpegified: (also try `{}ultrajpegify`!)".format(contx.message.author.mention, prefix))
    await asyncio.sleep(5)
    await bot.delete_message(tmp)


@bot.command(pass_context=True)
async def ultrajpegify(contx):
    """Makes images ultra jaypeg."""
    images_to_process = await get_images(contx, "ultrajpegify")
    msg_to_send = 'Processing image(s).' if len(
        images_to_process) != 0 else '{}: No images found. Try linking them or uploading them directly through discord.'.format(contx.message.author.mention)
    tmp = await bot.send_message(contx.message.channel, msg_to_send)
    for imgtp in images_to_process:
        logging.info("Processing {} for new ultrajpeg".format(imgtp))
        im = PIL.Image.open(imgtp)
        out_filename = "files/ultrajpegify-{}".format(imgtp.replace("files/", ""))
        w, h = im.size
        for x in range(0, 25):
            im = im.resize((int(w * 0.9), int(h * 1.1)))
            im.save(out_filename, quality=0, optimize=False, progressive=False)
            im = PIL.Image.open(out_filename)

            im = im.resize((int(w * 1.1), int(h * 0.9)))
            im.save(out_filename, quality=0, optimize=False, progressive=False)
            im = PIL.Image.open(out_filename)
        im = im.resize((w, h))
        im.save(out_filename, quality=0, optimize=False, progressive=False)
        await bot.send_file(contx.message.channel, out_filename,
                            content="{}: Here's your image, ULTRA jpegified:".format(contx.message.author.mention))
    await asyncio.sleep(5)
    await bot.delete_message(tmp)


@bot.command(pass_context=True)
async def mazeify(contx):
    """Makes images ultra jaypeg."""
    images_to_process = await get_images(contx, "mazeify")
    msg_to_send = 'Processing image(s).' if len(
        images_to_process) != 0 else '{}: No images found. Try linking them or uploading them directly through discord.'.format(contx.message.author.mention)
    tmp = await bot.send_message(contx.message.channel, msg_to_send)
    for imgtp in images_to_process:
        logging.info("Processing {} for new mazeify".format(imgtp))
        im = PIL.Image.open(imgtp)
        out_filename = "files/mazeify-{}".format(imgtp.replace("files/", ""))

        for x in range(0, 7):
            im = im.filter(PIL.ImageFilter.SHARPEN)
            im.save(out_filename, quality=0, optimize=False, progressive=False)
            im = PIL.Image.open(out_filename)
        await bot.send_file(contx.message.channel, out_filename,
                            content="{}: Here's your image, mazeified (also try `{}ultramazeify`!):".format(contx.message.author.mention, prefix))
    await asyncio.sleep(5)
    await bot.delete_message(tmp)


@bot.command(pass_context=True)
async def ultramazeify(contx):
    """Makes images maze."""
    images_to_process = await get_images(contx, "ultramazeify")
    msg_to_send = 'Processing image(s).' if len(
        images_to_process) != 0 else '{}: No images found. Try linking them or uploading them directly through discord.'.format(contx.message.author.mention)
    tmp = await bot.send_message(contx.message.channel, msg_to_send)
    for imgtp in images_to_process:
        logging.info("Processing {} for new ultramazeify".format(imgtp))
        im = PIL.Image.open(imgtp)
        out_filename = "files/ultramazeify-{}".format(imgtp.replace("files/", ""))

        for x in range(0, 10):
            for y in range(0, 10):
                im = im.filter(PIL.ImageFilter.SHARPEN)
            im.save(out_filename, quality=0, optimize=False, progressive=False)
            im = PIL.Image.open(out_filename)
        await bot.send_file(contx.message.channel, out_filename,
                            content="{}: Here's your image, ULTRA mazeified:".format(contx.message.author.mention))
    await asyncio.sleep(5)
    await bot.delete_message(tmp)


@bot.command(pass_context=True)
async def joelify(contx):
    """A tribute to joel (of vinesauce)."""
    try:
        images_to_process = await get_images(contx, "joelify")
        msg_to_send = 'Processing image(s).' if len(
            images_to_process) != 0 else '{}: No images found. Try linking them or uploading them directly through discord.'.format(contx.message.author.mention)
        tmp = await bot.send_message(contx.message.channel, msg_to_send)
        for imgtp in images_to_process:
            logging.info("Processing {} for joelification".format(imgtp))
            im = PIL.Image.open(imgtp)

            w, h = im.size
            for i in range(0, 100):
                w_val = (random.randint(1, 20) / 10)
                h_val = (random.randint(1, 20) / 10)
                im = im.resize((int(w * w_val), int(h * h_val)))
                im = im.resize((w, h))

            out_filename = "files/joelify-{}".format(imgtp.replace("files/", ""))
            im.save(out_filename, quality=50, optimize=False, progressive=False)
            await bot.send_file(contx.message.channel, out_filename,
                                content="{}: Here's your image, joelified (also try `{}ultrajoelify`):".format(contx.message.author.mention, prefix))
        await asyncio.sleep(5)
        await bot.delete_message(tmp)
    except Exception:
        await catch_error(traceback.format_exc())


@bot.command(pass_context=True)
async def ultrajoelify(contx):
    """A tribute to joel (of vinesauce)."""
    try:
        images_to_process = await get_images(contx, "ultrajoelify")
        msg_to_send = '{}: Processing image(s), this\'ll take some time (~30 secs).' if len(
            images_to_process) != 0 else '{}: No images found. Try linking them or uploading them directly through discord.'.format(contx.message.author.mention)
        tmp = await bot.send_message(contx.message.channel, msg_to_send)
        for imgtp in images_to_process:
            logging.info("Processing {} for ultra joelification".format(imgtp))
            im = PIL.Image.open(imgtp)

            w, h = im.size
            for i in range(0, 500):
                w_val = (random.randint(1, 20) / 10)
                h_val = (random.randint(1, 20) / 10)
                im = im.resize((int(w * w_val), int(h * h_val)))
                im = im.resize((w, h))

            out_filename = "files/joel{}".format(imgtp.replace("files/", ""))
            im.save(out_filename, quality=50, optimize=False, progressive=False)
            await bot.send_file(contx.message.channel, out_filename,
                                content="{}: Here's your image, ultra joelified:".format(contx.message.author.mention))
        await asyncio.sleep(5)
        await bot.delete_message(tmp)
    except Exception:
        await catch_error(traceback.format_exc())

@bot.command()
async def unfurl(link: str):
    """Finds where a URL redirects to."""
    resolved = unfurl_b(link)
    await bot.say("<{}> Unfurls to <{}>".format(link, resolved))


@bot.command()
async def invite():
    """Gives a link that can be used to add AveBot."""
    inviteurl = discord.utils.oauth_url(bot.user.id)
    await bot.say("You can use the following link to add AveBot to your server:\n<{}>".format(inviteurl))


@bot.command(pass_context=True)
async def contact(contx, *, contact_text: str):
    """Contacts developers with a message."""
    em = discord.Embed(description=contact_text,
                       colour=0xDEADBF)
    em.set_author(name="{} ({}) on \"{}\" at \"{}\"".format(str(contx.message.author), contx.message.author.id,
                                                            contx.message.channel.name,
                                                            contx.message.server.name),
                  icon_url=contx.message.author.avatar_url)
    await bot.send_message(discord.Object(id=config['base']['support-channel']), embed=em)

    em = discord.Embed(title='Contact sent!',
                       description='Your message has been delivered to the developers.',
                       colour=0xDEADBF)
    await bot.send_message(contx.message.channel, embed=em)


@bot.command(pass_context=True)
async def sinfo(contx):
    """Shows info about the current server."""
    the_server = contx.message.server
    em = discord.Embed(title='Server info of {} ({})'.format(the_server.name, the_server.id),
                       description='Count of users: **{}**\nRegion: **{}**\nOwner: **{}**\nVerification Level: **{}**\nCreated at: **{}**'.format(
                           str(the_server.member_count), str(the_server.region), str(the_server.owner),
                           str(the_server.verification_level), str(the_server.created_at)),
                       colour=0xDEADBF)
    # em.set_image(url=the_server.icon_url)
    em.set_thumbnail(url=the_server.icon_url)
    await bot.send_message(contx.message.channel, embed=em)


@bot.command(pass_context=True)
async def uinfo(contx):
    """Shows info about the user."""
    to_post = contx.message.mentions
    if len(to_post) == 0:  # if no one is mentioned, return current user
        to_post.append(contx.message.author)
    no_play_text = "No game is being played."
    for the_user in to_post:
        the_member = contx.message.server.get_member_named(str(the_user))
        played_game_text = no_play_text if the_member.game is None else the_member.game.name
        if played_game_text != no_play_text and the_member.game.type == 1:
            played_game_text += "**\nStreaming at: **{}".format(the_member.game.url)
        em = discord.Embed(title='User info of {} ({})'.format(str(the_user), the_user.id),
                           description='Registered at: **{}**\nJoined this server at: **{}**\nStatus: **{}**\nGame: **{}**\nIs bot: **{}**'.format(
                               str(the_user.created_at), str(the_member.joined_at), str(the_member.status),
                               played_game_text, (":white_check_mark:" if the_user.bot else ":x:")),
                           colour=0xDEADBF)

        em.set_thumbnail(url=the_user.avatar_url)
        await bot.send_message(contx.message.channel, embed=em)


@bot.command(hidden=True)
async def dig():
    await bot.say("Please use >resolve")


@bot.command()
async def resolve(domain: str):
    """Resolves a domain to a URL."""
    resolved = repr(socket.gethostbyname_ex(domain))
    await bot.say("Successfully resolved `{}` to `{}`".format(domain, resolved))


@bot.command(name="!")
async def _duckduckgo():
    """Resolves a duckduckgo bang."""
    await bot.say("No bang supplied. Try giving a bang like >!wiki.")


@bot.command(hidden=True)
async def unixtime():
    await bot.say("Current epoch time is: **{}**.".format(str(int(time.time()))))


@bot.command()
async def epoch():
    """Returns the Unix Time / Epoch."""
    await bot.say("Current epoch time is: **{}**.".format(str(int(time.time()))))


@bot.command(pass_context=True)
async def ping(contx):
    """Calculates the ping between the bot and the discord server."""
    before = time.monotonic()
    tmp = await bot.send_message(contx.message.channel, 'Calculating...')
    after = time.monotonic()
    ping_ms = (after - before) * 1000
    message_text = ':ping_pong: Ping is {}ms'.format(str(ping_ms)[:6])
    await bot.edit_message(tmp, message_text)


@bot.command(name='exit', pass_context=True)
async def _exit(contx):
    """Quits the bot (Owner only)."""
    if check_level(contx.message.author.id) == "9":
        await bot.say("Exiting AveBot, goodbye!")
        await bot.logout()


@bot.command(pass_context=True)
async def pull(contx):
    """Does a git pull (Owner only)."""
    if check_level(contx.message.author.id) == "9":
        tmp = await bot.send_message(contx.message.channel, 'Pulling...')
        git_pull()
        await bot.edit_message(tmp, "Pull complete, exiting!")
        await bot.logout()


@bot.command(pass_context=True)
async def addpriv(contx):
    """Adds a privileged user (Mod/Owner only)"""
    if check_level(contx.message.author.id) in ["8", "9"]:
        privtoadd = contx.message.mentions
        for dtag in privtoadd:
            if not (check_level(contx.message.author.id) == "8" and check_level(dtag.id) in ["8", "9"]):
                config['permissions'][dtag.id] = "2"
                em = discord.Embed(title='Added {} ({}) as privileged user.'.format(str(dtag), dtag.id),
                                   description='Welcome to the team!', colour=0x64dd17)
                await bot.send_message(contx.message.channel, embed=em)
        save_config()


@bot.command(pass_context=True)
async def rmpriv(contx):
    """Removes a privileged user (Mod/Owner only)"""
    if check_level(contx.message.author.id) in ["8", "9"]:
        privtorm = contx.message.mentions
        for dtag in privtorm:
            if not (check_level(contx.message.author.id) == "8" and check_level(dtag.id) in ["8", "9"]):
                config['permissions'][dtag.id] = "1"
                em = discord.Embed(
                    title='Removed {} ({}) as privileged user.'.format(str(dtag), dtag.id), colour=0x64dd17)
                await bot.send_message(contx.message.channel, embed=em)
        save_config()


@bot.command(pass_context=True)
async def addmod(contx):
    """Adds a mod (Owner only)"""
    if check_level(contx.message.author.id) in ["9"]:
        modstoadd = contx.message.mentions
        for dtag in modstoadd:
            config['permissions'][dtag.id] = "8"
            em = discord.Embed(title='Added {} ({}) as mod.'.format(str(dtag), dtag.id),
                               description='Welcome to the team!', colour=0x64dd17)
            await bot.send_message(contx.message.channel, embed=em)
        save_config()


@bot.command(pass_context=True)
async def rmmod(contx):
    """Removes a mod (Owner only)"""
    if check_level(contx.message.author.id) in ["9"]:
        modstorm = contx.message.mentions
        for dtag in modstorm:
            config['permissions'][dtag.id] = "1"
            em = discord.Embed(title='Removed {} ({}) as mod.'.format(str(dtag), dtag.id), colour=0x64dd17)
            await bot.send_message(contx.message.channel, embed=em)
        save_config()


@bot.command(pass_context=True)
async def fetchlog(contx):
    """Returns log"""
    if check_level(contx.message.author.id) in ["9"]:
        await bot.send_file(contx.message.channel, log_file_name, content="Here's the current log file:")


@bot.command(pass_context=True)
async def ban(contx):
    """Bans a user (Mod/Owner only)"""
    if check_level(contx.message.author.id) in ["8", "9"]:
        toban = contx.message.mentions
        for dtag in toban:
            if not (check_level(contx.message.author.id) == "8" and check_level(dtag.id) in ["8", "9"]):
                config['permissions'][dtag.id] = "0"
                em = discord.Embed(title='Banned {} ({}).'.format(str(dtag), dtag.id), colour=0x64dd17)
                await bot.send_message(contx.message.channel, embed=em)
        save_config()


@bot.command(name='eval', pass_context=True)
async def _eval(ctx, *, code: str):
    """Evaluates some code (Owner only)"""
    if check_level(ctx.message.author.id) in ["9"]:
        try:
            code = code.strip('` ')

            env = {
                'bot': bot,
                'ctx': ctx,
                'message': ctx.message,
                'server': ctx.message.server,
                'channel': ctx.message.channel,
                'author': ctx.message.author
            }
            env.update(globals())

            logging.info("running:" + repr(code))
            result = eval(code, env)
            if inspect.isawaitable(result):
                result = await result

            result = "Success! ```{}```".format(repr(result))
            for msg in slice_message(result, 1994):
                await bot.send_message(ctx.message.channel, "```{}```".format(msg))
        except:
            await bot.send_message(ctx.message.channel, "Error! ```{}```".format(traceback.format_exc()))
    else:
        logging.info("no perms for eval")


@bot.command(pass_context=True)
async def unban(contx):
    """Unbans a user (Mod/Owner only)"""
    if check_level(contx.message.author.id) in ["8", "9"]:
        tounban = contx.message.mentions
        for dtag in tounban:
            if not (check_level(contx.message.author.id) == "8" and check_level(dtag.id) in ["8", "9"]):
                config['permissions'][dtag.id] = "1"
                em = discord.Embed(
                    title='Unbanned {} ({}).'.format(str(dtag), dtag.id), colour=0x64dd17)
                await bot.send_message(contx.message.channel, embed=em)
        save_config()


@bot.command(pass_context=True)
async def say(contx, *, the_text: str):
    """Says something (Mod/Owner only)."""
    if check_level(contx.message.author.id) in ["8", "9"]:
        await bot.say(the_text)


@bot.command(pass_context=True)
async def material(contx, filename: str):
    """Gets a file from material.io's icons gallery (Privileged/Mod/Admin only)."""
    if check_level(contx.message.author.id) in ["2", "8", "9"]:
        if not filename.startswith('ic_'):
            filename = "ic_" + filename
        if not filename.endswith('.svg'):
            filename = filename + "_white_48px.svg"
        link = "https://storage.googleapis.com/material-icons/external-assets/v4/icons/svg/" + filename
        filename = "files/" + filename
        if not Path(filename).is_file():  # caching
            download_file(link, filename)
        await bot.send_file(contx.message.channel, filename,
                            content="Here's the file you requested.")


@bot.command(pass_context=True)
async def get(contx, link: str):
    """Gets a file from the internet (Privileged/Mod/Admin only)."""
    if check_level(contx.message.author.id) in ["2", "8", "9"]:
        filename = "files/" + link.split('/')[-1]
        download_file(link, filename)
        file_size = Path(filename).stat().st_size
        if file_size < 1024 * 1024 * 7:  # Limit of discord is 7MiB
            await bot.send_file(contx.message.channel, filename,
                                content="{}: Here's the file you requested.".format(contx.message.author.mention))
        else:
            bot.say(
                "{}: File is too big for discord (Limit is 7MiB, file is {}MiB).".format(contx.message.author.mention,
                                                                                         (file_size / (1024 * 1024))))
        os.remove(filename)  # Remove file when we're done with it (kinda risky TBH )


@bot.command(pass_context=True)
async def dget(contx, link: str):
    """Directly gets (doesn't care about name) a file from the internet (Privileged/Mod/Admin only)."""
    if check_level(contx.message.author.id) in ["2", "8", "9"]:
        filename = "files/requestedfile"
        download_file(link, filename)
        file_size = Path(filename).stat().st_size
        if file_size < 1024 * 1024 * 7:  # Limit of discord is 7MiB
            await bot.send_file(contx.message.channel, filename,
                                content="{}: Here's the file you requested.".format(contx.message.author.mention))
        else:
            bot.say(
                "{}: File is too big for discord (Limit is 7MiB, file is {}MiB).".format(contx.message.author.mention,
                                                                                         (file_size / (1024 * 1024))))
        os.remove(filename)  # Remove file when we're done with it (kinda risky TBH )


@bot.command()
async def xkcd(xkcdcount: int):
    """Returns info about the specified xkcd comic."""
    output = requests.get("https://xkcd.com/{}/info.0.json".format(str(xkcdcount)))
    j = output.json()
    resolvedto = j["img"]
    if resolvedto:
        messagecont = "**XKCD {0}:** `{1}`, published on {2}-{3}-{4} (DMY)\n**Image:** {5}\n**Alt text:** `{6}`\n" \
                      "Explain xkcd: <http://www.explainxkcd.com/wiki/index.php/{0}>" \
            .format(str(j["num"]), j["safe_title"], j["day"], j["month"], j["year"], resolvedto, j["alt"])
        await bot.say(messagecont)


@bot.command()
async def xkcdlatest():
    """Returns info about the latest xkcd comic."""
    output = requests.get("https://xkcd.com/info.0.json")
    j = output.json()
    resolvedto = j["img"]
    if resolvedto:
        messagecont = "**XKCD {0}:** `{1}`, published on {2}-{3}-{4} (DMY)\n**Image:** {5}\n**Alt text:** `{6}`\n" \
                      "Explain xkcd: <http://www.explainxkcd.com/wiki/index.php/{0}>" \
            .format(str(j["num"]), j["safe_title"], j["day"], j["month"], j["year"], resolvedto, j["alt"])
        await bot.say(messagecont)


@bot.command()
async def copypasta(ticker: str):
    """Generates a copypasta for StockStream using the given ticker."""
    copypasta_list = ["Kreygasm MUST Kreygasm BUY Kreygasm {} Kreygasm THIS Kreygasm ROUND Kreygasm",
                      "FutureMan BUY FutureMan {} FutureMan FOR FutureMan A FutureMan BRIGHTER FutureMan FUTURE FutureMan",
                      "Clappy Lemme buy a {0} before I send you a {0} Clappy",
                      "GivePLZ TRAIN TO PROFIT TOWN TakeNRG BUY {}! GivePLZ BUY {} TakeNRG",
                      "PogChamp {} PogChamp IS PogChamp OUR PogChamp LAST PogChamp HOPE PogChamp"]
    to_post = "Copypasta ready: `{}`".format(random.choice(copypasta_list).format(ticker.upper()))
    await bot.say(to_post)


@bot.command()
async def copypastasell(ticker: str):
    """Generates a copypasta for StockStream using the given ticker."""
    copypasta_list = ["Kreygasm MUST Kreygasm SELL Kreygasm {} Kreygasm THIS Kreygasm ROUND Kreygasm",
                      "Kreygasm TIME Kreygasm TO Kreygasm CASH Kreygasm IN Kreygasm {} Kreygasm",
                      "FutureMan SELL FutureMan {} FutureMan FOR FutureMan A FutureMan BRIGHTER FutureMan FUTURE FutureMan",
                      "Clappy Lemme sell a {0} before I send you a {0} Clappy",
                      "GivePLZ TRAIN TO PROFIT TOWN TakeNRG SELL {}! GivePLZ SELL {} TakeNRG",
                      "SELLING PogChamp {} PogChamp IS PogChamp OUR PogChamp LAST PogChamp HOPE PogChamp"]
    to_post = "Copypasta ready: `{}`".format(random.choice(copypasta_list).format(ticker.upper()))
    await bot.say(to_post)


@bot.command(hidden=True)
async def stockchart():
    await bot.say("Please use >c")


@bot.command(hidden=True)
async def chart():
    await bot.say("Please use >c")


def get_change_color(ticker: str):
    symbols = requests.get(
        "https://api.robinhood.com/quotes/?symbols={}".format(ticker.upper()))

    if symbols.status_code != 200:
        return 0x000000  # black

    symbolsj = symbols.json()["results"][0]

    current_price = (
        symbolsj["last_trade_price"] if symbolsj["last_extended_hours_trade_price"] is None else symbolsj[
            "last_extended_hours_trade_price"])
    diff = str(Decimal(current_price) - Decimal(symbolsj["previous_close"]))
    percentage = (100 * Decimal(diff) / Decimal(current_price))
    return _get_change_color(percentage)
    

def _get_change_color(change_percentage):
    change_percentage = str(change_percentage).split('.')[0] # before the dot
    if change_percentage.startswith('-'):
        int_perc = int(change_percentage) * -1  # make it positive
        colors = [0xFFEBEE, 0xFFCDD2, 0xEF9A9A, 0xE57373, 0xEF5350, 0xF44336, 0xE53935, 0xD32F2F, 0xC62828, 0xB71C1C,
                  0xD50000]
        return colors[10 if int_perc > 10 else int_perc]
    else:
        int_perc = int(change_percentage) + 1
        colors = [0xF1F8E9, 0xDCEDC8, 0xC5E1A5, 0xAED581, 0x9CCC65, 0x8BC34A, 0x7CB342, 0x689F38, 0x558B2F, 0x33691E,
                  0x1B5E20]
        return colors[10 if int_perc > 10 else int_perc]


@bot.command(pass_context=True)
async def c(contx, ticker: str):
    """Returns stock chart of the given ticker."""
    link = "https://finviz.com/chart.ashx?t={}&ty=c&ta=1&p=d&s=l".format(ticker.upper())
    em = discord.Embed(title='Chart for {0}'.format(ticker.upper()),
                       colour=get_change_color(ticker))
    em.set_image(url=link)
    em.set_footer(text='See https://finviz.com/quote.ashx?t={0} for more info.'.format(ticker.upper()))
    await bot.send_message(contx.message.channel, embed=em)


@bot.command(pass_context=True)
async def btc(contx):
    """Returns bitcoin chart and price info."""
    btc_currentprice_req = requests.get("https://api.coindesk.com/v1/bpi/currentprice/USD.json")
    btc_currentprice_json = btc_currentprice_req.json()
    btc_currentprice_rate = btc_currentprice_json["bpi"]["USD"]["rate_float"]
    btc_currentprice_string = locale.currency(btc_currentprice_rate, grouping=True)

    btc_lastclose_req = requests.get("https://api.coindesk.com/v1/bpi/historical/close.json?for=yesterday")
    btc_lastclose_json = btc_lastclose_req.json()
    btc_lastclose_rate = next(iter(btc_lastclose_json["bpi"].values()))
    btc_lastclose_string = locale.currency(btc_lastclose_rate, grouping=True)

    btc_diff = btc_currentprice_rate - btc_lastclose_rate
    btc_change_percentage = (100 * Decimal(btc_diff) / Decimal(btc_currentprice_rate))
    btc_change_percentage_string = "{}%".format(str(btc_change_percentage)[:6])

    btc_change_color = _get_change_color(btc_change_percentage)

    link = "https://www.google.com/finance/chart?q=CURRENCY:BTCUSD&tkr=1&p=1M&chst=vkc&chs=500x300"
    em = discord.Embed(color=btc_change_color)

    em.set_author(name="30 Day BTC Chart and Info", icon_url="https://bitcoin.org/img/icons/opengraph.png")
    em.set_image(url=link)
    em.set_footer(text="Chart supplied by Google Finance. Price info supplied by CoinDesk.")
    em.add_field(name="Current Price", value=btc_currentprice_string, inline=True)
    em.add_field(name="Last Close Price", value=btc_lastclose_string, inline=True)
    em.add_field(name="Change", value=btc_change_percentage_string, inline=True)

    await bot.send_message(contx.message.channel, embed=em)


@bot.command(pass_context=True)
async def render(contx, page_link: str):
    """Returns an image of the site."""
    if check_level(contx.message.author.id) in ["2", "8", "9"]:
        link = "http://http2pic.haschek.at/api.php?url={}".format(page_link)
        em = discord.Embed(title='Page render for {}, as requested by {}'.format(page_link, str(contx.message.author)))
        em.set_image(url=link)
        em.set_footer(text='Powered by http2pic.haschek.at. If you want a domain banned (nsfw site etc) please PM ao#5755.')
        await bot.send_message(contx.message.channel, embed=em)


@bot.command()
async def bigly(*, text_to_bigly: str):
    """Makes a piece of text as big as the hands of the god emperor."""
    letters = re.findall(r'[a-z0-9 ]', text_to_bigly.lower())
    biglytext = ''
    ri = 'regional_indicator_'
    for letter in letters:
        biglytext = biglytext + ":" + ri + str(letter) + ":\u200b"
    to_post = biglytext.replace(ri + "0", "zero").replace(ri + "1", "one").replace(
        ri + "2", "two").replace(ri + "3", "three").replace(ri + "4",
                                                            "four").replace(ri + "5", "five").replace(ri + "6",
                                                                                                      "six").replace(
        ri + "7", "seven").replace(ri + "8", "eight").replace(ri + "9", "nine") \
        .replace(":" + ri + " :", "\n").replace("\n :", "\n:").replace("\n :", "\n:")  # Worst fucking hack ever.
    await bot.say(to_post)


@bot.command(pass_context=True)
async def howmanymessages(contx):
    """Counts how many messages you sent in this channel in last 10000 messages."""
    tmp = await bot.send_message(contx.message.channel, 'Calculating messages...')
    counter = 0
    allcounter = 0
    async for hmlog in bot.logs_from(contx.message.channel, limit=10000):
        allcounter += 1
        if hmlog.author == contx.message.author:
            counter += 1
    percentage_of_messages = str(100 * (counter / allcounter))[:6]
    message_text = '{}: You have sent {} messages out of the last {} in this channel (%{}).' \
        .format(contx.message.author.mention, str(counter), str(allcounter), percentage_of_messages)
    await bot.edit_message(tmp, message_text)


@bot.command(pass_context=True)
async def log(contx, count: int):
    """Returns a file out of the last N messages submitted in this channel."""
    if check_level(contx.message.author.id) in ["9"]:
        log_text = "===start of log, exported by avebot===\n"
        async for mlog in bot.logs_from(contx.message.channel, limit=count):
            log_text += "[{}]<{}>{}\n".format(str(mlog.timestamp), str(mlog.author), mlog.clean_content)

        mlog_file_name = "files/{}.log".format(contx.message.channel.id)
        file = open(mlog_file_name, "w")
        file.write(log_text)
        file.write("===end of log, exported by avebot===")
        file.close()
        await bot.send_file(contx.message.channel, mlog_file_name,
                            content="{}: Here's the log file you requested.".format(contx.message.author.mention))


@bot.command()
async def similar(*, word: str):
    output = requests.get(
        "https://api.datamuse.com/words?ml={}".format(word.replace(" ", "+")))
    j = output.json()
    await bot.say(
        "**Similar Word:** `{}`\n(more on <http://www.onelook.com/thesaurus/?s={}&loc=cbsim>)".format(j[0]["word"],
                                                                                                      word.replace(" ",
                                                                                                                   "_")))


@bot.command()
async def typo(*, word: str):
    output = requests.get(
        "https://api.datamuse.com/words?sp={}".format(word.replace(" ", "+")))
    j = output.json()
    await bot.say("**Typo Fixed:** `{}`\n(more on <http://www.onelook.com/?w={}&ls=a>)".format(j[0]["word"],
                                                                                               word.replace(" ", "_")))


@bot.command()
async def soundslike(*, word: str):
    output = requests.get(
        "https://api.datamuse.com/words?sl={}".format(word.replace(" ", "+")))
    j = output.json()
    await bot.say("**Sounds like:** `{}`\n(more on <http://www.onelook.com/?w={}&ls=a>)".format(j[0]["word"],
                                                                                                word.replace(" ", "_")))


@bot.command()
async def rhyme(*, word: str):
    output = requests.get(
        "https://api.datamuse.com/words?rel_rhy={}".format(word.replace(" ", "+")))
    j = output.json()
    await bot.say(
        "**Rhymes with:** `{}`\n(more on <http://www.rhymezone.com/r/rhyme.cgi?Word={}&typeofrhyme=adv&org1=syl&org2=l&org3=y>)".format(
            j[0]["word"], word.replace(" ", "_")))


@bot.command(pass_context=True)
async def howold(contx):
    uri_base = config['howold']['uribase']
    subscription_key = config['howold']['subkey']
    urls = await get_image_links(contx, "howold")
    headers = {
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': subscription_key,
    }
    params = {
        'returnFaceId': 'false',
        'returnFaceLandmarks': 'false',
        'returnFaceAttributes': 'age,gender',
    }
    for url in urls:
        body = {'url': url}
        response = requests.request('POST', uri_base + '/face/v1.0/detect', json=body, data=None, headers=headers, params=params)
        logging.info("Howold response: {}".format(response.text))
        parsed = response.json()
        try:
            age = parsed[0]["faceAttributes"]["age"]
            gender = parsed[0]["faceAttributes"]["gender"]
            await bot.say("Age: **{}**\nGender: **{}**\n(it's hella inaccurate I know blame microsoft not me)".format(age, gender))
        except:
            logging.warning("howold failed: {}".format(traceback.format_exc()))
            await bot.say("No face detected.")


@bot.command(hidden=True)
async def stock():
    await bot.say("Please use >s")


@bot.command(pass_context=True)
async def s(contx, ticker: str):
    """Returns stock info about the given ticker."""
    symbols = requests.get(
        "https://api.robinhood.com/quotes/?symbols={}".format(ticker.upper()))
    if symbols.status_code != 200:
        error_text = (
            "Stock not found." if symbols.status_code == 400 else "HTTPError Code: {}".format(
                str(symbols.status_code)))
        em = discord.Embed(title="HTTP Error",
                           description=error_text,
                           colour=0xab000d)
        await bot.send_message(contx.message.channel, embed=em)
        return
    symbolsj = symbols.json()["results"][0]
    instrument = requests.get(symbolsj["instrument"])
    instrumentj = instrument.json()
    fundamentals = requests.get(
        "https://api.robinhood.com/fundamentals/{}/".format(ticker.upper()))
    fundamentalsj = fundamentals.json()

    current_price = Decimal(
        symbolsj["last_trade_price"] if symbolsj["last_extended_hours_trade_price"] is None else symbolsj[
            "last_extended_hours_trade_price"])
    diff = Decimal(Decimal(current_price) - Decimal(symbolsj["previous_close"]))
    percentage = str(100 * diff / current_price)[:6]

    if not percentage.startswith("-"):
        percentage = "+" + percentage

    current_price_string = locale.currency(current_price, grouping=True)
    diff_string = locale.currency(diff, grouping=True)
    bid_price_string = locale.currency(Decimal(symbolsj["bid_price"]), grouping=True)
    ask_price_string = locale.currency(Decimal(symbolsj["ask_price"]), grouping=True)
    tradeable_string = (":white_check_mark:" if instrumentj["tradeable"] else ":x:")

    update_timestamp = parser.parse(symbolsj["updated_at"])

    embed = discord.Embed(title="{}'s stocks info".format(symbolsj["symbol"]), color=get_change_color(symbolsj["symbol"]), timestamp=update_timestamp)

    embed.add_field(name="Name", value=instrumentj["name"])
    embed.add_field(name="Current Price", value=current_price_string)
    embed.add_field(name="Change from yesterday", value="{} ({}%)".format(diff_string, percentage))
    embed.add_field(name="Bid size", value="{} ({})".format(symbolsj["bid_size"], bid_price_string), inline=True)
    embed.add_field(name="Ask size", value="{} ({})".format(symbolsj["ask_size"], ask_price_string), inline=True)
    embed.add_field(name="Current Volume", value=fundamentalsj["volume"], inline=True)
    embed.add_field(name="Average Volume", value=fundamentalsj["average_volume"], inline=True)
    embed.add_field(name="Tradeable on Robinhood", value=tradeable_string, inline=True)
    embed.add_field(name="Country", value=":flag_{}:".format(instrumentj["country"].lower()), inline=True)

    await bot.send_message(contx.message.channel, embed=embed)


def unfurl_b(link):
    max_depth = int(config["advanced"]["unfurl-depth"])
    current_depth = 0
    prev_link = ""
    last_link = link
    try:
        while (prev_link != last_link) and (current_depth < max_depth):
            prev_link = last_link
            last_link = requests.head(prev_link, allow_redirects=True).url
            current_depth += 1
        return last_link
    except Exception:
        return prev_link

def slice_message(text, size):
    reply_list = []
    while len(text) > size:
        reply_list.append(text[:size])
        text = text[size:]
    reply_list.append(text)
    return reply_list


new_message = 0
new_command = 0

@bot.event
async def on_message(message):
    try:
        if message.author.bot:
            return

        global new_message
        global new_command
        new_message += 1
        if message.content.startswith(prefix):  # TODO: OK this is not reliable at all, find a better way to check this.
            new_command += 1

        if message.content.startswith(">") and message.content.split(" ")[0] in old_commands:
            new_command += 1
            await bot.send_message(message.channel, 'Heya, AveBot changed prefixes! Please send your message again but use `ab!` instead of `>`. This message will stop being sent in 2018-01-01.\nThanks for supporting AveBot!')

        if message.author.name == "GitHub" and message.channel.id == config['base']['main-channel'] and "new commit" in message.embeds[0]['title']:
            tmp = await bot.send_message(message.channel, 'Pulling...')
            git_pull()
            await bot.edit_message(tmp, "Pull complete, exiting!")
            await bot.logout()

        if check_level(str(message.author.id)) != "0":  # Banned users simply do not get a response
            if message.content.lower().startswith(config["advanced"]["voting-prefix"].lower()):
                await bot.add_reaction(message, config["advanced"]["voting-emoji-y"])
                await bot.add_reaction(message, config["advanced"]["voting-emoji-n"])

            if message.content.startswith('abddg!'):  # implementing this here because ext.commands handle the bang name ugh
                toduck = message.content.replace("+", "%2B").replace("abddg!", "!").replace(" ", "+")
                output = requests.get(
                    "https://api.duckduckgo.com/?q={}&format=json&pretty=0&no_redirect=1".format(toduck))
                j = output.json()
                resolvedto = j["Redirect"]
                if resolvedto:
                    await bot.send_message(message.channel, "Bang resolved to: {}".format(unfurl_b(resolvedto)))

            if message.content.startswith(prefix):
                if message.channel.is_private:
                    logging.info(
                        "{} ({}) said \"{}\" on PMs ({}).".format(message.author.name, message.author.id, message.content, message.channel.id))
                else:
                    logging.info("{} ({}) said \"{}\" on \"{}\" ({}) at \"{}\" ({})."
                           .format(message.author.name, message.author.id, message.content, message.channel.name, message.channel.id, message.server.name, message.server.id))
            if message.content.lower() == "{}help".format(prefix):
                help_text = open("help.md", "r").read()
                em = discord.Embed(title="Welcome to AveBot Rewrite",
                                   description=help_text,
                                   colour=0xDEADBF)
                await bot.send_message(message.channel, embed=em)
            else:
                await bot.process_commands(message)
    except Exception:
        await catch_error(traceback.format_exc())

async def update_stats():
    await bot.wait_until_ready()
    while not bot.is_closed:
        if config['stats']['url'] and config['stats']['key']:
            server_count = len(bot.servers)
            user_count = 0
            for server in bot.servers:
                user_count += server.member_count

            global new_message
            global new_command
            url_to_call = "{}?key={}&user_count={}&server_count={}&new_total_messages={}&new_addressed_messages={}".format(config['stats']['url'], config['stats']['key'], user_count, server_count, new_message, new_command)
            new_message = 0
            new_command = 0
            requests.get(url_to_call)
        await asyncio.sleep(3)

logging.info("AveBot started. Git hash: " + get_git_revision_short_hash())
if not os.path.isdir("files"):
    os.makedirs("files")

bot.loop.create_task(update_stats())
bot.run(config['base']['token'])
