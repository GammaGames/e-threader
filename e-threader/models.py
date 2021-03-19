from pony.orm import *

db = Database(provider="sqlite", filename="/opt/db.sqlite", create_db=True)


class Guild(db.Entity):
    id = PrimaryKey(int, size=64)
    name = Required(str)
    channels = Set(lambda: TextChannel)


class BaseChannel(db.Entity):
    id = PrimaryKey(int, size=64)
    messages = Set(lambda: Message)


class TextChannel(BaseChannel):
    name = Required(str)
    guild = Required(Guild)


class DmChannel(BaseChannel):
    user = Required("User")


class Message(db.Entity):
    id = PrimaryKey(int, size=64)
    thread = Optional("Thread")
    content = Required(str)
    channel = Required(BaseChannel)
    users = Set(lambda: User)


class User(db.Entity):
    id = PrimaryKey(int, size=64)
    name = Required(str)
    email = Optional(str)
    dm_channel = Optional(DmChannel)
    submissions = Set(lambda: Thread)
    subscriptions = Set(lambda: Thread)
    messages = Set(lambda: Message)



class Thread(db.Entity):
    id = PrimaryKey(int)
    link = Required(str)
    submitter = Required(User, reverse="submissions")
    subscribers = Set(lambda: User, reverse="subscriptions")
    message = Optional(Message)


db.generate_mapping(create_tables=True)
