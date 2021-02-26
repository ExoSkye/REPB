import json, requests, random, discord, pickle

class RAPB(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)
        self.query = "avali"

    async def getpic(self,url, message):
        if message.channel.id in self.get_channel_settings():
            headers = {
                    "User-Agent": "RandomAvaliPicDiscordBot/1.0 (by ProtoByte on e926)"
                }
            r = requests.get(url,headers=headers)


            if r.status_code != 200:
                await message.channel.send("Got non-200 return code: "+str(r.status_code)+" ("+requests.status_codes._codes[r.status_code][0]+")")
            else:
                return_json = json.loads(r.text)
                if len(return_json["posts"]) == 0:
                    await message.channel.send("That search didn't find anything, please check your query")
                else:
                    idx = random.randint(0,len(return_json["posts"])-1)
                    artists = return_json["posts"][idx]["tags"]["artist"]
                    image_location = return_json["posts"][idx]["file"]["url"]
                    if len(artists) == 0:
                        artists.append("a mysterious person")
                    await message.channel.send("Got this picture by "+" and ".join(artists)+". Available here: "+image_location)

        else:
            await message.channel.send("I'm not allowed to post here")

    def get_channel_settings(self):
        channels = {}
        try:
            with open("channels.pickle",'rb') as channel_file:
                channels = pickle.load(channel_file)
        except:
            pass
        return channels

    def save_channel_settings(self,channel):
        with open("channels.pickle",'wb+') as channel_file:
            pickle.dump(channel,channel_file)

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        elif message.content == '!gethelp':
             await message.channel.send('https://www.youtube.com/watch?v=OANob2HpS4o')

        elif message.content == '!getpic':
            lewd_role = False
            for role in message.author.roles:
                    if role.name == "Lewd":
                        lewd_role = True
                        break

            if message.channel.is_nsfw():
                if lewd_role:
                    await self.getpic('https://e621.net/posts.json?tags=order:random rating:m rating:q '+self.get_channel_settings()[message.channel.id]+'&limit=320',message)
                else:
                    await message.channel.send(
                        "You are not authorised to ask for an NSFW picture, please make sure that you have the @Lewd role")
            else:
                await self.getpic('https://e926.net/posts.json?tags=order:random ' + self.get_channel_settings()[
                    message.channel.id] + '&limit=320', message)


        elif message.content[:9] == "!setquery":
            if message.author.permissions_in(message.channel).administrator:
                channels = self.get_channel_settings()
                channels[message.channel.id] = message.content[10:]
                self.save_channel_settings(channels)
                await message.channel.send("Successfully set the search query to "+self.get_channel_settings()[message.channel.id])
            else:
                await message.channel.send("You aren't allowed to do that")

        elif message.content == "!help":
            await message.channel.send("""Possible commands:
            !getpic     - Gets a picture from e926 or e621 (dependent on having a lewd role and being in an nsfw chat) using the query set by an admin
            !setquery   - Sets the query to search with (admin only)
            !help       - Prints this help
            !allowpost  - Adds the current channel to channels that this bot can use
            """)

        elif message.content == "!allowpost":
            if message.author.permissions_in(message.channel).administrator:
                channels = self.get_channel_settings()
                channels[message.channel.id] = "avali_(original)"
                self.save_channel_settings(channels)
                await message.channel.send("I can now post here")
            else:
                await message.channel.send("You aren't allowed to do that")
        


client = RAPB()
with open(".token") as tokenfile:
    key = tokenfile.read()
    client.run(key)
