from dl.ddqn.replay_memory import ReplayMemory
import numpy as np


class BrainDDQN:
    def __init__(self, main_network, target_network, batch_size=32, memory_capacity=10000, gamma=0.99):
        self.num_actions = main_network.output_size  # 取れる行動の数
        self.num_states = main_network.input_size

        self.batch_size = batch_size
        self.memory_capacity = memory_capacity
        self.memory = ReplayMemory(self.memory_capacity)

        self.gamma = gamma  # 時間割引率

        self.main_q_network = main_network
        self.target_q_network = target_network

    def decide_action(self, state, episode):
        """
        ε-greedy法で徐々に最適行動のみを採用する
        """
        epsilon = 0.5 * (1 / (episode + 1))

        if epsilon <= np.random.uniform(0, 1):
            target_action = self.main_q_network.model.predict(state)[0]
            action = np.argmax(target_action)
        else:
            action = np.random.choice(self.num_actions)  # どれかのアクションを返す

        return action

    def replay(self):
        """
        memoryに保存したデータを使用しmainネットワークを更新する
        :return:
        """

        # データが溜まっていない間は実行しない
        if len(self.memory) < self.batch_size:
            return

        # ミニバッチの作成
        # ミニバッチの作成 メモリからミニバッチ分のデータを取り出す
        transitions = self.memory.sample(self.batch_size)
        #        batch = Transition(*zip(*transitions))

        # 教師信号Q(s_t,a_t)を求める
        (states, action_values) = self.get_expected_state_action_values(transitions)

        # 結合パラメータの更新
        self.update_main_q_network(states, action_values)

    def get_expected_state_action_values(self, batch):
        """
        sample batchからmain ネットワークの更新に使用するデータを作成する
        :param batch: memory
        :return: 状態,状態に対して更新するaction_value
        """

        states = np.zeros((self.batch_size, self.num_states))
        action_values = np.zeros((self.batch_size, self.num_actions))

        for i, (state_b, action_b, next_state_b, reward_b) in enumerate(batch):

            if not (next_state_b == np.zeros(state_b.shape)).all(axis=1):
                # 価値の計算
                main_q = self.main_q_network.model.predict(next_state_b)
                next_action = np.argmax(main_q)

                next_action_q = self.target_q_network.model.predict(next_state_b)
                reward = reward_b + self.gamma * next_action_q[0][next_action]

            else:
                reward = reward_b

            states[i] = state_b

            action_values[i] = self.main_q_network.model.predict(state_b)
            action_values[i][action_b] = reward

        return states, action_values

    def update_main_q_network(self, states, action_values):
        # Qネットワークの重みを学習・更新する replay
        if len(self.memory) > self.batch_size:
            self.main_q_network.model.train_on_batch(
                states, action_values)

    def update_target_q_network(self):
        # target ネットワークを更新する
        self.target_q_network.model.set_weights(self.main_q_network.model.get_weights())