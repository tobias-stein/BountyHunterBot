import random
import numpy as np
import atexit

from Bot import Bot
from BountyHunter import PlayerAction
from constants import *

# keras/tensorflow stuff
import tensorflow as tf

from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, Dropout, concatenate, Flatten, CuDNNLSTM, Conv2D, TimeDistributed, LSTM

from keras import backend as K

def atexit_handler():
    if ToBot.shared_session is not None:
        ToBot.shared_session.close()
        ToBot.shared_session = None

# make sure to close shared tensorflow session
atexit.register(atexit_handler)


class ToBot(Bot):

    # shared tensorflow session
    shared_session = None

    # model inputs
    in_frames = Input(shape=(TIME_STEPS, FRAME_SIZE_X, FRAME_SIZE_Y, FRAME_DEPTH))
    in_states = Input(shape=(TIME_STEPS, STATES_DIM))
    in_actions = Input(shape=(TIME_STEPS, ACTIONS_DIM))

    # model outputs
    out_action_move = None
    out_action_turn = None

    def __init__(self, frame_width, frame_height, num_player):

        # probability that bot will make a random move
        self.exploration_rate = 0.2

        self.memory = {}
        self.last_action = PlayerAction(0.0, 0.0)
        self.ResetMemory()

        # initialize shared session
        if ToBot.shared_session is None:
            # create NN model
            model = ToBot.CreateModel()
            print(model.summary())
            # create session
            ToBot.shared_session = tf.Session(graph=K.get_session().graph)
            # initialize graph
            ToBot.shared_session.run(tf.global_variables_initializer())

        print("ToBot initialized.")

    def ResetMemory(self):
        self.memory = {'last_actions': [], 'player_states': [], 'frame_data': [], 'rewards': []}
        self.last_action = PlayerAction(0.0, 0.0)

    def CreateModel():

        # convolution
        conv0 = TimeDistributed(
            Conv2D(filters=16, kernel_size=(2, 2), strides=(2, 2), padding='same', activation=tf.nn.relu))(ToBot.in_frames)
        conv1 = TimeDistributed(
            Conv2D(filters=32, kernel_size=(5, 5), strides=(2, 2), padding='same', activation=tf.nn.relu))(conv0)
        conv2 = TimeDistributed(
            Conv2D(filters=32, kernel_size=(2, 2), strides=(4, 4), padding='same', activation=tf.nn.relu))(conv1)

        flat0 = TimeDistributed(Flatten())(conv2)

        # lstm
        lstm0 = LSTM(units=TIME_STEPS)(flat0)
        lstm1 = LSTM(units=TIME_STEPS)(ToBot.in_states)
        lstm2 = LSTM(units=TIME_STEPS)(ToBot.in_actions)

        # merge
        conc0 = concatenate([lstm0, lstm1, lstm2])

        # dense
        dens0 = Dense(units=256, activation=tf.nn.relu)(conc0)

        # output
        ToBot.out_action_move = Dense(units=1, activation=tf.nn.sigmoid)(dens0)
        ToBot.out_action_turn = Dense(units=1, activation=tf.nn.tanh)(dens0)

        # return model
        return Model(
            inputs=[ToBot.in_actions, ToBot.in_states, ToBot.in_frames],
            outputs=[ToBot.out_action_move, ToBot.out_action_turn]
        )

    def Restarted(self):
        # clear last memory
        self.ResetMemory()

    def Step(self, player_state, frame_data, frame_num):

        # collect data for training
        self.memory['last_actions'].append([self.last_action.move, self.last_action.turn])
        self.memory['player_states'].append([
            player_state.playerPositionX,
            player_state.playerPositionY,
            player_state.playerRotation,
            player_state.playerPocketLoad,
            player_state.playerStashLoad,
            player_state.playerDead])
        self.memory['frame_data'].append(frame_data)
        #self.memory['rewards'].append(player_state.playerReward)
        # clipped reward
        self.memory['rewards'].append(max(-1.0, min(player_state.playerReward, 1.0)))

        t_samples = max(1, min(frame_num, TIME_STEPS))

        last_t_actions = np.asarray(self.memory['last_actions'][-t_samples:])
        last_t_states = np.asarray(self.memory['player_states'][-t_samples:])
        last_t_frames = np.asarray(self.memory['frame_data'][-t_samples:])

        # zero pad missing samples
        pad = TIME_STEPS - t_samples
        if pad > 0:
            last_t_actions = np.append(last_t_actions, np.zeros((pad, ACTIONS_DIM)))
            last_t_states = np.append(last_t_states, np.zeros((pad, STATES_DIM)))
            last_t_frames = np.append(last_t_frames, np.zeros((pad, FRAME_SIZE_X, FRAME_SIZE_Y, FRAME_DEPTH)))

        # reshape data to match time-series format expected by model
        last_t_actions = last_t_actions.reshape((1, TIME_STEPS, ACTIONS_DIM))
        last_t_states = last_t_states.reshape((1, TIME_STEPS, STATES_DIM))
        last_t_frames = last_t_frames.reshape((1, TIME_STEPS, FRAME_SIZE_X, FRAME_SIZE_Y, FRAME_DEPTH))

        # perform action
        if random.uniform(0, 1) < self.exploration_rate:
            # explore, use random move
            action = PlayerAction(random.uniform(0.0, 1.0), random.uniform(-1.0, 1.0))
        else:
            assert ToBot.shared_session is not None
            # exploit, use policy
            move, turn = ToBot.shared_session.run(
                [ToBot.out_action_move, ToBot.out_action_turn],
                {
                    ToBot.in_actions: last_t_actions,
                    ToBot.in_states: last_t_states,
                    ToBot.in_frames: last_t_frames
                }
            )

            move = move[0][0]
            turn = turn[0][0]

            action = PlayerAction(move, turn)

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

