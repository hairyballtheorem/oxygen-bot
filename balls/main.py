import random
import asyncio
import discord

from balls.db import *
from discord.ext.commands import *

crt_users_running = {}

class Main(Cog):
    def __init__(self, client : Bot):
        self.client = client
    
    def get_blocks_per_min(self, id):
        ret = 20
        for i in range(levels[id][0]):
            ret += 20
        
        return ret
    
    def get_bp_capacity(self, id):
        ret = 200
        for i in range(levels[id][1]):
            ret += 100
        
        return ret

    def get_upgrade_cost(self, l):
        base = 100

        if l < 50:
            for i in range(l):
                base *= 1.1
        else:
            for i in range(50):
                base *= 1.1

            for i in range(50, l):
                base += 500

        return int(round(base, 0))

    @Cog.listener()
    async def on_message(self, message): #this function gets invoked whenever a message is sent
        if not message.author.bot: #ignore bots
            try:
                if not crt_users_running[str(message.author.id)]: #if user is not already running
                    while running[str(message.author.id)]: #while backpack is not full
                        #crt_users_running contains the users that are already running in this function. When the backpack gets filled, this function will stop.
                        #crt_users_running running multiple instances of this function

                        crt_users_running[str(message.author.id)] = True #user is running
                        s = 0
                        for i in backpack[str(message.author.id)]: #for every item in backpack
                            s += i[1] #get a sum of total items in the backpack
                            
                        capacity = self.get_bp_capacity(str(message.author.id))
                        if mult[str(message.author.id)][2] != 0:
                            capacity *= mult[str(message.author.id)] #apply backpack capacity multipliers
                            capacity = int(capacity) #round capacity

                        if s >= capacity: #if the sum is greater or equal than the backpack capacity...
                            running[str(message.author.id)] = False #set backpack full
                            crt_users_running[str(message.author.id)] = False #user is not running
                            break #exit
                            
                        bpm = self.get_blocks_per_min(str(message.author.id)) / 2 #blocks mined per 30 seconds
                        if mult[str(message.author.id)][1] != 0:
                            bpm *= mult[str(message.author.id)] #apply mining speed multipliers
                            bpm = int(bpm)

                        if bpm > capacity - s: #if amount of blocks to claim, are more than the free capacity...
                            to_add = capacity - s #add free capacity
                            running[str(message.author.id)] = False #set backpack full
                            crt_users_running[str(message.author.id)] = False #user is not running
                        else:
                            to_add = bpm #set amount of items to add

                        crt_stage = str(levels[str(message.author.id)][4]) #get current stage
                        t = random.choices(stages[crt_stage]["blocks"], stages[crt_stage]["chances"], k=to_add) #get the list of items to add into backpack
                        unique_list = stages[crt_stage]["blocks"] #get a list of items available in this stage
                        unique_list.sort() #sort the items

                        def ret_first(elm):
                            return elm[0] #return the first element of the list

                        try:
                            backpack[str(message.author.id)].sort(key=ret_first) #sort the backpack items by the first element of each list
                        except TypeError:
                            pass #already sorted

                        for i in range(len(unique_list)): #from 0 to (amount of available items)
                            backpack[str(message.author.id)][i][0] = unique_list[i] #add item to backpack
                            backpack[str(message.author.id)][i][1] += t.count(unique_list[i]) #set quantity
                        
                        mined[str(message.author.id)] += bpm #amount of blocks mined, never resets
                        save() #save updated data
                        await asyncio.sleep(30) #wait for 30 seconds
            except KeyError: #if user is not registered in one of the dictionaries
                if str(message.author.id) in running and running[str(message.author.id)]: #if user is registered and backpack is not full
                    crt_users_running[str(message.author.id)] = False #set user not running

    @command()
    async def start(self, ctx):
        if str(ctx.author.id) in coins: #if user is registered
            return await ctx.send("You have already started your profile.")
        
        init_all(str(ctx.author.id)) #initialize every list entry for the user
        await ctx.send("Registered successfully.")
        running[str(ctx.author.id)] = True #set backpack not full
        crt_users_running[str(ctx.author.id)] = True #set user running
        save()
    
    @command(aliases=["s"])
    async def sell(self, ctx):
        if str(ctx.author.id) in coins:
            if backpack[str(ctx.author.id)][0][0] == 0: #backpack is empty
                await ctx.reply("You do not have any items in your backpack.")
                return

            l = [] #item, quantity
            j = 0
            earnings = 0
            for i in range(3):
                if backpack[str(ctx.author.id)][i][0] == 0: #empty entry
                    continue
            
                l.append(backpack[str(ctx.author.id)][i])
                j += 1
                earnings += blocks[backpack[str(ctx.author.id)][i][0]] * backpack[str(ctx.author.id)][i][1] #get total earnings
                coins[str(ctx.author.id)] += earnings #and add them to coins database
                backpack[str(ctx.author.id)][i] = [0, 0] #since we sold the items, our backpack is empty now
            
            running[str(ctx.author.id)] = True

            #the on_message function has been already invoked for this message, if we set this value to True,
            #on_message will not run in the next message.
            crt_users_running[str(ctx.author.id)] = False

            save()

            desc = "**You sold:**\n"
            for i in l:
                desc += f"{i[1]}x {i[0]} {emojis[i[0]]}\n"
            desc += f"\nYou earned: **{earnings:,}** coins"
        
            e = discord.Embed(title="You sold your items from your backpack", description=desc, color=discord.Color.random())
            await ctx.reply(embed=e)
        else:
            await ctx.reply("You are not registered yet. Use `.start` to get started")
    
    @command(aliases=["p"])
    async def prestige(self, ctx):
        if levels[str(ctx.author.id)][0] >= 200 and levels[str(ctx.author.id)][1] >= 200: #if we have the required upgrades for prestige...
            levels[str(ctx.author.id)][2] += 1 #add 1 to prestige
            coins[str(ctx.author.id)] = 0 #set coins to zero
            levels[str(ctx.author.id)][0] = levels[str(ctx.author.id)][1] = 1 #set backpack and pickaxe levels to 1
            tokens[str(ctx.author.id)][0] += 1 #add 1 prestige token

            if levels[str(ctx.author.id)][2] % 3 == 0 and levels[str(ctx.author.id)][4] < 8: #unlocked a new stage
                levels[str(ctx.author.id)][4] += 1
                await ctx.send(f"You prestiged to prestige {levels[str(ctx.author.id)][2]}. You also unlocked stage {levels[str(ctx.author.id)][4]}")
            else:
                await ctx.send(f"You prestiged to prestige {levels[str(ctx.author.id)][2]}.")
            
            save()
        else:
            await ctx.reply("You do not meet the requirements to prestige")

    @command(aliases=["rb"])
    async def rebirth(self, ctx):
        if levels[str(ctx.author.id)][2] >= 24 and levels[str(ctx.author.id)][0] >= 200 and levels[str(ctx.author.id)][1] >= 200: #if we meet rebirth requirements...
            coins[str(ctx.author.id)] = 0 #set coins to zero
            levels[str(ctx.author.id)][3] += 1 #add 1 to rebirth count
            levels[str(ctx.author.id)][0] = levels[str(ctx.author.id)][1] = 1 #set backpack and pickaxe levels to 1
            levels[str(ctx.author.id)][2] = 0 #set prestiges to zero
            levels[str(ctx.author.id)][4] = 1 #stage 1
            tokens[str(ctx.author.id)][0] = 0 #set prestige tokens to zero
            tokens[str(ctx.author.id)][1] += 1 #add 1 rebirth token

            await ctx.send(f"You unlocked rebirth {levels[str(ctx.author.id)][3]}.")
            save()
        
        else:
            await ctx.reply("You do not meet the requirements to rebirth.")
        
    @command(aliases=["info", "sinfo"])
    async def stage_info(self, ctx):
        desc = str() #intialize description
        for i in stages.keys(): #for every stage...
            desc += f"**stage {i}**\nPrestige requirement: {stages[i]['requirement']}\nBlocks:\n" #add prestige requirement
            for j in stages[i]["blocks"]: #for every block in that stage...
                desc += f"{emojis[j]} {j}\n" #append the corresponding emoji and the block name
            desc += "\n" #add a new line
        
        e = discord.Embed(title="list of stages", description=desc, color=discord.Color.random())
        await ctx.send(embed=e)

    @command(aliases=["cv", "conv"])
    async def convert(self, ctx, amount):
        if tokens[str(ctx.author.id)][1] == 0:
            await ctx.reply("You do not have any rebirth tokens")
        elif amount > tokens[str(ctx.author.id)][1]:
            await ctx.reply("You do not have that many rebirth tokens")
        else:
            if amount == "max" or amount == "all":
                await ctx.reply(f"You converted {tokens[str(ctx.author.id)][1]} rebirth tokens into {tokens[str(ctx.author.id)][1] * 3} prestige tokens")
                tokens[str(ctx.author.id)][0] += tokens[str(ctx.author.id)][1] * 3 #1 rebirth token -> 3 prestige tokens
                tokens[str(ctx.author.id)][1] = 0
            elif amount <= 0:
                await ctx.reply("Invalid input")
            else:
                await ctx.reply(f"You converted {amount} rebirth tokens into {amount * 3} prestige tokens")
                tokens[str(ctx.author.id)][0] += amount * 3
                tokens[str(ctx.author.id)][1] -= amount
            
            save()

    @command(aliases=["lb", "top"])
    async def leaderboard(self, ctx, t = "coins"):
        if t == "coins":
            d = sort_by_value(coins) #sort our coins dictionary by value
            desc = str()
            r = range(len(d.keys())) if len(d.keys()) < 10 else range(10) #limit amount of people in leaderboard to 10
            for i in r:
                user = await self.client.fetch_user(int(list(d.keys())[i]))
                desc += f"**#{i + 1} {user}** {d[list(d.keys())[i]]:,} coins\n" #the ":," in fstring adds a thousandth seperator
            
            e = discord.Embed(title="Global coin leaderboard", description=desc)
            await ctx.reply(embed=e)
        elif t == "rebirth":
            keys = list(levels.keys())
            items = []

            for i in keys:
                items.append(levels[i][3])
            
            d = sort_by_value(dict(zip(keys, items))) #create a new dictionary from our keys and items lists and then sort it
            desc = str()
            r = range(len(d.keys())) if len(d.keys()) < 10 else range(10)
            for i in r:
                user = await self.client.fetch_user(int(list(d.keys())[i]))
                desc += f"**#{i + 1} {user}** {d[list(d.keys())[i]]:,} rebirths\n"
            
            e = discord.Embed(title="Global rebirth leaderboard", description=desc) 
            await ctx.reply(embed=e)
        elif t == "prestige":
            keys = list(levels.keys())
            items = []

            for i in keys:
                items.append(levels[i][2])
            
            d = sort_by_value(dict(zip(keys, items)))
            desc = str()
            r = range(len(d.keys())) if len(d.keys()) < 10 else range(10)
            for i in r:
                user = await self.client.fetch_user(int(list(d.keys())[i]))
                desc += f"**#{i + 1} {user}** {d[list(d.keys())[i]]:,} prestiges\n"

            e = discord.Embed(title="Global prestige leaderboard", description=desc)
            await ctx.reply(embed=e)
        elif t == "mined":
            d = sort_by_value(coins)
            desc = str()
            r = range(len(d.keys())) if len(d.keys()) < 10 else range(10)
            for i in r:
                user = await self.client.fetch_user(int(list(d.keys())[i]))
                desc += f"**#{i + 1}** {d[list(d.keys())[i]]:,} blocks\n"
            
            e = discord.Embed(title="Blocks mined leaderboard", description=desc)
            await ctx.reply(embed=e)
        else:
            await ctx.reply("Invalid input")

    @command(aliases=["up"])
    async def upgrade(self, ctx, tool, level = None):
        global coins
        if str(ctx.author.id) in coins:
            if tool == "pickaxe" or tool == "p":
                tool = 0
                toolstr = "pickaxe"
            elif tool == "backpack" or tool == "bp":
                tool = 1
                toolstr = "backpack"
            else:
                await ctx.reply("Invalid argument.")
                return
            
            if level == None: #no level argument provided
                cost = self.get_upgrade_cost(levels[str(ctx.author.id)][tool] + 1) #get next level cost
                if cost > coins[str(ctx.author.id)]: #not enough coins
                    await ctx.reply(f"You do not have enough coins to upgrade your {toolstr}.")
                    return
                    
                coins[str(ctx.author.id)] -= cost
                levels[str(ctx.author.id)][tool] += 1
                save()
                await ctx.reply(f"You upgraded your {toolstr} to **level {levels[str(ctx.author.id)][tool]}** for **{cost} coins**")
            elif level == "max":
                i_initial = levels[str(ctx.author.id)][tool]
                i = i_initial

                while self.get_upgrade_cost(i) < coins[str(ctx.author.id)]:
                    i += 1
                    coins[str(ctx.author.id)] -= self.get_upgrade_cost(i)

                if i == i_initial: #level is the same as the base level which means it did not change
                    await ctx.reply(f"You do not have enough coins to upgrade your {toolstr}.")
                    return
                
                levels[str(ctx.author.id)][tool] = i
                save()

                await ctx.reply(f"You upgraded your {toolstr} to **level {levels[str(ctx.author.id)][tool]}** for **{cost} coins**")
            elif int(level) <= 0:
                await ctx.reply("Invalid input")
            else:
                l = int(level)
                cost = 0
                r = levels[str(ctx.author.id)][tool]
                for i in range(l):
                    r += 1
                    cost += self.get_upgrade_cost(r)
                    if cost > coins[str(ctx.author.id)]:
                        await ctx.reply(f"You do not have enough money to upgrade your {toolstr}.")
                        return
                    
                levels[str(ctx.author.id)][tool] += r
                coins[str(ctx.author.id)] -= cost
                save()
                await ctx.reply(f"You upgraded your {toolstr} to **level {levels[str(ctx.author.id)][tool]}** for **{cost} coins**")
        else:
            await ctx.reply("You are not registered yet. Use `.start` to get started")

    @command()
    async def shop(self, ctx, mode = None):
        ...
    
    @command()
    async def help(self, ctx, command = None):
        if command == None:
            e = discord.Embed(title="Help", description="", color=discord.Color.blue())
            v = str()
            for i in helplist.keys():
                v += i + (", " if list(helplist.keys())[len(list(helplist.keys())) - 1] != i else "")
            e.add_field(name="Command list", value=v)

            await ctx.reply(embed=e)
        else:
            t = get_key_by_subdict_item(helplist, "aliases", command) #retrieve command name, if command parameter is an alias
            if t == -1: #command not in dictionary keys and not an alias
                await ctx.reply("Invalid query")
                return
            
            e = discord.Embed(title=f"help for command {t}", description=helplist[t]["description"], color=discord.Color.blue())

            if helplist[t]["aliases"] != None:
                e.add_field(name="Aliases", value=helplist[t]["aliases"], inline=False)
            if helplist[t]["args"] != None:
                e.add_field(name="Usage", value=f"```\n.{t} {helplist[t]['args']}\n```", inline=False)
            if helplist[t]["footer"] != None:
                e.set_footer(text=helplist[t]["footer"])
            
            await ctx.reply(embed=e)

    #commands by @archisha69
    @command(aliases=["pf", "userinfo", "uinfo"])
    async def profile(self, ctx, user:discord.User = None):
        if user == None:
            user = ctx.author

        if str(user.id) not in coins:
            await ctx.reply("This user is not registered.")
            return

        embed = discord.Embed(title=f"{user}'s profile", description=bio[str(user.id)] if bio[str(user.id)] != 0 else "", color=discord.Color.blue())
        embed.add_field(name="**-----Status-----**", value="_ _", inline=False)
        embed.add_field(name="Current stage:", value=levels[str(user.id)][4], inline=False)
        embed.add_field(name="Blocks mined:", value=mined[str(user.id)], inline=False)
        embed.add_field(name="Prestige(s):", value=levels[str(user.id)][2], inline=False)
        embed.add_field(name="Rebirth(s):", value=levels[str(user.id)][3], inline=False)
        embed.add_field(name="**-----Levels-----**", value="_ _", inline=False)
        embed.add_field(name="Pickaxe level:", value=levels[str(user.id)][0], inline=False)
        embed.add_field(name="Blocks/min", value=self.get_blocks_per_min(str(user.id)), inline=True)
        embed.add_field(name="Backpack level:", value=levels[str(user.id)][1], inline=False)
        embed.add_field(name="Backpack capacity", value=self.get_bp_capacity(str(user.id)), inline=True)
        await ctx.send(embed=embed)

    @command(aliases=["bio", "setbio"])
    async def userbio(self, ctx, *, content : str = None):
        if content != None:
            content = content.strip() #remove leading and trailing spaces
            if len(content) > 100:
                await ctx.reply("You have reached the 100 character limit.")
                return
            
            bio[str(ctx.author.id)] = content
            await ctx.reply(f"Your bio has been set to {content}")
        else:
            bio[str(ctx.author.id)] = 0
            await ctx.reply("Your bio has been resset successfully")
        
        save()
        

    @command(aliases=["inv", "inventory", "bp"])
    async def backpack(self, ctx, user : discord.User = None):
        if user == None:
            user = ctx.author

        if str(user.id) not in backpack:
            await ctx.reply("This user is not registered.")
            return
        
        embed = discord.Embed(title=f"{user}'s backpack", description="", color=discord.Color.blue())
        for i in range(3):
            if backpack[str(user.id)][i][0] != 0:
                embed.add_field(name=f"{emojis[backpack[str(user.id)][i][0]]} {backpack[str(user.id)][i][0]}", value=backpack[str(user.id)][i][1], inline=False)
        
        await ctx.reply(embed=embed)

    #end commands by archisha69

async def setup(client):
    await client.add_cog(Main(client))