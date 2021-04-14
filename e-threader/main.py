import discord
import os
import re
import reddit
import ebook
import mail
from pony.orm import db_session, select
from models import Guild, TextChannel, DmChannel, Message, User, Thread

SIGNUP_CHANNEL = "sign-up"
LOG_CHANNEL = "bot-log"
SIGNUP_REACT = "🙋"
CONFIRM_REACT = "✔️"
SEEN_REACT = "👀"
FETCHED_REACT = "⬆️"
RENDERED_REACT = "📖"
SENT_REACT = "📬"
COMPLETE_REACT = "✔️"
ERROR_REACT = "❌"
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GMAIL_USERNAME = client_secret=os.getenv("GMAIL_USERNAME")
HELP_TEXT = """
Commands:
    - `?email [EMAIL]`: Set user email
    - `[LINK]`: Send reddit thread to your email as an e-book (default command)
    - `?thread [LINK]`: Send reddit thread to your email as an e-book
    - `?serial [LINK]`: Send links from reddit thread/wiki to your email as an e-book
    - `?help`: Print this text
"""
client = discord.Client()

_print = print

def print(*args, **kwargs):
    _print(*args, flush=True, **kwargs)


async def send_log(message):
    print(message)
    with db_session():
        log_channels = select(c for c in TextChannel if c.name == LOG_CHANNEL)
        for channel in log_channels:
            lc = client.get_channel(channel.id)
            await lc.send(message)


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
    await send_log(f"Signing up: {u.name}")
    with db_session():
        user = User[u.id]

        m = await u.send("Confirm signup?")
        c = m.channel
        channel = await get_model(DmChannel, id=c.id, user=user)
        Message(id=m.id, channel=channel, content=m.content)
        await m.add_reaction(CONFIRM_REACT)


async def confirm_signup(u):
    await send_log(f"Confirmed: {u.name}")
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
        else:
            if text.startswith("?email"):
                match = re.search(r"\?email\s+(?P<email>[^\s\"]+|\".*\")$", text)
                if match is not None:
                    user.email = match.group("email")
                    await send_log(f"Email set: {user.name}")
                    await u.send(f"""
Signed up with email: "{user.email}"
Please add us to your approved document email list:
1. Go to "Manage Your Kindle": https://www.amazon.com/myk
2. Under "Approved Personal Document E-mail List" add the following address:
""")
                    await u.send(GMAIL_USERNAME)
                    await u.send("To remove books from your Kindle, visit https://www.amazon.com/mn/dcw/myx.html#/home/content/pdocs/dateDsc/")
                    await u.send(HELP_TEXT)
            if text.startswith("?help"):
                    await u.send(HELP_TEXT)
            if not text.startswith("?") or text.startswith("?thread"):
                match = re.search(r"(?:\?thread\s+)?<?(?P<url>https:\/\/(?:www\.)?(?:old\.)?reddit\.com[^\s]+)>?$", text)
                if match is not None:
                    url = match.group("url")
                    await m.add_reaction(SEEN_REACT)
                    await send_log(f"Thread received: {user.name}, <{url}>")
                    id = reddit.get_post_id(url)
                    meta = await reddit.get_post(id)
                    post = await reddit.render_post(id)
                    comments = await reddit.render_comments(id)
                    await m.add_reaction(FETCHED_REACT)
                    filename = ebook.create_book_from_thread(meta, post, comments)
                    await m.add_reaction(RENDERED_REACT)
                    await mail.send_mail(
                        [user.email],
                        meta["title"],
                        "Here is your epub file!",
                        [filename]
                    )
                    await m.add_reaction(SENT_REACT)
                    await m.add_reaction(COMPLETE_REACT)
                    await send_log(f"Thread complete: {user.name}, <{url}>")
                else:
                    await m.add_reaction(ERROR_REACT)
                    await send_log(f"Message error: {user.name}, >{text}")

            if text.startswith("?serial"):
                match = re.search(r"(?:\?serial\s+)?<?(?P<url>https:\/\/www.(?:old\.)?reddit\.com[^\s]+)>?$", text)
                if match is not None:
                    url = match.group("url")
                    print(url)
                    await m.add_reaction(SEEN_REACT)
                    await send_log(f"Serial received: {user.name}, <{url}>")
                    wiki_match = re.search(r"reddit\.com\/r\/(?P<subreddit>\w+)\/wiki\/(?P<page>\w+)$", text)
                    text = await reddit.get_wiki_text(
                        wiki_match.group("subreddit"), wiki_match.group("page")
                    ) if wiki_match is not None else await reddit.get_post_text(reddit.get_post_id(url))
                    ids = reddit.scrape_post_ids(text)
                    if len(ids):
                        meta = await reddit.get_post(ids[0])
                        await m.add_reaction(FETCHED_REACT)
                        posts = [
                            await reddit.render_post(id, template="serial_post.html")
                            for id in ids
                        ]
                        filename = ebook.create_book_from_serial(meta, posts)
                        await m.add_reaction(RENDERED_REACT)
                        await mail.send_mail(
                            [user.email],
                            meta["title"],
                            "Here is your epub file!",
                            [filename]
                        )
                        await m.add_reaction(SENT_REACT)
                        await m.add_reaction(COMPLETE_REACT)
                        await send_log(f"Serial complete: {user.name}, <{url}>")


@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online)
    await send_log(f"Discord connected: {client.user}")
    reddit_user = await reddit.setup()

    await send_log(f"Reddit connected: {reddit_user}")
    with db_session():
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
                user = await get_model(User, id=u.id, name=u.name)
                guild = await get_model(Guild, id=g.id, name=g.name)
                channel = await get_model(TextChannel, id=c.id, name=c.name, g=guild)
                message = await get_model(Message, id=m.id, content=m.content, user=user, channel=channel)
                # Don't do anything for text channel messages
            # Parse incoming requests
            if isinstance(m.channel, discord.channel.DMChannel) and User.exists(id=u.id):
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
            if react == SIGNUP_REACT and TextChannel.exists(id=payload.channel_id, name=SIGNUP_CHANNEL) and not user.email:
                await init_signup(u)
            # Signup confirmation
            elif react == CONFIRM_REACT and DmChannel.exists(id=payload.channel_id):
                await confirm_signup(u)


@client.event
async def on_raw_reaction_remove(payload):
    with db_session():
        user = User[payload.user_id]
        if user.id != client.user.id:
            message = Message[payload.message_id]


client.run(DISCORD_TOKEN)
