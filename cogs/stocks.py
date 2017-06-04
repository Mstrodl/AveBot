import discord
import requests
from discord.ext import commands
from decimal import *

class Stocks():
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def stock(self):
        await self.bot.say("Please use >s")

    @commands.command(pass_context=True)
    async def s(self, contx, ticker: str):
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
            await self.bot.send_message(contx.message.channel, embed=em)
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
        await self.bot.send_message(contx.message.channel, embed=em)


def setup(bot):
    bot.add_cog(Stocks(bot))