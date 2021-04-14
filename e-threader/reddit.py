import asyncpraw as praw
import os
import re
import markdown
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("/opt/e-threader/templates"))
reddit = None

async def setup():
    global reddit
    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_SECRET"),
        username=os.getenv("REDDIT_USERNAME"),
        password=os.getenv("REDDIT_PASSWORD"),
        user_agent="testing e-threader",
    )
    me = await reddit.user.me()
    return me


def get_post_id(url):
    return praw.models.Submission.id_from_url(url)


async def get_post(id):
    global reddit
    submission = await reddit.submission(id=id)
    await submission.subreddit.load()
    return {
        "id": submission.id,
        "title": submission.title,
        "author": submission.author.name,
        "subreddit": submission.subreddit.display_name
    }


async def render_post(id, template="thread_post.html"):
    global reddit
    template = env.get_template(template)
    submission = await reddit.submission(id=id)
    return {
        "submission": submission,
        "author": submission.author.name,
        "title": submission.title,
        "body": template.render(
            author=submission.author.name,
            title=submission.title,
            body=markdown.markdown(submission.selftext)
        )
    }


async def render_comments(id):
    global reddit
    template = env.get_template("thread_comment.html")
    submission = await reddit.submission(id=id)
    submission.comment_sort = "old"
    comments = await submission.comments()
    return [
        {
            "comment": c,
            "author": c.author.name,
            "body": template.render(
                author=c.author.name,
                body=markdown.markdown(c.body)
            )
        } for c in await comments.list()
        if c.parent_id.startswith("t3") and c.author.name != "AutoModerator"
    ]


async def get_post_text(id):
    global reddit
    submission = await reddit.submission(id=id)
    return submission.selftext


async def get_wiki_text(subreddit, wiki):
    global reddit
    sub = await reddit.subreddit(subreddit)
    await sub.load()
    page = await sub.wiki.get_page(wiki)
    return page.content_md


def scrape_post_ids(text):
    return [get_post_id(x.group()) for x in re.finditer(r"(https:\/\/www.(?:old\.)?reddit\.com[^\s]+)", text)]
