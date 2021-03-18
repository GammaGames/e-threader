import discord
import os
from pony.orm import db_session
from models import Guild, Channel, Message, User, Thread

SIGNUP_REACT = "🙋"
CONFIRM_REACT = "✔️"
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
client = discord.Client()

_print = print

def print(*args, **kwargs):
    _print(*args, flush=True, **kwargs)


def filter_user(user=None):
    return user != client.user


@db_session
async def init_signup(u):
    print("signup", u)
    user = User[u.id]

    confirm_message = await u.send("Confirm?")
    # await confirm_message.add_reaction("✔️")
    print(confirm_message)


@db_session
async def confirm_signup(user):
    pass


@db_session
async def process_message(message):
    pass


@client.event
async def on_ready():
    with db_session():
        global join_guild, join_channel, join_message
        print("We have logged in as {0.user}".format(client))
        # print(client.private_channels)
        for g in client.guilds:
            guild = Guild[g.id] if Guild.exists(id=g.id) else Guild(id=g.id, name=g.name)

            for c in g.text_channels:
                channel = Channel[c.id] if Channel.exists(id=c.id) else Channel(id=c.id, guild=guild, name=c.name)
                if c.name == "sign-up":
                    if Message.exists(channel=channel):
                        message = Message.get(channel=channel)
                        m = await c.fetch_message(message.id)

                        for reaction in m.reactions:
                            print(reaction)
                            async for u in reaction.users():
                                if filter_user(u):
                                    user = User[u.id] if User.exists(id=u.id) else User(id=u.id, name=u.name)
                                    if not user.email:
                                        print(f"init signup {u}")
                                        z = await init_signup(u)


                        # TODO check if new subscribers
                    else:
                        m = await c.send("React to this message to set up a bot!")
                        message = Message(id=m.id, channel=channel, content=m.content)
                        await m.add_reaction(SIGNUP_REACT)


@client.event
async def on_raw_reaction_add(payload):
    # print(payload)
    u = payload.member
    if filter_user(u):
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
