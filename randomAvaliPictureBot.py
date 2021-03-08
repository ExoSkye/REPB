import json, requests, random, discord, pickle
from discord.utils import get

class RAPB(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)
        self.artist_blacklist = ["conditional_dnp", "epilepsy_warning", "sound_warning"]
        self.pic_blacklist = ["epilepsy_warning"]

    async def getpic(self, url, message):
        if message.channel.id in self.get_channel_settings():
            headers = {
                "User-Agent": "RandomAvaliPicDiscordBot/1.0 (by ProtoByte on e926)"
            }
            r = requests.get(url, headers=headers)

            if r.status_code != 200:
                await message.channel.send("Got non-200 return code: " + str(r.status_code) + " (" +
                                           requests.status_codes._codes[r.status_code][0] + ")")
            else:
                return_json = json.loads(r.text)
                if len(return_json["posts"]) == 0:
                    await message.channel.send("That search didn't find anything, please check your query")
                else:
                    idx = random.randint(0, len(return_json["posts"]) - 1)
                    artists = return_json["posts"][idx]["tags"]["artist"]
                    image_location = return_json["posts"][idx]["file"]["url"]
                    sound_warning = ""
                    segment_type = " picture "
                    if "animated" in return_json["posts"][idx]["tags"]["general"]:
                        segment_type = " animation "
                    for artist in artists:
                        if artist in self.artist_blacklist:
                            if artist == "sound_warning":
                                sound_warning = "[SOUND WARNING] "
                            artists.remove(artist)
                        if artist in self.pic_blacklist:
                            await self.getpic(url, message)
                            return
                    if len(artists) == 0:
                        artists.append("a mysterious person")
                    await message.channel.send(sound_warning + "Got this" + segment_type + "by " + " and ".join(
                        artists) + ". Available here: " + image_location)

        else:
            await message.channel.send("I'm not allowed to post here")

    def get_channel_settings(self):
        channels = {}
        try:
            with open("channels.pickle", 'rb') as channel_file:
                channels = pickle.load(channel_file)
        except:
            pass
        return channels

    def save_channel_settings(self, channel):
        with open("channels.pickle", 'wb+') as channel_file:
            pickle.dump(channel, channel_file)

    def get_server_settings(self):
        servers = {}
        try:
            with open("servers.pickle", 'rb') as channel_file:
                servers = pickle.load(channel_file)
        except:
            ret = {}
            self.save_servers_settings(ret)
            return ret
        return servers

    def save_servers_settings(self, server):
        with open("servers.pickle", 'wb+') as servers_file:
            pickle.dump(server, servers_file)

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
                    await self.getpic('https://e621.net/posts.json?tags=order:random rating:m rating:q ' +
                                      self.get_channel_settings()[message.channel.id] + '&limit=320', message)
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
                await message.channel.send(
                    "Successfully set the search query to " + self.get_channel_settings()[message.channel.id])
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

        elif message.content.startswith("!setuproles"):
            if message.author.permissions_in(message.channel).administrator:
                args = message.content[12:].split(" ")
                print(args)
                msg_id = args[1]
                content = json.loads(args[0])
                for channel in message.guild.channels:
                    message2 = None
                    try:
                        message2 = await channel.fetch_message(msg_id)
                    except discord.NotFound:
                        pass
                    except AttributeError:
                        pass
                    else:
                        settings = self.get_server_settings()
                        settings[str(message2.guild.id)] = {}
                        for roles in content["roles"]:
                            emoji = roles["emoji"].strip(" ")
                            role_id = roles["role_id"]
                            await message2.add_reaction(emoji)
                            settings_cur_server = settings[str(message2.guild.id)]
                            try:
                                settings_cur_server["roles"][0]
                            except:
                                settings_cur_server["roles"] = []

                            settings_cur_server["roles"].append({"emoji": emoji, "role_id": role_id})
                            settings_cur_server["roles_msg_id"] = msg_id
                            settings[str(message2.guild.id)] = settings_cur_server

                            self.save_servers_settings(settings)

                        break

                await message.channel.send("Successfully set watched message up")

            else:
                await message.channel.send("You aren't allowed to do that")

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        settings = self.get_server_settings()
        if str(payload.guild_id) in settings:
            settings_cur_server = settings[str(payload.guild_id)]
            msg_id = settings_cur_server["roles_msg_id"]
            if int(msg_id) == payload.message_id:
                for role in settings_cur_server["roles"]:
                    emoji = role["emoji"]
                    role_id = role["role_id"]
                    if emoji == payload.emoji.name:
                        guild = self.get_guild(payload.guild_id)
                        role = guild.get_role(int(role_id))
                        await payload.member.add_roles(role)
                        break

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        settings = self.get_server_settings()
        if str(payload.guild_id) in settings:
            settings_cur_server = settings[str(payload.guild_id)]
            msg_id = settings_cur_server["roles_msg_id"]
            if int(msg_id) == payload.message_id:
                for role in settings_cur_server["roles"]:
                    emoji = role["emoji"]
                    role_id = role["role_id"]
                    if emoji == payload.emoji.name:
                        guild = self.get_guild(payload.guild_id)
                        role = guild.get_role(int(role_id))
                        member = guild.get_member(payload.user_id)
                        await member.remove_roles(role)
                        break

intents = discord.Intents.default()
intents.members = True
client = RAPB(intents=intents)
with open(".token") as tokenfile:
    key = tokenfile.read()
    client.run(key)
