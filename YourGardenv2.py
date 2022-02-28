# Your Garden v2, a discord bot for mindfulness (maybe)
# but this time with actual command structure

# openers: -----------------------------------------------------------------------------------------------------------
import datetime
from datetime import datetime as dt
# import time
import os
from datetime import timedelta
import discord
# import numpy as np
import math as m
import pandas as pd
# from datetime import datetime as dt
# import json
import random
from discord.ext import tasks, commands

# from discord.utils import get

# discord.py initializer stuff ------------------------------------------------------------------
toke = os.getenv('token')
# client = discord.Client()  // deprecated use
bot = commands.Bot(command_prefix='g$')

# useful variables ------------------------------------------------------------------------------
# reference database
database = pd.read_csv('v2db.csv')
# note = plot1status at i=13

# allows trees to grow half as fast
growmod = 0

# notable deltas
mindelta = timedelta(hours=3)  # min time of watering
maxdelta = timedelta(days=2)  # max time of watering (death timer)

# emoji dicts. string dict deprecated.
flowdict = {}
with open('v2flowdict.txt') as file:
    for line in file:
        (key, value) = line.split()
        flowdict[int(key)] = value
# with open('flowdictstring.txt') as file:
#     stringdata = file.read()
# flowdictstring = json.loads(stringdata)
spdict = {'Basic Seeds': 1, 'Flower Seeds': 3, 'Tree Seeds': 3, 'Ultra Seeds': 10}

coldict = {1: 21, 2: 15, 3: 8, 4: 20, 5: 19, 6: 18, 7: 17, 8: 14, 9: 13, 10: 12, 11: 11, 12: 7, 13: 6, 14: 5, 15: 4}
colrev = {v: k for k, v in coldict.items()}


# common use functions ------------------------------------------------------------------------------------------------

# time conversion functions: -------------------------
def datetime_to_float(d):
    return d.timestamp()


def float_to_datetime(fl):
    return datetime.datetime.fromtimestamp(fl)


# write to file --------------------------------------
def hardwrite():
    global database
    database = database.fillna(0)
    database.to_csv('v2db.csv', index=False)
    database = pd.read_csv('v2db.csv')


# sv related functions ------------------------------
# get type from sv. Returns 1, 2, or 3
def svtype(sv):
    if sv % 2 == 0:
        typer = 2
    elif sv % 3 == 0:
        typer = 3
    else:
        typer = 1
    return typer


# get growth value of sv. returns 1, 2, 3, 4
def svgrowth(sv):
    g = 0
    svcheck = sv
    while svcheck % 7 == 0:
        g += 1
        svcheck = svcheck / 7
    return g


# get table ID of sv. returns 1, 2, 3, 4, 5
def svtableid(sv):
    p = 0
    svcheck = sv
    while svcheck % 5 == 0:
        p += 1
        svcheck = svcheck / 5
    return p


# convert stored value of plot to dict value for emoji conversion
def svtodict(sv):
    t = svtype(sv)
    g = svgrowth(sv)
    p = svtableid(sv)
    dv = 0
    if t == 2:
        if g == 1:
            dv = 2
        elif g == 2:
            dv = 3
        elif g == 4:
            dv = 9
        else:
            if p == 1:
                dv = 4
            elif p == 2:
                dv = 5
            elif p == 3:
                dv = 6
            elif p == 4:
                dv = 7
            elif p == 5:
                dv = 8
    elif t == 3:
        if g == 1:
            dv = 2
        elif g == 2:
            dv = 10
        elif g == 4:
            dv = 16
        else:
            if p == 1:
                dv = 11
            elif p == 2:
                dv = 12
            elif p == 3:
                dv = 13
            elif p == 4:
                dv = 14
            elif p == 5:
                dv = 15
    else:
        if g == 1:
            dv = 2
        elif g == 2:
            r = random.randint(1, 2)
            if r % 2 == 0:
                r = 3
            else:
                r = 10
            dv = r
        elif g == 4:
            dv = 22
        else:
            if p == 1:
                dv = 17
            elif p == 2:
                dv = 18
            elif p == 3:
                dv = 19
            elif p == 4:
                dv = 20
            elif p == 5:
                dv = 21
    return dv


# note: this only works with v2flowdict.txt


# turn a dict value to an emoji  \\ unused due to next fcn
def dicttoemoji(di):
    emoji = flowdict.get(di)
    return emoji


# turn sv directly into an emoji
def svtoemoji(sv):
    dic = svtodict(sv)
    emoji = flowdict.get(dic)
    return emoji


# sv from plant type, id, and growth stage
def sval(pt, pnum, gst):
    ptloc = 5 ** pnum
    gstloc = 7 ** gst
    sv = ptloc * pt * gstloc
    return sv


# discord functions: -------------------------------
# role checker. takes in command context and a string, outputs a boolean (T if user has role, else F)
def hasrolectx(ctx, role):
    search = str(role)
    role = discord.utils.find(lambda r: r.name == search, ctx.message.guild.roles)
    authroles = ctx.message.author.roles
    if role in authroles:
        res = True
        return res
    else:
        res = False
        return res


# play check, pass in uid, get out a bool
def playcheck(uid):
    users = database['User']
    if id not in users.values:
        b = True
    else:
        b = False
    return b


# db functions -------------------------------------
# based on command user, create a df to concat onto the main
def inituser(ctx):
    user = ctx.message.author.id
    inituserrow = pd.DataFrame(  # starter garden dataframe
        {"User": user,
         "Currency": [0],
         "Plot Size": ["s"],
         "Has Watered": False,
         "Last Water": [0],
         "Basic Seeds": [0],
         "Flower Seeds": [0],
         "Tree Seeds": [0],
         "Ultra Seeds": [0],
         "Luck": [0.1],
         "Collection": ["1000000000000000"],
         "Sell Modifier": [1.0],
         "Passive Modifier": [1.0],
         "plot1status": [1]},
        index=[0]
    )
    return inituserrow


# join a new user df into the main
def jnu(b):
    global database
    database = pd.concat([database, b], axis=0, ignore_index=True, verify_integrity=True)


# returns the user's index as int, used for .iat
def useridx(ctx):
    global database
    authorid = ctx.message.author.id
    idx = database.loc[database['User'] == authorid].index[0]
    return idx


# get a df based on a user's plots, returns a df with one row
def userplots(ctx):
    global database
    idx = useridx(ctx)
    userrow = database.iloc[[idx]]
    plots = userrow.loc[:, 'plot1status':'plot25status']
    return plots


# for iterating - outputs a list of plot values
def userplotlist(ctx):
    global database
    plots = userplots(ctx)
    plotlist = plots.values.flatten().tolist()
    return plotlist


# other functions ------------------------------------------
# generate plots
def plotnamelist():
    plottitles = []
    for i in range(1, 25):
        app = "plot" + str(i) + "status"
        plottitles.append(app)
    return plottitles


# grow a plant, based on its current growth, type, and watering
# in: sv int, out: new sv int to write
def grow(a):
    g = svgrowth(a)
    t = svtype(a)
    newa = a
    if g < 3:  # is not adult?
        if t == 2:  # is flower?
            newa = newa * 7  # grow flower up
        elif t == 3 and growmod % 2 == 0:  # is tree and tree growth tick?
            newa = newa * 7  # grow tree
        else:
            newa = a  # nothing new
    return newa


# cause plant to enter growth 4 or reset
def die(a):
    g = svgrowth(a)
    newa = a
    if g == 3:  # adult to wither
        newa = newa * 7
    elif g == 4:  # wither to arable
        newa = 1
    else:  # no change
        newa = a
    return newa


# input userid, get string of garden
def getgarden(tid):
    authorid = tid
    idx = database.loc[database['User'] == authorid].index[0]
    userrow = database.iloc[[idx]]
    plots = userrow.loc[:, 'plot1status':'plot25status']
    plotlist = plots.values.flatten().tolist()
    pl1 = []
    for b in range(len(plotlist)):
        plot = plotlist[b]
        if plot != 0 and plot != 1:
            a = svtodict(plot)
            pl1.append(a)
        else:
            a = plot
            pl1.append(a)
    pl = [flowdict.get(plot, plot) for plot in pl1]
    pl.insert(0, "bump")
    printer = pl[1] + pl[2] + pl[9] + pl[10] + pl[25] + "\n" + pl[4] + pl[3] + pl[8] + pl[11] + pl[24] + "\n" + pl[5] + \
              pl[6] + pl[7] + pl[12] + pl[23] + "\n" + pl[16] + pl[15] + pl[14] + pl[13] + pl[22] + "\n" + pl[17] + pl[
                  18] + pl[19] + pl[20] + pl[21]
    return printer


# buy a thing
def buy(ctx, seed, num):
    clean = seed.lower()
    num = int(num)
    authorid = ctx.message.author.id
    idx = database.loc[database['User'] == authorid].index[0]
    userrow = database.iloc[[idx]]
    cur = userrow.at[idx, 'Currency']
    print(cur)
    print(type(cur))
    seedlist = []  # get current prices
    pricelist = []
    for s, p in spdict.items():
        seedlist.append(str(s))
        pricelist.append(str(p))
    bmod = int(pricelist[0])  # use current prices, in general
    fmod = int(pricelist[1])
    tmod = int(pricelist[2])
    umod = int(pricelist[3])
    rs = ""
    if clean == 'basic seed' or clean == 'basic seeds':
        if cur > (num * bmod):
            database.at[idx, 'Currency'] = cur - (num * bmod)
            database.at[idx, 'Basic Seeds'] += num
            rs = "Bought " + str(num) + " basic seeds."
        else:
            rs = "Not enough sanddollars... oof."
    elif clean == 'flower seed' or clean == 'flower seeds':
        if cur > (num * fmod):
            database.at[idx, 'Currency'] = cur - (num * fmod)
            database.at[idx, 'Flower Seeds'] += num
            rs = "Bought " + str(num) + " flower seeds."
        else:
            rs = "Not enough sanddollars."
    elif clean == 'tree seed' or clean == 'tree seeds':
        if cur > (num * tmod):
            database.at[idx, 'Currency'] = cur - (num * tmod)
            database.at[idx, 'Tree Seeds'] += num
            rs = "Bought " + str(num) + " tree seeds."
        else:
            rs = "Not enough sanddollars."
    elif clean == 'ultra seed' or clean == 'ultra seeds':
        if cur > (num * umod):
            database.at[idx, 'Currency'] = cur - (num * umod)
            database.at[idx, 'Ultra Seeds'] += num
            rs = "Bought " + str(num) + " ultra seeds."
        else:
            rs = "Not enough sanddollars."
    hardwrite()
    return rs


# upgrade function
sizedict = {'s': 1, 'm': 2, 'l': 3, 'xl': 4, 'xxl': 5}
rvdict = {1: 's', 2: 'm', 3: 'l', 4: 'xl', 5: 'xxl'}


def upg(ctx):
    idx = useridx(ctx)
    psize = database.at[idx, 'Plot Size']
    pn = sizedict.get(psize)
    pmax = (pn + 1) ** 2
    pmin = pn ** 2
    npn = pn + 1
    np = rvdict.get(npn)
    cost = (2 ** (pn + 2)) - 1
    database.at[idx, 'Plot Size'] = np
    database.at[idx, 'Currency'] = database.at[idx, 'Currency'] - cost
    for i in range(pmin, (pmax + 1)):
        stat = 'plot' + str(i) + 'status'
        if database.at[idx, stat] == 0:
            database.at[idx, stat] = 1
    hardwrite()


# fcn to get a plant from a seed table, returns an int ready to write to table
def seedpl(ty, luck):
    st = pd.read_csv('seedtables.csv')
    rr = random.randint(1, 100)
    bump = m.floor((luck * 2.5))
    tl = (((rr + bump) // 5) * 5) + 5
    if tl > 100:
        tl = 100
    res = st.at[ty, str(tl)]
    plant = 7 * int(res)
    return plant


# take in string, return list of characters
def unstring(cst):
    s = str(cst)
    lt = []
    for i in s:
        lt.append(i)
    return lt


def restring(lst):
    st = ""
    for el in lst:
        st += str(el)
    return st


# collection to emoji
def colemoji(lt):
    checker = 0
    out = ""
    for el in lt:
        if el == '1' and checker != 0:
            disp = coldict.get(checker)
            add = str(dicttoemoji(disp) + " ")
            out += add
        else:
            add = str(dicttoemoji(0) + " ")
            out += add
        checker += 1
    return out

# bot start --------------------------------------
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to discord!')
    await bot.change_presence(activity=discord.Game(name="Grief my status with g$grief <message>"))


# commands -----------------------------------------------------------------------------------------------------------
# test command
@bot.command(pass_context=True)
async def test(ctx):
    await ctx.send("Worked!")
    print("got here")


@bot.command()
async def grief(ctx, *, arg):
    status = str(arg)
    authid = ctx.message.author.id
    await ctx.send(f"Great idea, <@{authid}>!")
    await bot.change_presence(activity=discord.Game(name=status))


# dict tester
@bot.command()
async def calldict(ctx, arg: int):
    emoji = svtoemoji(arg)
    stringres = "This is " + str(emoji)
    await ctx.send(stringres)


# ctx tester
@bot.command(pass_context=True)
async def getcon(ctx):
    print(ctx)
    # role = discord.utils.find(lambda r: r.name == 'bottrusted', ctx.message.guild.roles)
    # authroles = ctx.message.author.roles
    #  print(db)


# new user join
@bot.command()
async def join(ctx):
    global database
    users = database['User']
    if ctx.message.author.id not in users.values:
        u = inituser(ctx)
        jnu(u)
        id1 = ctx.message.author.id
        idx = database[database['User'] == id1].index[0]
        await ctx.send("You've been added to the game, with index " + str(idx) + ". ")
        hardwrite()
    else:
        await ctx.send("You are already playing!")


# check self info
@bot.command()
async def me(ctx):
    if playcheck(ctx.message.author.id):
        idx = useridx(ctx)
        userrow = database.iloc[[idx]]
        final = []  # list to append to
        sep = ' \n '  # separator for later
        dn = ctx.message.author.display_name
        final.append(str(dn) + "'s garden: :blossom:")
        curr = str(userrow.at[idx, 'Currency'])
        final.append(":moneybag: You have " + curr + " sanddollars.")
        haswater = userrow.at[idx, 'Has Watered']
        if haswater:
            final.append(":shower: You've watered this cycle.")
        else:
            final.append(":shower: You haven't watered yet!")
        inv = ":seedling: You have " + str(userrow.at[idx, 'Basic Seeds']) + " basic seeds, " + str(
            userrow.at[idx, 'Flower Seeds']) + " flower seeds, " + str(
            userrow.at[idx, 'Tree Seeds']) + " tree seeds, and " + str(userrow.at[idx, 'Ultra Seeds']) + " ultra seeds."
        final.append(inv)
        sellmod = str(userrow.at[idx, 'Sell Modifier'])
        final.append(":arrow_double_up: Your sell modifier is " + sellmod)
        passmod = str(userrow.at[idx, 'Passive Modifier'])
        final.append(":arrow_up: Your passive modifier is " + passmod)
        luck = userrow.at[idx, 'Luck']
        luckstr = ""
        if luck < 0.5:
            luckstr = "You have bad luck. :confused:"
        elif 0.5 <= luck < 1:
            luckstr = "You have okay luck. :neutral_face:"
        elif 1 <= luck < 1.5:
            luckstr = "You have good luck. :slight_smile:"
        elif 1.5 <= luck < 2:
            luckstr = "You have great luck! :exploding_head:"
        elif luck == 2:
            luckstr = "You have amazing luck! :four_leaf_clover:"
        final.append(luckstr)
        size = ""
        if userrow.at[idx, 'Plot Size'] == 's':  # size to plaintext conversion
            size = "Your plot is small. :pinching_hand:"
        elif userrow.at[idx, 'Plot Size'] == 'm':
            size = "Your plot is medium. :+1:"
        elif userrow.at[idx, 'Plot Size'] == 'l':
            size = "Your plot is large. :partying_face:"
        elif userrow.at[idx, 'Plot Size'] == 'xl':
            size = "Your plot is extra large. :smirk:"
        elif userrow.at[idx, 'Plot Size'] == 'xxl':
            size = "Your plot is max size! :cowboy:"
        final.append(size)
        collection = userrow.at[idx, 'Collection']
        disp = unstring(collection)
        coldispemoji = colemoji(disp)
        final.append("Your collection: ")
        final.append(coldispemoji)
        mestring = sep.join(final)
        await ctx.send(mestring)
    else:
        await ctx.send("You aren't playing! Do g$join to sign up.")


# show own garden
@bot.command(aliases=['mg'])
async def mygarden(ctx):
    if playcheck(ctx.message.author.id):
        printer = getgarden(ctx.message.author.id)
        await ctx.send(printer)
    else:
        await ctx.send("You aren't playing! Do g$join to sign up.")


# show other's garden
@bot.command()
async def garden(ctx, *, member: discord.Member):
    if playcheck(member.id):
        printer1 = getgarden(member.id)
        printer2 = "{0}'s garden".format(member)
        modp = printer2 + "\n" + printer1
        await ctx.send(modp)
    else:
        await ctx.send("That person isn't playing.")


# get seed prices
@bot.command(aliases=['sp'])
async def seedprices(ctx):
    seedlist = []
    pricelist = []
    for s, p in spdict.items():
        seedlist.append(str(s))
        pricelist.append(str(p))
    pricead = ""
    for i in range(len(seedlist)):
        new = seedlist[i] + " price: " + pricelist[i] + "\n"
        pricead += new
    await ctx.send(pricead)


# buy command
@bot.command()
async def buyseeds(ctx, p1, p2, q):
    if playcheck(ctx.message.author.id):
        seed = str(p1) + " " + str(p2)
        print(seed)
        rs = buy(ctx, seed, q)
        rstr = ""
        await ctx.send(rs)
    else:
        await ctx.send("You aren't playing! Do g$join to sign up.")


# plant command
@bot.command(name='plant')
async def plant(ctx, ty1, plot: int):
    try:
        ty = int(ty1)
    except:
        await ctx.send(
            "Your g$plant didn't work!.\nformat: g$plant <type> <plot#>\nMake sure to use 0, 1, 2, or 3 as your type (basic, flower, tree, and ultra respesctively)")
        print("broke")
        return
    if playcheck(ctx.message.author.id):
        idx = useridx(ctx)
        ty = int(ty1)
        plotcol = "plot" + str(plot) + "status"
        userrow = database.iloc[[idx]]
        cs = database.at[idx, plotcol]
        sc = 0
        if ty == 0:
            sc = int(userrow.at[idx, 'Basic Seeds'])
        elif ty == 1:
            sc = int(userrow.at[idx, 'Flower Seeds'])
        elif ty == 2:
            sc = int(userrow.at[idx, 'Tree Seeds'])
        elif ty == 3:
            sc = int(userrow.at[idx, 'Ultra Seeds'])
        lck = float(userrow.at[idx, 'Luck'])
        if sc > 0 and cs == 1:
            rt = seedpl(ty, lck)
            database.at[idx, plotcol] = rt
            await ctx.send("Planted in plot " + str(plot) + "! ")
            hardwrite()
        elif cs == 0:
            await ctx.send("You haven't unlocked that plot!")
        elif sc == 0:
            await ctx.send("You don't have any seeds of that type!")
        else:
            await ctx.send("Something else went wrong...")
            print(cs)
            print(sc)
    else:
        await ctx.send("You aren't playing! Do g$join to sign up.")


# map out the plots
@bot.command()
async def plotmap(ctx):
    pl = []
    for i in range(25):
        if i < 10:
            pl.append("  " + str(i + 1) + " ")
        else:
            pl.append(" " + str(i + 1) + " ")
    pl.insert(0, 0)
    print(pl)
    printer = pl[1] + "  " + pl[2] + pl[9] + pl[10] + pl[25] + "\n" + pl[4] + pl[3] + pl[8] + pl[11] + pl[24] + "\n" + \
              pl[5] + \
              pl[6] + pl[7] + pl[12] + pl[23] + "\n" + pl[16] + pl[15] + pl[14] + pl[13] + pl[22] + "\n" + pl[17] + pl[
                  18] + pl[19] + pl[20] + pl[21]
    await ctx.send(printer)


# harvester
@bot.command()
async def harvest(ctx, plot: int):
    idx = useridx(ctx)
    plotcol = "plot" + str(plot) + "status"
    userrow = database.iloc[[idx]]
    sv = userrow.at[idx, plotcol]
    growth = svgrowth(sv)
    sm = userrow.at[idx, 'Sell Modifier']
    pm = userrow.at[idx, 'Passive Modifier']
    lm = userrow.at[idx, 'Luck']
    if playcheck(ctx.message.author.id):
        if growth == 4:
            database.at[idx, plotcol] = 1
            await ctx.send("It was dead. What a pity...\nYou've been given 2 sanddollars, out of pity.")
            database.at[idx, 'Currency'] += 2
            hardwrite()
        elif growth == 3:
            t = svtype(sv)
            p = svtableid(sv)
            nsv = sv / (7 ** growth)
            if p == 1:
                curgain = 1 * t
            elif p == 2 or p == 3:
                curgain = 2 * t
            elif p == 4:
                curgain = 3 * t
            else:
                curgain = 6 * t
            if nsv == 6250 and sm < 2.0:
                await ctx.send("You feel more suave...")
                database.at[idx, 'Sell Modifier'] += 0.05
            if nsv == 9375 and pm < 2.0:
                await ctx.send("You feel more successful...")
                database.at[idx, 'Passive Modifier'] += 0.05
            if nsv == 3125 and lm < 2.0:
                await ctx.send("How lucky!")
                curgain = curgain * 3
                database.at[idx, 'Luck'] += 0.25
            if nsv == 625:
                curgain = curgain * 2
            sellmod = float(userrow.at[idx, 'Sell Modifier'])
            curgain = curgain * sellmod
            database.at[idx, plotcol] = 1
            database.at[idx, 'Currency'] += curgain
            await ctx.send("A fine harvest of " + str(curgain) + " sanddollars.")
    else:
        await ctx.send("You aren't playing! Do g$join to sign up.")


# plot upgrader
@bot.command()
async def upgrade(ctx):
    idx = useridx(ctx)
    playing = playcheck(ctx.message.author.id)
    psize = database.at[idx, 'Plot Size']
    money = int(database.at[idx, 'Currency'])
    if playing:
        if psize == 's' and money >= 8:
            upg(ctx)
        elif psize == 'm' and money >= 16:
            upg(ctx)
        elif psize == 'l' and money >= 32:
            upg(ctx)
        elif psize == 'xl' and money >= 64:
            upg(ctx)
        elif psize == 'xxl':
            await ctx.send("Your plot is already max size!")
        else:
            await ctx.send(
                "You don't have enough currency to upgrade at this time. It costs 7 for the medium, 15 for the large, 31 for the extra large, and 63 for the extra extra large.")  # ha poor
    else:
        await ctx.send("You aren't playing! Do g$join to sign up.")


# collect a plant
@bot.command()
async def collect(ctx, pnum: int):
    playing = playcheck(ctx.message.author.id)
    idx = useridx(ctx)
    plotcol = "plot" + str(pnum) + "status"
    userrow = database.iloc[[idx]]
    if playing:
        fv = int(userrow.at[idx, plotcol])
        col = unstring(userrow.at[idx, 'Collection'])
        dfv = colrev.get(svtodict(fv))
        gfv = svgrowth(fv)
        if col[dfv] == 1:
            await ctx.send("You already have that flower!")
            return
        elif col[dfv] == '0' and gfv == 3:
            col[dfv] = 1
            database.at[idx, plotcol] = 1
        elif gfv == 4:
            await ctx.send("That plant has died...")
        else:
            await ctx.send("Could not collect.")
        new = restring(col)
        database.at[idx, 'Collection'] = new
    else:
        await ctx.send("You aren't playing! Do g$join to sign up.")

# watering
@bot.command()
async def water(ctx):
    idx = useridx(ctx)
    playing = playcheck(ctx.message.author.id)
    userrow = database.iloc[[idx]]
    if playing:
        watered = userrow.at[idx, 'Has Watered']
        await ctx.send(":shower:\nWatering...\n:shower:")
        database.at[idx, 'Has Watered'] = True
        database.at[idx, 'Last Water'] = datetime_to_float(dt.now())
        hardwrite()
    else:
        await ctx.send("You aren't playing! Do g$join to sign up.")

@bot.command()
async def explain(ctx):
    expl = "Welcome to Your Garden, a bot where you can make a little garden, collect plants, and stack ~~paper~~ sanddollars. Once you g$join, you'll have a tiny garden - only 1x1. " \
           "Once you get some money, you can g$upgrade it. You start with a Basic Seed, which you can g$plant, g$water it to keep it growing, then hopefully, g$harvest it" \
           "for sanddollars (the plant currency). You can later g$buy more seeds. If you see a new plant, you can also g$collect it for a little passive income. "
    await ctx.send(expl)


# debug cash
@bot.command()
async def cash(ctx, c: int):
    idx = useridx(ctx)
    if hasrolectx(ctx, 'bottrusted'):
        database.at[idx, 'Currency'] += c
    else:
        await ctx.send("Not so fast.")


# sweep up
@bot.command()
async def sweep(ctx):
    global database
    sweeper = pd.read_csv('v2dbblank.csv')
    database.to_csv("dbbackup.csv", index=False)
    database = sweeper
    hardwrite()
    await ctx.send(":broom:")


@bot.command()
async def nightnight(ctx):
    if hasrolectx(ctx, 'bottrusted'):
        await ctx.send("Night night! :last_quarter_moon_with_face: ")
        quit()
    else:
        await ctx.send("Good night!")


# updater
@tasks.loop(hours=3)
async def update():
    channel = await bot.fetch_channel(945380648934330419)
    global growmod
    userlist = database['User'].tolist()
    for user in userlist:
        idx = database.loc[database['User'] == user].index[0]
        # database.at[idx, "Has Watered"] = False
        lastwater = float_to_datetime(database.at[idx, 'Last Water'])
        delt = dt.now() - lastwater
        hw = database.at[idx, 'Has Watered']
        if delt > maxdelta:  # death timer
            for i in range(0, 25):
                plotcol = "plot" + str(i + 1) + "status"
                plamt = database.at[idx, plotcol]
                g = svgrowth(plamt)
                if plamt % 343 == 0 and plamt % 2401 != 0:
                    new = die(plant)
                else:
                    new = plamt
                database.at[idx, plotcol] = new
        elif delt < maxdelta and hw:  # grow if things are watered
            for i in range(0, 25):
                plotcol = "plot" + str(i + 1) + "status"
                plamt = database.at[idx, plotcol]
                g = svgrowth(plamt)
                if plamt > 1 and g < 4:
                    new = grow(plamt)
                else:
                    new = plamt
                database.at[idx, plotcol] = new
        database.at[idx, 'Has Watered'] = False
        coll = unstring(database.at[idx, "Collection"])
        gain = 0
        for i in coll:
            if i == 1:
                if 0 < coll[i] < 4:
                    gain += 2
                elif 4 <= coll[i]:
                    gain += 0.5
        gain *= database.at[idx, 'Passive Modifier']
        database.at[idx, 'Currency'] += gain
    await channel.send("Update time! Time to water, and see if your plants have grown!")








update.start()


# message event
@bot.event
async def on_message(message):
    if message.author == bot.user:  # no self response
        return
    await bot.process_commands(message)


bot.run(toke)
