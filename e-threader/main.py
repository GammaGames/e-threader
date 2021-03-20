import discord
import os
import re
import asyncio
import reddit
import ebook
import mail
from discord.channel import DMChannel
from pony.orm import db_session
from models import Guild, TextChannel, DmChannel, Message, User, Thread

SIGNUP_CHANNEL = "sign-up"
SIGNUP_REACT = "🙋"
CONFIRM_REACT = "✔️"
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
client = discord.Client()

_print = print

def print(*args, **kwargs):
    _print(*args, flush=True, **kwargs)


def filter_user(user=None):
    return user != client.user


async def get_model(Model, id=None, **kwargs):
    with db_session():
        return Model[id] if Model.exists(id=id) else Model(id=id, **kwargs)


async def init_signup_message(c):
    with db_session():
        channel = TextChannel[c.id]
        m = await c.send("React to this message to set up a bot!")
        Message(id=m.id, channel=channel, content=m.content)
        await m.add_reaction(SIGNUP_REACT)


async def init_signup(u):
    with db_session():
        user = User[u.id]

        m = await u.send("Confirm signup?")
        c = m.channel
        channel = await get_model(DmChannel, id=c.id, user=user)
        Message(id=m.id, channel=channel, content=m.content)
        await m.add_reaction(CONFIRM_REACT)


async def confirm_signup(u):
    with db_session():
        user = User[u.id]

        await u.send("""
Thank you for signing up!
Please assign your email with `?email [YOUREMAIL@kindle.com]`.
        """)


async def process_dm(u, c, m):
    with db_session():
        user = User[u.id]
        text = m.content
        if not user.email and not text.startswith("?email"):
            await u.send("Please assign your email with `?email [YOUREMAIL@kindle.com]` first.")
            channel = await get_model(DmChannel, id=m.channel.id, user=user)
            # Message(id=m.id, channel=channel, content=m.content)
        else:
            if text.startswith("?email"):
                match = re.search(r"\?email\s+(?P<email>[^\s\"]+|\".*\")$", text)
                if match is not None:
                    user.email = match.group("email")
                    await u.send(f"""
Signed up with email: "{user.email}"
Please add us to your approved document email list:
1. Go to "Manage Your Kindle": https://www.amazon.com/myk
2. Under "Approved Personal Document E-mail List" add a new email address
3. Enter "ethreader.bot@gmail.com"
Commands:
    - `?email [EMAIL]`: Set user email
    - `?thread [LINK]`: Send reddit thread to your email as an e-book
    - `?help`: Print this text
                    """)
            if text.startswith("?help"):
                    await u.send("""
Commands:
    - `?email [EMAIL]`: Set user email
    - `?thread [LINK]`: Send reddit thread to your email as an e-book
    - `?help`: Print this text
                    """)
            if not text.startswith("?") or text.startswith("?thread"):
                match = re.search(r"(?:\?thread\s+)?<?(?P<url>https:\/\/www.(?:old\.)?reddit\.com[^\s]+)>?$", text)
                if match is not None:
                    id = await reddit.get_post_id(match.group("url"))
                    print("post:", id)
                    # with open(f"/opt/e-threader/out/{id}.html", "w") as out_file:
                    meta = await reddit.get_post(id)
                    post = await reddit.render_post(id)
                    comments = await reddit.render_comments(id)
                    filename = await ebook.create_book(meta, post, comments)
                    await mail.send_mail(
                        [user.email],
                        meta["title"],
                        "Here is your epub file!",
                        [filename]
                    )
                        # out_file.write(rendered)



@client.event
async def on_ready():
    await reddit.setup()
    with db_session():
        global join_guild, join_channel, join_message
        print("Discord login:", client.user)
        # print(client.private_channels)
        for g in client.guilds:
            guild = await get_model(Guild, id=g.id, name=g.name)

            for c in g.text_channels:
                channel = await get_model(TextChannel, id=c.id, guild=guild, name=c.name)
                if c.name == SIGNUP_CHANNEL:
                    if Message.exists(channel=channel):
                        message = Message.get(channel=channel)
                        m = await c.fetch_message(message.id)

                        # Check for new signups
                        for react in m.reactions:
                            if react.emoji == SIGNUP_REACT:
                                async for u in react.users():
                                    if filter_user(u):
                                        user = await get_model(User, id=u.id, name=u.name)
                                        if not user.email:
                                            await init_signup(u)

                    # Add sign-up message
                    else:
                        await init_signup_message(c)


@client.event
async def on_message(m):
    u = m.author
    with db_session():
        user = await get_model(User, id=u.id, name=u.name)
        if filter_user(u):
            c = m.channel
            # Store messages in textchannel
            if isinstance(m.channel, discord.channel.TextChannel):
                g = m.guild
                guild = await get_model(Guild, id=g.id, name=g.name)
                channel = await get_model(TextChannel, id=c.id, name=c.name, g=guild)
                message = await get_model(Message, id=m.id, content=m.content, user=user, channel=channel)
                # Don't do anything for text channel messages
            # Parse incoming requests
            if isinstance(m.channel, discord.channel.DMChannel):
                channel = await get_model(DmChannel, id=c.id, user=user)
                message = await get_model(Message, id=m.id, content=m.content, channel=channel)
                await process_dm(u, c, m)


@client.event
async def on_raw_reaction_add(payload):
    u = payload.member
    if u is None:
        u = await client.fetch_user(payload.user_id)
    if filter_user(u):
        with db_session():
            user = await get_model(User, id=u.id, name=u.name)
            react = payload.emoji.name
            # Signup actions
            if react == SIGNUP_REACT and not user.email:
                await init_signup(u)

            elif react == CONFIRM_REACT:
                await confirm_signup(u)


@client.event
async def on_raw_reaction_remove(payload):
    with db_session():
        user = User[payload.user_id]
        if user.id != client.user.id:
            message = Message[payload.message_id]


client.run(DISCORD_TOKEN)
