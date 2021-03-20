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
    print("Reddit login:", me)


async def get_post_id(url):
    match = re.search(r".*reddit.com\/(?:r\/\w+\/)?(?:comments\/)?(?P<url>\w+)", url)
    if match is not None:
        return match.group("url")


async def get_post(id):
    global reddit
    submission = await reddit.submission(id=id)
    await submission.subreddit.load()
    return {
        "id": submission.id,
        "title": submission.title,
        "subreddit": submission.subreddit.display_name
    }


async def render_post(id):
    global reddit
    template = env.get_template("post.html")
    submission = await reddit.submission(id=id)
    return template.render(
        title=submission.title,
        body=markdown.markdown(submission.selftext)
    )


async def render_comments(id):
    global reddit
    template = env.get_template("comment.html")
    submission = await reddit.submission(id=id)
    submission.comment_sort = "old"
    comments = await submission.comments()
    # comments = [
    #     {
    #         "comment": c,
    #         "author": c.author.name,
    #         "body": markdown.markdown(c.body)
    #     } for c in await comments.list()
    #     if c.parent_id.startswith("t3")
    # ]
    # comments = [
    #     c for c in submission.comments.list()
    #     if c.parent_id.startswith("t3")
    # ]
    # return [r for r in comments]
    return [
        {
            "author": c.author.name,
            "body": template.render(
                author=c.author.name,
                body=markdown.markdown(c.body)
            )
        } for c in await comments.list()
        if c.parent_id.startswith("t3")
    ]
