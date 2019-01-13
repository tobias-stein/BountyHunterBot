from BountyHunter import Game
from constants import *
import random
import cv2

random.seed(RANDOM_SEED)

def LoadBotClass(bot_name):
    return getattr(__import__(bot_name), bot_name)

def main():

    # create new game instance
    game = Game(NUM_PLAYERS, RANDOM_SEED)
    
    # create bots
    bots = [
        LoadBotClass('ToBot')(FRAME_SIZE_X, FRAME_SIZE_Y, NUM_PLAYERS),
        LoadBotClass('ToBot')(FRAME_SIZE_X, FRAME_SIZE_Y, NUM_PLAYERS),
        LoadBotClass('ToBot')(FRAME_SIZE_X, FRAME_SIZE_Y, NUM_PLAYERS),
        LoadBotClass('ToBot')(FRAME_SIZE_X, FRAME_SIZE_Y, NUM_PLAYERS)
    ]

    game_count = 0


    while True:

        try:
            # restart game
            game.Restart()
            game_count += 1

            print(f"Run game {game_count} ...")

            # signal game is restarted
            for i in range(len(bots)):
                bots[i].Restarted()

            frame_num = 0
            winner = game.Step()

            # while game is not over, keep running
            while winner < 0:
                frame_num += 1
                frame = cv2.resize(game.frame_buffer, (FRAME_SIZE_X, FRAME_SIZE_Y))

                # step bots
                for i in range(len(bots)):

                    pid = game.player_id[i]
                    # set player action
                    game.player_action[pid] = bots[i].Step(game.player_state[pid], frame, frame_num)

                # step game
                winner = game.Step()

                # render
                game.RenderGameState()
                #game.DumpGameState()

            #print(f"Bot {winner} won the match.")

            # signal game is over
            print("Game done, save train data...")
            for i in range(len(bots)):
                bots[i].Done(game.player_id[i] == winner)

        except KeyboardInterrupt:
            # terminate game
            game.Terminate()
            print("User interrupted data generation process.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)