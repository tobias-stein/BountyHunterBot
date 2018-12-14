from BountyHunter import Game

def LoadBotClass(bot_name):
    return getattr(__import__(bot_name), bot_name)

def main():

    # create new game instance
    game = Game(2)

    # create bots
    bots = [
        LoadBotClass('ToBot')(game.frame_render_width, game.frame_render_height, 2),
        LoadBotClass('ToBot')(game.frame_render_width, game.frame_render_height, 2)
    ]

    # signal game is restarted
    for i in range(len(bots)):
        bots[i].Restarted()

    frame_num = 0
    winner = game.Step()

    # while game is not over, keep running
    while winner < 0:
        frame_num += 1

        # step bots
        for i in range(len(bots)):
            pid = game.player_id[i]
            game.player_action[pid] = bots[i].Step(game.player_state[pid], game.frame_buffer, frame_num)

        # step game
        winner = game.Step()

    print(f"Bot {winner} won the match.")

    # signal game is over
    for i in range(len(bots)):
        bots[i].Done(game.player_id[i] == winner)

    # terminate game
    game.Terminate()


if __name__ == "__main__":
    main()