from Bot import Bot
from BountyHunter import PlayerAction

class ToBot(Bot):

    def __init__(self, frame_width, frame_height, num_player):
        print("ToBot initialized.")

    def Restarted(self):
        pass

    def Step(self, player_state, frame_data, frame_num):
        return super().Step(player_state, frame_data, frame_num)

    def Done(self, is_winner):
        pass