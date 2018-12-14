import random
from BountyHunter import PlayerAction

class Bot(object):
    """
    Base bot class.
    """

    def __init__(self, frame_width, frame_height, num_player):
        print("Basic bot initialized.")

    def Restarted(self):
        """
        Called when game is restarted.
        :return:
        """
        pass

    def Step(self, player_state, frame_data, frame_num):
        """
        Called every frame. This method gives a bot the opportunity to evaluate its current frame state
        and return a response.

        :param player_state: Holds the current player state for this frame.
        :param frame_data: Frame pixel data (self.frame_width, self.frame_height, 3)
        :param frame_num: Current frame number.
        :return: PlayerAction: a player action executed next frame.
        """
        return PlayerAction(random.uniform(0.0, 1.0), random.uniform(0.0, 1.0))

    def Done(self, is_winner):
        """
        Called when game is over.
        :param is_winner: True, if this bot has won the match.
        :return:
        """
        pass
