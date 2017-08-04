from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase

STATE_NEW = 1
STATE_PLAYING = 2
STATE_FINISHED = 3
STATE_CANCELLED = 4

db = SqliteExtDatabase('my_database.db')


class BaseModel(Model):
    class Meta:
        database = db


class Game(BaseModel):
    slack_team = TextField(null=True)
    slack_channel = TextField(null=True)
    state = IntegerField(default=STATE_NEW)

    board_x = IntegerField(null=True, default=5)
    board_y = IntegerField(null=True, default=5)

    def cancel(self):
        self.state = STATE_CANCELLED
        self.save()


class Player(BaseModel):
    game = ForeignKeyField(Game, related_name='player_games')
    slack_user_id = TextField()


class Move(BaseModel):
    game = ForeignKeyField(Game, related_name='game_moves')
    player = ForeignKeyField(Player, related_name='game_players')


db.connect()
try:
    db.create_tables([Game, Player, Move])
    print("Tables created")
except Exception:
    print("Tables not created")
