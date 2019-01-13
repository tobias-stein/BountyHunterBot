import random
import numpy as np

from Bot import Bot
from BountyHunter import PlayerAction
from constants import *

# keras/tensorflow stuff
import tensorflow as tf

from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, Dropout, Concatenate, Flatten, CuDNNLSTM, Conv2D, TimeDistributed

class ToBot(Bot):

    def __init__(self, frame_width, frame_height, num_player):

        # probability that bot will make a random move
        self.exploration_rate = 0.2

        # create NN model
        #self.model = self._CreateModel()
        #self.model.summary()

        self.memory = {}
        self.last_action = None
        self.ResetMemory()

        print("ToBot initialized.")

    def ResetMemory(self):
        self.memory = {'last_actions': [], 'player_states': [], 'frame_data': [], 'rewards': []}
        self.last_action = None

    def _CreateModel(self):
        # create model inputs
        # move, turn
        self.input_last_action = Input(shape=(2,), name="IN_last_action")
        # posX, posY, angle, pocket, stash, dead
        self.input_state = Input(shape=(6,), name="IN_player_state")
        # frame data
        self.input_frame = Input(shape=(FRAME_SIZE_X, FRAME_SIZE_Y, FRAME_DEPTH,), name="IN_frame")

        # apply some convolution on frame input
        conv0 = Conv2D(filters=16, kernel_size=(8, 8), strides=(4, 4), padding='same', activation=tf.nn.relu)(self.input_frame)
        conv1 = Conv2D(filters=32, kernel_size=(4, 4), strides=(2, 2), padding='same', activation=tf.nn.relu)(conv0)

        time0 = TimeDistributed(conv1)
        # apply lstm layer to frame data
        lstm0 = CuDNNLSTM(units=32, return_sequences=False, name="lstm_frame")(time0)
        # apply lstm to last action data
        lstm1 = CuDNNLSTM(units=32, return_sequences=False, name="lstm_last_action")(self.input_last_action)
        # apply lstm to player state data
        lstm2 = CuDNNLSTM(units=32, return_sequences=False, name="lstm_player_state")(self.input_state)

        # concatenate hidden lstm output
        conc0 = Concatenate([lstm0, lstm1, lstm2])
        # add another dense layer
        dens1 = Dense(units=256)(conc0)

        # ouput (scaled between [0; +1])
        self.output_action_move = Dense(units=1, activation=tf.nn.sigmoid, name="OUT_action_move")(dens1)
        # ouput (scaled between [-1; +1])
        self.output_action_turn = Dense(units=1, activation=tf.nn.tanh, name="OUT_action_turn")(dens1)

        # return model
        return Model(inputs=[self.input_last_action, self.input_state, self.input_frame], outputs=[self.output_action_move, self.output_action_turn])

    def Restarted(self):
        # clear last memory
        self.ResetMemory()

    def Step(self, player_state, frame_data, frame_num):

        # collect data for training
        if self.last_action is not None:
            self.memory['last_actions'].append(self.last_action)
            self.memory['player_states'].append(player_state[:-1])
            self.memory['frame_data'].append(frame_data)
            self.memory['rewards'].append(player_state[-1])

        # perform random action
        action = PlayerAction(random.uniform(0.0, 1.0), random.uniform(-1.0, 1.0))
        self.last_action = action

        return action

    def Done(self, is_winner):
        # train model with current collected memory
        self.train(is_winner)

    def train(self, is_winner):

        actions = np.asarray(self.memory['last_actions'])
        states = np.asarray(self.memory['player_states'])
        frames = np.asarray(self.memory['frame_data'])

        # get the discounted rewards
        discounted_rewards = self.discounted_rewards(self.memory['rewards'], normalize=True)


    def discount_rewards(self, r, normalize=False):
        discounted_rewards = np.zeros_like(r)
        running_reward = 0

        for t in reversed(range(0, len(r))):
            running_reward = running_reward* DISCOUNT_FACTOR + r[t]
            discounted_rewards[t] = running_reward

        if normalize:
            discounted_rewards -= np.mean(discounted_rewards)
            discounted_rewards /= np.std(discounted_rewards)

        return discounted_rewards

