import discord
import os
from pony.orm import db_session
from models import Guild, Channel, Message, User, Thread

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
client = discord.Client()

_print = print

def print(*args, **kwargs):
    _print(*args, flush=True, **kwargs)


@client.event
async def on_ready():
    with db_session():
        global join_guild, join_channel, join_message
        print("We have logged in as {0.user}".format(client))
        print(client.private_channels)
        for g in client.guilds:
            guild = Guild[g.id] if Guild.exists(id=g.id) else Guild(id=g.id, name=g.name)

            for c in g.text_channels:
                channel = Channel[c.id] if Channel.exists(id=c.id) else Channel(id=c.id, guild=guild, name=c.name)
                if c.name == "sign-up":
                    if Message.exists(channel=channel):
                        pass
                        # TODO check if new subscribers
                    else:
                        m = await c.send("React to this message to set up a bot!")
                        message = Message(id=m.id, channel=channel, content=m.content)
                        await m.add_reaction("🙋")


@client.event
async def on_raw_reaction_add(payload):
    u = payload.member
    if u != client.user:
        with db_session():
            guild = Guild[payload.guild_id]
            channel = Channel[payload.channel_id]
            message = Message[payload.message_id]
            user = User[u.id] if User.exists(id=u.id) else User(id=u.id, name=u.name)
            # TODO send message to user to confirm
            print("add", user, message)
            # confirm_message = await user.send("Confirm?")
            # await confirm_message.add_reaction("✔️")


@client.event
async def on_raw_reaction_remove(payload):
    print(payload)
    with db_session():
        user = User[payload.user_id]
        if user.id != client.user.id:
            message = Message[payload.message_id]
            # TODO remove user?
            print("remove", user, message)
            # confirm_message = await user.send("Confirm?")
            # await confirm_message.add_reaction("✔️")


# @client.event
# async def on_message(message):
#     if message.author == client.user:
#         return

#     print(message)

#     if message.content.startswith("$hello"):
#         await message.channel.send("Hello!")


client.run(DISCORD_TOKEN)
