import psycopg2
from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase

AP_TICK_RATE = 30

GAME_STATE_NEW = 1
GAME_STATE_PLAYING = 2
GAME_STATE_FINISHED = 3
GAME_STATE_CANCELLED = 4

PLAYER_STATE_ALIVE = 1
PLAYER_STATE_DEAD = 2

PLAYER_STARTING_HEALTH = 3

ACTION_TYPE_MOVE = 1
ACTION_TYPE_ATTACK = 2
ACTION_TYPE_EXPAND_RANGE = 3

if False:
    db = PostgresqlDatabase('postgres',
                            host='localhost', port=32768, user='postgres', password='postgres',
                            autocommit=True, autorollback=True)
else:
    db = SqliteExtDatabase('my_database.db')


class BaseModel(Model):
    class Meta:
        database = db


class Team(BaseModel):
    slack_domain = TextField(null=True)
    slack_img = TextField(null=True)
    slack_access_token = TextField(null=True)
    slack_team_name = TextField(null=True)
    slack_team_id = TextField(null=True)
    slack_webhook_url = TextField(null=True)
    slack_bot_id = TextField(null=True)
    slack_bot_access_token = TextField(null=True)

    @classmethod
    def get_current_game(cls):
        pass


class Game(BaseModel):
    slack_team = ForeignKeyField(Team, related_name='team_games')
    slack_channel_id = TextField(null=True)
    slack_channel_name = TextField(null=True)
    state = IntegerField(default=GAME_STATE_NEW)

    ap_tick_seconds = AP_TICK_RATE

    board_x = IntegerField(null=True, default=5)
    board_y = IntegerField(null=True, default=5)

    def cancel(self):
        self.state = GAME_STATE_CANCELLED
        self.save()


class Player(BaseModel):
    game = ForeignKeyField(Game, related_name='game_players')
    state = IntegerField(default=PLAYER_STATE_ALIVE)
    slack_user_id = TextField()
    name = TextField(null=True)
    img = TextField(null=True)
    hp = IntegerField(default=PLAYER_STARTING_HEALTH, null=True)
    ap = IntegerField(default=10, null=True)
    range = IntegerField(default=1)
    x = IntegerField(null=True)
    y = IntegerField(null=True)


class Move(BaseModel):
    player = ForeignKeyField(Player, related_name='player_moves')
    action = IntegerField()


db.connect()
try:
    db.create_tables([Game, Player, Move, Team])
    print("Tables created")
except Exception:
    print("Tables not created")
