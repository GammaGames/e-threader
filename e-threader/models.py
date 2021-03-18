from pony.orm import *

db = Database(provider="sqlite", filename="/opt/db.sqlite", create_db=True)


class Guild(db.Entity):
    id = PrimaryKey(int, size=64)
    name = Required(str)
    channels = Set(lambda: Channel)


class Channel(db.Entity):
    id = PrimaryKey(int, size=64)
    name = Required(str)
    guild = Required(Guild)
    messages = Set(lambda: Message)


class Message(db.Entity):
    id = PrimaryKey(int, size=64)
    content = Required(str)
    channel = Required(Channel)
    users = Set(lambda: User)


class User(db.Entity):
    id = PrimaryKey(int, size=64)
    name = Required(str)
    email = Optional(str)
    submissions = Set(lambda: Thread)
    subscriptions = Set(lambda: Thread)
    messages = Set(lambda: Message)



class Thread(db.Entity):
    id = PrimaryKey(int)
    submitter = Required(User, reverse="submissions")
    subscribers = Set(lambda: User, reverse="subscriptions")
    link = Required(str)


db.generate_mapping(create_tables=True)
