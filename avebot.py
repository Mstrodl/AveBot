import asyncio
import datetime
import os
import re
import socket
import subprocess
import time
import traceback

from pathlib import Path
from decimal import *

import random
import requests

import discord
from discord.ext import commands

import configparser

# TODO: COGS https://gist.github.com/leovoel/46cd89ed6a8f41fd09c5
# TODO: Take over >help (on on_message, handle it before handling command)
# TODO: >get >dget size and timeouts

config_file_name = "avebot.ini"
log_file_name = "avebot.log"


def avelog(content):
    try:
        st = str(datetime.datetime.now()).split('.')[0]
        text = '[' + st + ']: ' + content
        print(text)
        with open(log_file_name, "a") as myfile:
            myfile.write(text + "\n")
        return
    except Exception:
        exit()

config = configparser.ConfigParser()
if not Path(config_file_name).is_file():
    avelog("No config file ({}) found, please create one from avebot.ini.example file.".format(config_file_name))
    exit()

prefix = config['base']['prefix']


def get_git_commit_text():
    return str(subprocess.check_output(['git', 'log', '-1', '--pretty=%B']).strip())[2:-1]


def get_git_revision_short_hash():
    return str(subprocess.check_output(['git', 'log', '-1', '--pretty=%h']).strip())[2:-1]


description = 'AveBot Rewrite\nGit Hash: {}\nLast Commit: {}' \
    .format(get_git_revision_short_hash(), get_git_commit_text())
bot = commands.Bot(command_prefix=prefix, description=description)


def check_level(discord_id: str):
    #  = banned, 1 = regular user, 2 = privileged, 8 = mod, 9 = owner
    perm = config['permissions'][discord_id]
    if config['permissions'][discord_id]:
        return config['permissions'][discord_id]
    else:
        return "1"


def download_file(url,
                  local_filename):  # This function is based on https://stackoverflow.com/a/16696317/3286892 by Poman Podlinov (https://stackoverflow.com/users/427457/roman-podlinov), modified by Avery (https://github.com/ardaozkal), licensed CC-BY-SA 3.0
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                # f.flush() commented by recommendation from J.F.Sebastian


@bot.event
async def on_ready():
    st = str(datetime.datetime.now()).split('.')[0]
    avelog('Logged in as')
    avelog(bot.user.name)
    avelog(bot.user.id)
    avelog('------')
    try:
        asyncio.sleep(3)
        await bot.change_presence(game=discord.Game(name='run >help'))
        em = discord.Embed(title='AveBot initialized!',
                           description='Git hash: `{}`\nHostname: `{}`\nLocal Time: `{}`\nLogs are below.'
                           .format(get_git_revision_short_hash(), socket.gethostname(), st),
                           colour=0xDEADBF)
        em.set_author(name='AveBot', icon_url='https://s.ave.zone/c7d.png')
        await bot.send_message(discord.Object(id=config['base']['main-channel']), embed=em)
        await bot.send_file(discord.Object(id=config['base']['main-channel']), log_file_name)
        open(log_file_name, 'w').close()  # Clears log
    except Exception:
        avelog(traceback.format_exc())
        bot.close()
        exit()


@bot.command()
async def roll(dice: str):
    """Rolls a dice in NdN format."""
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await bot.say('Format has to be in NdN!')
        return

    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    await bot.say(result)


@bot.command()
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


@bot.command(pass_context=True)
async def whoami(contx):
    """Returns your information."""
    await bot.say("You are {} (`{}`) and your permission level is {} (0 = banned, 1 = normal, 2 = authenticated, 8 = mod, 9 = owner).".format(
        contx.message.author.name, contx.message.author.id, check_level(contx.message.author.id)))


@bot.command()
async def unfurl(link: str):
    """Finds where a URL redirects to."""
    resolved = unfurl_b(link)
    await bot.say("<{}> Unfurls to <{}>".format(link, resolved))


@bot.command()
async def addavebot():
    """Gives a link that can be used to add AveBot."""
    inviteurl = discord.utils.oauth_url(bot.user.id)
    await bot.say("You can use <{}> to add AveBot to your server.".format(inviteurl))


@bot.command(pass_context=True)
async def contact(contx, *, contact_text: str):
    """Contacts developers with a message."""
    em = discord.Embed(title='Contact received!',
                       description='**Message by:** {} ({})\n on {} at {}\n**Message content:** {}'.format(str(
                           contx.message.author), contx.message.author.id, contx.message.channel.name,
                           contx.message.server.name, contact_text),
                       colour=0xDEADBF)
    em.set_author(name='AveBot', icon_url='https://s.ave.zone/c7d.png')
    await bot.send_message(discord.Object(id=config['base']['support-channel']), embed=em)

    em = discord.Embed(title='Contact sent!',
                       description='Your message has been delivered to the developers.',
                       colour=0xDEADBF)
    em.set_author(name='AveBot', icon_url='https://s.ave.zone/c7d.png')
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
    message_text = ':ping_pong: Ping is {}ms'.format(ping_ms[:6])
    await bot.edit_message(tmp, message_text)


@bot.command(name='exit', pass_context=True)
async def _exit(contx):
    """Quits the bot (Owner only)."""
    if check_level(contx.message.author.id) == "9":
        await bot.say("Exiting AveBot, goodbye!")
        await bot.logout()


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
        if file_size < 1024*1024*7:  # Limit of discord is 7MiB
            await bot.send_file(contx.message.channel, filename,
                                content="{}: Here's the file you requested.".format(contx.message.author.mention))
        else:
            bot.say("{}: File is too big for discord (Limit is 7MiB, file is {}MiB).".format(contx.message.author.mention, (file_size/(1024*1024))))
        os.remove(filename)  # Remove file when we're done with it (kinda risky TBH )


@bot.command(pass_context=True)
async def dget(contx, link: str):
    """Directly gets (doesn't care about name) a file from the internet (Privileged/Mod/Admin only)."""
    if check_level(contx.message.author.id) in ["2", "8", "9"]:
        filename = "files/requestedfile"
        download_file(link, filename)
        file_size = Path(filename).stat().st_size
        if file_size < 1024*1024*7:  # Limit of discord is 7MiB
            await bot.send_file(contx.message.channel, filename,
                                content="{}: Here's the file you requested.".format(contx.message.author.mention))
        else:
            bot.say("{}: File is too big for discord (Limit is 7MiB, file is {}MiB).".format(contx.message.author.mention, (file_size/(1024*1024))))
        os.remove(filename)  # Remove file when we're done with it (kinda risky TBH )


@bot.command()
async def xkcd(xkcdcount: int):
    """Returns info about the specified xkcd comic."""
    output = requests.get("https://xkcd.com/{}/info.0.json".format(str(xkcdcount)))
    j = output.json()
    resolvedto = j["img"]
    if resolvedto:
        messagecont = "**XKCD {}:** `{}`, published on {}-{}-{} (DMY)\n**Image:** {}\n**Alt text:** `{}`\n" \
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
        messagecont = "**XKCD {}:** `{}`, published on {}-{}-{} (DMY)\n**Image:** {}\n**Alt text:** `{}`\n" \
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
    to_post = "Copypasta ready: `{}`".format(random.choice(copypasta_list).format(ticker))
    await bot.say(to_post)


@bot.command(hidden=True)
async def stockchart():
    await bot.say("Please use >c")


@bot.command(hidden=True)
async def chart():
    await bot.say("Please use >c")


@bot.command(pass_context=True)
async def c(contx, ticker: str):
    """Returns stock chart of the given ticker."""
    link = "http://finviz.com/chart.ashx?t={}&ty=c&ta=1&p=d&s=l".format(ticker.upper())
    filename = "files/{}.png".format(ticker.upper())
    download_file(link, filename)
    await bot.send_file(contx.message.channel, filename,
                        content="Here's the charts for {0}. See <http://finviz.com/quote.ashx?t={0}> for more info.".format(
                            ticker.upper()))


@bot.command()
async def bigly(*, text_to_bigly: str):
    """Makes a piece of text as big as the hands of the god emperor."""
    letters = re.findall(r'[a-z0-9 ]', text_to_bigly.lower())
    biglytext = ''
    ri = 'regional_indicator_'
    for letter in letters:
        biglytext = biglytext + ":" + ri + str(letter) + ": "
    to_post = biglytext.replace(ri + "0", "zero").replace(ri + "1", "one").replace(
        ri + "2", "two").replace(ri + "3", "three").replace(ri + "4",
                                                            "four").replace(ri + "5", "five").replace(ri + "6",
                                                                                                      "six").replace(
        ri + "7", "seven").replace(ri + "8", "eight").replace(ri + "9", "nine") \
        .replace(":" + ri + " :", "\n").replace("\n :", "\n:")  # Worst fucking hack ever.
    await bot.say(to_post)


@bot.command(pass_context=True)
async def howmanymessages(contx):
    """Counts how many messages you sent in this channel in last 10000 messages."""
    tmp = await bot.send_message(contx.message.channel, 'Calculating messages...')
    counter = 0
    allcounter = 0
    async for log in bot.logs_from(contx.message.channel, limit=10000):
        allcounter += 1
        if log.author == contx.message.author:
            counter += 1
    percentage_of_messages = str(100 * (counter / allcounter))[:6]
    message_text = '{}: You have sent {} messages out of the last {} in this channel (%{}).' \
        .format(contx.message.author.mention, str(counter), str(allcounter), percentage_of_messages)
    await bot.edit_message(tmp, message_text)


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
        em.set_author(name='AveBot', icon_url='https://s.ave.zone/c7d.png')
        await bot.send_message(contx.message.channel, embed=em)
        return
    symbolsj = symbols.json()["results"][0]
    instrument = requests.get(symbolsj["instrument"])
    instrumentj = instrument.json()
    fundamentals = requests.get(
        "https://api.robinhood.com/fundamentals/{}/".format(ticker.upper()))
    fundamentalsj = fundamentals.json()

    current_price = (
        symbolsj["last_trade_price"] if symbolsj["last_extended_hours_trade_price"] is None else symbolsj[
            "last_extended_hours_trade_price"])
    diff = str(Decimal(current_price) - Decimal(symbolsj["previous_close"]))
    if not diff.startswith("-"):
        diff = "+" + diff
    percentage = str(100 * Decimal(diff) / Decimal(current_price))[:6]

    if not percentage.startswith("-"):
        percentage = "+" + percentage

    reply_text = "Name: **{}**\nCurrent Price: **{} USD**\nChange from yesterday: **{} USD**, (**{}%**)\n" \
                 "Bid size: **{} ({} USD)**, Ask size: **{} ({} USD)**\n" \
                 "Current Volume: **{}**, Average Volume: **{}** \n" \
                 "Tradeable (on robinhood): {}, :flag_{}:".format(instrumentj["name"], current_price, diff,
                                                                  percentage, str(symbolsj["bid_size"]),
                                                                  symbolsj["bid_price"], str(symbolsj["ask_size"]),
                                                                  symbolsj["ask_price"], fundamentalsj["volume"],
                                                                  fundamentalsj["average_volume"], (
                                                                      ":white_check_mark:" if instrumentj[
                                                                          "tradeable"] else ":x:"),
                                                                  instrumentj["country"].lower())

    em = discord.Embed(title="{}'s stocks info as of {}".format(symbolsj["symbol"], symbolsj["updated_at"]),
                       description=reply_text, colour=(0xab000d if diff.startswith("-") else 0x32cb00))
    em.set_author(name='AveBot - Stocks', icon_url='https://s.ave.zone/c7d.png')
    await bot.send_message(contx.message.channel, embed=em)


def unfurl_b(link):
    max_depth = int(config["advanced"]["unfurl-depth"])
    current_depth = 0
    prev_link = ""
    last_link = link
    while (prev_link != last_link) and (current_depth < max_depth):
        prev_link = last_link
        last_link = requests.head(prev_link, allow_redirects=True).url
        current_depth += 1
    return last_link


# TODO: respect  and voting-prefix

@bot.event
async def on_message(message):
    try:
        if config["advanced"]["add-reactions"] == True:
            if message.content.lower().startswith('ok'):
                await bot.add_reaction(message, "🆗")  # OK emoji
            elif message.content.lower().startswith('hot'):
                await bot.add_reaction(message, "🔥")  # fire emoji
            elif message.content.lower().startswith('cool'):
                await bot.add_reaction(message, "❄")  # snowflake emoji
            if "🤔" in message.content:  # thinking emoji
                await bot.add_reaction(message, "🤔")

        if message.content.lower().startswith(config["advanced"]["voting-prefix"].lower()):
            await bot.add_reaction(message, config["advanced"]["voting-emoji-y"])
            await bot.add_reaction(message, config["advanced"]["voting-emoji-n"])


        if check_level(str(message.author.id)) != "0":  # Banned users simply do not get a response
            if message.content.startswith('>!'):  # implementing this here because ext.commands handle the bang name ugh
                toduck = message.content.replace(">!", "!").replace(" ", "+")
                output = requests.get(
                    "https://api.duckduckgo.com/?q={}&format=json&pretty=0&no_redirect=1".format(toduck))
                j = output.json()
                resolvedto = j["Redirect"]
                if resolvedto:
                    await bot.send_message(message.channel, "Bang resolved to: {}".format(unfurl_b(resolvedto)))

            if message.channel.is_private:
                avelog("{} ({}) said \"{}\" on PMs.".format(message.author.name, message.author.id, message.content))
            else:
                avelog("{} ({}) said \"{}\" on \"{}\" at \"{}\"."
                       .format(message.author.name, message.author.id, message.content, message.channel.name,
                               message.server.name))

            await bot.process_commands(message)
    except Exception:
        avelog(traceback.format_exc())
        em = discord.Embed(title="An error happened", description="It was logged and will be reviewed by developers.",
                           colour=0xcc0000)
        em.set_author(name='AveBot', icon_url='https://s.ave.zone/c7d.png')
        await bot.send_message(message.channel, embed=em)


avelog("AveBot started. Git hash: " + get_git_revision_short_hash())
if not os.path.isdir("files"):
    os.makedirs("files")

bot.run(config['base']['token'])