import json
import time
from pathlib import Path
import os
import numpy as np

from api.actions import Move, Push, Idle, Action, Jump
from bots import BaseBot

### GPU CUDA CONFIG
os.environ['CUDA_CACHE_DISABLE'] = '0'

os.environ['HOROVOD_GPU_ALLREDUCE'] = 'NCCL'


os.environ['TF_GPU_THREAD_MODE'] = 'gpu_private'
# os.environ['TF_GPU_THREAD_COUNT'] = '1'

os.environ['TF_USE_CUDNN_BATCHNORM_SPATIAL_PERSISTENT'] = '1'

os.environ['TF_ADJUST_HUE_FUSED'] = '1'
os.environ['TF_ADJUST_SATURATION_FUSED'] = '1'
os.environ['TF_ENABLE_WINOGRAD_NONFUSED'] = '1'

os.environ['TF_SYNC_ON_FINISH'] = '0'
os.environ['TF_AUTOTUNE_THRESHOLD'] = '2'
os.environ['TF_DISABLE_NVTX_RANGES'] = '1'
###

import tensorflow as tf
from tensorflow import keras
from keras import layers


tf.compat.v1.disable_eager_execution()

EPOCHS = 1000
SHOW_EVERY = 50

DECAY_FACTOR = 0.999
y = 0.95

# Double Deep Q... Coming Soon
GAMMA = 0.95
TAU = 0.08
BATCH_SIZE = 4

IS_TRAINING = True
#IS_TRAINING = False


class CrazeeSecret(BaseBot):
    name = 'Secret Sauce'
    say = 'Learning how To get Better'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = 'secret_00'

        self.total_epoch = 0
        self.reset()

        self.r_sum = 0
        self.avg_loss = 0
        self.epsilon = 0.5
        self.step = 0
        self.model_history = None
        self.illegal_action = False
        self.previous_inputs = None

        self.model = None
        self.target_model = None

        self.last_score = args[0].get_score(self.bot_id)
        self.inputs = self.gen_inputs(api=args[0])

        self.actions = self.possible_moves

        self.input_amount = len(self.inputs)
        self.output_amount = len(self.actions)

        # double Q learning
        self.double_q = False
        self.input_history = []
        self.output_history = []
        self.action_history = []
        self.reward_history = []

        if not self.load():
            self.machine_learning_init()

    def bot_logic(self, api):
        if IS_TRAINING:
            return self.train_model(api)
        else:
            return self.trained_action(api)

    def train_model(self, api):
        self.inputs = self.gen_inputs(api)
        action = self.q_learning(api)
        return action

    def trained_action(self, api):
        outputs = self.model.predict(keras.utils.normalize(self.inputs))
        a = np.argmax(outputs[0][:len(self.actions)])
        action = self.smart_do_action(a, api)
        # print(outputs)
        if action is None:
            self.illegal_action = True
            return [0, 0]
        return action

    def gen_inputs(self, api):
        inputs = api.players_location.flatten()
        inputs = np.append(inputs, api.board.flatten())
        return inputs

    def machine_learning_init(self):
        policy = keras.mixed_precision.Policy('mixed_float16')
        keras.mixed_precision.set_global_policy(policy)

        self.model = keras.Sequential([
                layers.InputLayer(batch_input_shape=(1, self.input_amount)),
                layers.Dense(32, activation=tf.nn.relu),
                #layers.Dense(16, activation=tf.nn.relu),
                layers.Dense(self.output_amount, activation=tf.nn.softmax)
            ])

        self.model.compile(optimizer=keras.optimizers.Adam(), loss='mse')

    def q_learning(self, api):
        if self.model is None:
            raise Exception("NO MODEL EXCEPTION")

        if np.random.random() < self.epsilon:
            outputs = None
            a = np.random.randint(0, len(self.actions))
        else:
            outputs = self.model.predict(keras.utils.normalize(self.inputs))
            a = np.argmax(outputs[0][:len(self.actions)])

        #game update/ q_learning
        if self.previous_inputs is not None:

            reward = self.reward_calc(api)

            target = reward + y * np.max(self.model.predict(keras.utils.normalize(self.previous_inputs)))
            target_vec = self.model.predict(keras.utils.normalize(self.inputs))[0]
            target_vec[a] = target
            t_in = keras.utils.normalize(self.inputs)
            t_out = target_vec.reshape(-1, self.output_amount)
            self.model_history = self.model.fit(t_in, t_out, epochs=1, verbose=0)

            self.r_sum += reward

        self.previous_inputs = self.inputs.copy()
        action = self.smart_do_action(a, api)
        if action is None:
            self.illegal_action = True

            return self.q_learning(api)
            #return [0, 0]

        return action

    @property
    def possible_moves(self):
        return np.array([[0, 0],
                         [0, 1],
                         [1, 0],
                         [1, 1],
                         [0, -1],
                         [-1, 0],
                         [-1, -1],
                         [1, -1],
                         [-1, 1],
                         ])

    def smart_do_action(self, index, api):
        action = self.actions[index]
        #print(f"bot {self.bot_id} wants to do {action}")
        if api.check_valid_move(self.bot_id, action):
            return action
        return None

    def reward_calc(self, api):
        # reward = delta score from last turn, maybe add 1 if it tacks a point away from an oponnet?
        my_score = api.get_score(self.bot_id)
        reward = my_score - self.last_score
        if self.illegal_action:
            reward -= 2
            self.illegal_action = False
        self.last_score = my_score
        return reward / 100

    def save(self, name=None):
        if name is None:
            name = self.name
        # global epoch
        # epoch += 0.1
        data = {
                'bot_id': name,
                'epsilon': self.epsilon,
                "r_sum": self.r_sum,
                'epoch': self.total_epoch + 0.1
                }
        with open(f'{name}.json', 'w') as fp:
            json.dump(data, fp)
        self.model.save_weights(f'{name}.h5')
        print(f"model for unit {name} saved")
        # self.model.summary()

    def load(self, name=None):
        if name is None:
            name = self.name
        # global r_avg_list
        file = f'{name}.json'
        if not Path(file).is_file():
            print("NOFI LE TO LOAD BY NAME:", file)
            return False
        with open(file, 'r') as fp:
            data = json.load(fp)
            self.epsilon = data['epsilon']
            self.r_sum = 0
            self.total_epoch = data['epoch']
            #r_avg_list.append(data['r_sum'])
        #del self.model
        self.machine_learning_init() #if not self.double_q else self.double_machine_learning_init()
        self.model.load_weights(f'{name}.h5')
        # if self.double_q:
        #     self.target_model.load_weights(f'{name}.h5')
        print(f"model for unit {name} loaded")
        return True

    def reset(self):
        self.r_sum = 0
        self.avg_loss = 0
        self.epsilon = 0.5
        self.step = 0
        self.model_history = None
        self.illegal_action = False
        self.previous_inputs = None
        self.last_score = 1
        self.total_epoch += 0.1
        # print(f"model was {self.name} loaded from last game")
        return True


# BOT = CrazeeSecret


def ping():
    return time.time()


def pong(ping_):
    return time.time() - ping_


def train(epochs=EPOCHS, show_every=SHOW_EVERY):
    print("Starting Training...")
    last_bots = None
    for match in range(epochs):
        debug_console = match % show_every == 0
        # run game
        game_time = ping()
        game = logic.game.Game(bots=[CrazeeSecret]*4, map_size=(5, 5), debug=False, reuse_bots=last_bots)
        for i in range(game.max_turns):
            game.turn = i
            if debug_console:
                pass
                #print(f"Turn:{i}")
            game.api.update(game)
            game.turn_handler()
        last_bots = game.players_bots
        game_len = pong(game_time)
        if debug_console:
            save_bots(game.players_bots, game.api)
        print(f"Game {match+1}/{epochs}: {game_len}s")


def save_bots(bots, api):
    scores = []
    cbots = []
    for bot in bots:
        if isinstance(bot, CrazeeSecret):
            cbots.append(bot)
            scores.append(api.get_score(bot.bot_id))
    # find bot with best score and save them.   or mix the best 2
    index_sort = np.argsort(scores, kind='heapsort')
    a, b = (cbots[index_sort[-1]], cbots[index_sort[-2]])
    a.model.set_weights(combine_bots(a, b))
    a.epsilon *= DECAY_FACTOR
    a.save()


def combine_bots(a, b):
    a_weights = np.array(a.model.get_weights())
    b_weights = np.array(b.model.get_weights())
    #print(f"a_weights_split: {a_weights.shape} \r\n")
    #print(f"b_weights_split: {np.array_split(b_weights, 2)[0].shape} \r\n")
    ab_weights = np.concatenate((np.array_split(a_weights, 2)[0], np.array_split(b_weights, 2)[1]))
    #print(f"ab_weights: {ab_weights}")
    return ab_weights


if IS_TRAINING:
    train()