from infight import *
# game = Game.create(slack_team="infight", slack_channel="infight")

for game in Game.select():
    print(game)
    if game.state == STATE_CANCELLED:
        print("Already cancelled")
    else:
        game.cancel()

print("ha!")
