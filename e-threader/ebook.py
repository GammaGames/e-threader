from ebooklib import epub
import subprocess
import re


def create_book_from_thread(meta, post, comments):
    book = epub.EpubBook()

    book.set_identifier(meta["id"])
    book.set_title(meta["title"])
    book.add_author(meta["subreddit"])
    book.set_language("en")

    foreword = epub.EpubHtml(
        title="Foreword",
        file_name="foreword.xhtml",
        lang="en"
    )
    foreword.set_content(post["body"])
    book.add_item(foreword)

    chapters = []
    for comment in comments:
        chapter = epub.EpubHtml(
            title=comment["author"],
            file_name=f"{comment['author']}.xhtml",
            lang="en"
        )
        chapter.set_content(comment["body"])
        chapters.append(chapter)
        book.add_item(chapter)
        book.add_author(comment["author"])

    book.toc = (
        epub.Link("foreword.xhtml", "Foreword", "foreword"),
        (
            epub.Section("Stories"),
            tuple(chapters)
        )
    )
    book.spine = ["nav", foreword] + chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub.write_epub(f"/var/tmp/{meta['id']}.epub", book)
    safe_title = re.sub(r"\[\w+\]", "", meta["title"]).strip()
    subprocess.run([
        "ebook-convert",
        f"/var/tmp/{meta['id']}.epub",
        f"opt/e-threader/out/{meta['id']}.mobi",
        f"--title=\"{safe_title}\""
    ])
    return f"opt/e-threader/out/{meta['id']}.mobi"


def create_book_from_serial(meta, posts):
    book = epub.EpubBook()

    book.set_identifier(meta["id"])
    book.set_title(meta["title"])
    book.set_language("en")
    book.add_author(meta["author"])

    chapters = []
    for post in posts:
        chapter = epub.EpubHtml(
            title=post["title"],
            file_name=f"{post['title']}.xhtml",
            lang="en"
        )
        chapter.set_content(post["body"])
        chapters.append(chapter)
        book.add_item(chapter)

    book.toc = tuple(chapters)
    book.spine = ["nav"] + chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub.write_epub(f"/var/tmp/{meta['id']}.epub", book)
    safe_title = re.sub(r"\[\w+\]", "", meta["title"]).strip()
    match = re.search(r"<(?P<title>.*)>", safe_title)
    if match is not None:
        safe_title = match.group("title")
    subprocess.run([
        "ebook-convert",
        f"/var/tmp/{meta['id']}.epub",
        f"opt/e-threader/out/{meta['id']}.mobi",
        f"--title=\"{safe_title}\""
    ])
    return f"opt/e-threader/out/{meta['id']}.mobi"
