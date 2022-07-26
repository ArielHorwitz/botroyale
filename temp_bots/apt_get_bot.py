import copy
import os.path
import random
import numpy as np
from api.actions import Move, Push, Idle, Action, Jump
from bots import BaseBot
from util.hexagon import Hexagon, Hex
from api.bots import CENTER
from logic.state import State
from time import perf_counter


class AptGetBot(BaseBot):
    NAME = "apt-get bot"
    COLOR_INDEX = 69
    CENTER_TILE = CENTER
    SPRITE = 'petals'
    TESTING_ONLY = True

    def __init__(self, id: int, *args, **kwargs):
        super().__init__(id)
        self.obs_low = None
        self.obs_high = None
        self.max_map_size = None
        self.q_learning = None

    def setup(self, state: State):

        def _init_observations(map_size, ap_range):
            observation_space_low = []
            observation_space_high = []
            observation = []
            for pos in state.walls | state.pits:
                observation.extend(pos.qr)
                observation_space_low.extend((-map_size[0], -map_size[1]))
                observation_space_high.extend(map_size)
            for pos in state.positions:
                observation.extend(pos.qr)
                observation_space_low.extend((-map_size[0], -map_size[1]))
                observation_space_high.extend(map_size)
            for ap in state.ap:
                observation.append(ap)
                observation_space_low.append(ap_range[0])
                observation_space_high.append(ap_range[1])
            for ap in state.round_ap_spent:
                observation.append(ap)
                observation_space_low.append(ap_range[0])
                observation_space_high.append(ap_range[1])
            return observation, observation_space_low, observation_space_high

        self.max_map_size = [state.death_radius - 2] * 2
        _, self.obs_low, self.obs_high = _init_observations(self.max_map_size, (0, self.max_ap))
        env = Environment.from_state(state, self.obs_low, self.obs_high)
        self.q_learning: QLearning = QLearning(self.id, env, is_learning=False)

    def poll_action(self, state: State):
        # current_bot_id = state.round_remaining_turns[0]
        env = Environment.from_state(state, self.obs_low, self.obs_high)
        action = self.q_learning.play_step(env)
        # actions = env.get_all_legal_actions(self.id)
        # random_action = random.choice(actions) if len(actions) > 0 else Idle()
        # print(f"AP: {env.ap}")
        # print(f"round_remaining_turns: {env.round_remaining_turns}")
        return action


BOT = AptGetBot


class Environment(State):

    def __init__(self, obs_low, obs_high,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.observation_space_low = obs_low
        self.observation_space_high = obs_high
        self.reward_range = (-1, 1)

    def step(self, action: Action, unit_id: int):
        new_state = self.apply_action(action)
        self.update_from_state(new_state)
        return self.observation, self.get_score(unit_id), self.game_over

    def get_all_legal_actions(self, unit_id: int):
        actions = []
        pos: Hexagon = self.positions[unit_id]
        for neighbor in pos.neighbors:
            move = Move(neighbor)
            if self.check_legal_action(unit_id, move) and neighbor not in self.pits:
                actions.append(move)
            push = Push(neighbor)
            if self.check_legal_action(unit_id, push):
                actions.append(push)
        for jump_option in set(pos.ring(2)):
            jump = Jump(jump_option)
            if self.check_legal_action(unit_id, jump) and jump_option not in self.pits:
                actions.append(jump)
        return actions

    @staticmethod
    def get_all_theoretical_actions(pos: Hexagon = Hex(0, 0)):
        actions = [Idle()]
        for neighbor in pos.neighbors:
            actions.extend((Move(neighbor), Push(neighbor)))
        for jump_option in set(pos.ring(2)):
            actions.append(Jump(jump_option))
        return actions

    def get_theoretical_action(self, unit_id: int, action_id: int):
        pos: Hexagon = self.positions[unit_id]
        action = self.get_all_theoretical_actions(pos)[action_id]
        # if self.check_legal_action(unit_id, action):
        return action

    def get_score(self, unit_id: int):
        return self.reward_range[1] if unit_id == self.winner else self.reward_range[0]

    @property
    def observation(self):
        # observation should have world (walls, pits) V
        # observation should have  positions V
        # observation should have ap V
        # observation should have round_remaining_turns V
        observation = []
        for pos in self.walls | self.pits:
            observation.extend(pos.xy)
        for pos in self.positions:
            observation.extend(pos.xy)
        for ap in self.ap:
            observation.append(ap)
        for ap in self.round_ap_spent:
            observation.append(ap)
        return np.asarray(observation)

    @property
    def action_space(self):
        return self.get_all_theoretical_actions()

    @staticmethod
    def from_state(state: State, obs_low: list, obs_high: list):
        return Environment(
            obs_low=obs_low,
            obs_high=obs_high,
            death_radius=state.death_radius,
            positions=state.positions,
            walls=state.walls,
            pits=state.pits,
            alive_mask=state.pits,
            ap=state.ap,
            round_ap_spent=state.round_ap_spent,
            round_remaining_turns=state.round_remaining_turns,
            step_count=state.step_count,
            turn_count=state.turn_count,
            round_count=state.round_count
                           )

    def update_from_state(self, state: State):
        self.death_radius = state.death_radius,
        self.positions = state.positions,
        self.walls = state.walls,
        self.pits = state.pits,
        self.alive_mask = state.pits,
        self.ap = state.ap,
        self.round_ap_spent = state.round_ap_spent,
        self.round_remaining_turns = state.round_remaining_turns,
        self.step_count = state.step_count,
        self.turn_count = state.turn_count,
        self.round_count = state.round_count


class QLearning:
    # TODO: Add Saving Stats on best game
    def __init__(self, bot_id: int, env: Environment, is_learning=True,
                 learning_rate=0.1, discount=0.95, epsilon=0.7,
                 epsilon_decay=0.999, episodes=10000, show_every=1000):
        self.max_r = None
        self.is_learning = is_learning
        self.bot_id = bot_id
        self.episodes = episodes
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.learning_rate = learning_rate
        self.discount = discount
        self.show_every = show_every

        self.ep_rewards = []
        self.aggr_ep_rewards = {'ep': [], 'avg': [], 'min': [], 'max': []}

        self.Q = None
        self._init_q_table(env)

        if is_learning:
            self._init_learning()

    def _init_q_table(self, env: Environment):

        self.q_scaled_size = [40] * len(env.observation_space_high)

        self.obs_high = self.normalize_arr(env.observation_space_high)
        self.obs_low = self.normalize_arr(env.observation_space_low)
        self.q_scaled_chunk_size = (self.obs_high - self.obs_low) / self.q_scaled_size

        if not self.is_learning or not self.load():
            self.Q = np.random.uniform(low=-1.0, high=1.0,
                                       size=(len(self.q_scaled_chunk_size) * 40, len(env.action_space)))

    def _init_learning(self):
        self.r_sum = 0
        self.max_r = float('-inf')

    def play_game(self, env: Environment):
        self.learn_step(env) if self.is_learning else self.play_step(env)

    def play_step(self, env: Environment):
        state = self.get_normalized_state(env.observation)
        print(f"Q: {self.Q.shape}")
        print(f"state: {len(state)}")
        print(f"Q[state, :]: {self.Q[state, :].shape}")
        action_index = np.argmax(self.Q[state, :])
        print(f"action_index: {action_index}")
        return env.get_theoretical_action(self.bot_id, action_index)

    def learn_step(self, env: Environment):
        state = self.get_normalized_state(env.observation)

        if random.random() > self.epsilon:
            # choose the selected action
            action_index = np.argmax(self.Q[state, :])
        else:
            # Choose a random action
            action_index = random.randint(0, len(env.action_space)-1)

        # Get new state & reward from environment
        action = env.get_theoretical_action(self.bot_id, action_index)
        next_state, reward, done = env.step(action, self.bot_id)

        next_state = self.get_normalized_state(next_state)
        max_future_q = np.max(self.Q[next_state, :])
        current_q = self.Q[state, action_index]
        new_q = (1 - self.learning_rate) * current_q + self.learning_rate * \
                (reward + self.discount * max_future_q)

        # Update Q table with new Q value
        self.Q[state, action_index] = new_q
        self.r_sum += reward

        if done:
            if self.r_sum > self.max_r:
                self.max_r = self.r_sum
                self.save('best')
            self.ep_rewards.append(self.r_sum)
            self.epsilon *= self.epsilon_decay
        return action

    @staticmethod
    def normalize_arr(state, minn=-1000, maxx=1000):
        s = np.clip(state, minn, maxx)
        return s

    def get_normalized_state(self, state):
        d_state = (state - self.obs_low) / self.q_scaled_chunk_size
        return tuple(d_state.astype(int))

    def save(self, name='', q=None):
        np.save(f'{"default" if name is None else name}-{self.r_sum}-{self.bot_id}.npy', self.Q if q is None else q)
        print(f"Saved {name} Q Data")

    def load(self, name=None):
        if self.is_learning and name is None:
            return False
        if os.path.exists(f'{name}.npy'):
            self.Q = np.load(f'{"best" if name is None else name}.npy')
            print(f"Loaded {name} Q Data")
            return True
        return False

    def plot_history(self):
        from matplotlib import pyplot as plt
        plt.plot(self.aggr_ep_rewards['ep'], self.aggr_ep_rewards['avg'], label="Avg")
        plt.plot(self.aggr_ep_rewards['ep'], self.aggr_ep_rewards['min'], label="Min")
        plt.plot(self.aggr_ep_rewards['ep'], self.aggr_ep_rewards['max'], label="Max")
        plt.legend(loc=4)
        plt.show()


