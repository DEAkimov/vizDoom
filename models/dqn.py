import torch
from torch import nn
import torch.nn.functional as fun
import numpy as np


class DQN(nn.Module):
    def __init__(self, scenario, n_actions, epsilon=1.0):
        super(DQN, self).__init__()
        self.scenario = scenario
        self.n_actions = n_actions
        self.epsilon = epsilon
        if scenario == 'basic':
            self.conv1 = nn.Conv2d(1, 8, kernel_size=6, stride=3)
            self.conv2 = nn.Conv2d(8, 8, kernel_size=3, stride=2)

            self.fc1 = nn.Linear(192, 128)
            self.fc2 = nn.Linear(128, n_actions)
        else:
            self.conv1 = nn.Conv2d(3, 32, kernel_size=8, stride=4)
            self.conv2 = nn.Conv2d(32, 64, kernel_size=4, stride=2)
            self.conv3 = nn.Conv2d(64, 64, kernel_size=3)

            self.fc1 = nn.Linear(2560, 512)
            self.fc2 = nn.Linear(512, n_actions)

    def forward(self, x_screens, hidden):
        """Forward

        :param x_screens: screen batch of shape [batch, time, channels, height, width]
        :param hidden: fake lstm-state
        :return: estimated q-values of shape [batch*time, n_actions],
        """
        batch, time = x_screens.shape[:2]
        chw = x_screens.shape[2:]
        x_screens = x_screens.contiguous().view(batch*time, *chw)
        if self.scenario == 'basic':
            x = fun.relu(self.conv1(x_screens))
            x = fun.relu(self.conv2(x))
        else:
            x = fun.relu(self.conv1(x_screens))
            x = fun.relu(self.conv2(x))
            x = fun.relu(self.conv3(x))
        x = x.view(batch, time, -1)
        q_values = self.fc2(fun.relu(self.fc1(x)))
        return q_values, hidden  # q_values have shape [batch, n_actions]

    def sample_actions(self, device, screens, prev_state):
        # noinspection PyCallingNonCallable, PyUnresolvedReferences
        screens = torch.tensor(screens, dtype=torch.float32, device=device)
        q_values, next_state = self.forward(screens, prev_state)
        q_values = q_values.detach().cpu().numpy()
        batch_size, time_size, n_actions = q_values.shape
        q_values = q_values.reshape([batch_size * time_size, n_actions])

        eps = self.epsilon
        random_actions = np.random.choice(n_actions, size=batch_size*time_size)
        best_actions = q_values.argmax(axis=-1)

        should_explore = np.random.choice([0, 1], batch_size*time_size, p=[1-eps, eps])
        return np.where(should_explore, random_actions, best_actions), next_state


if __name__ == '__main__':
    net = DQN('p', 8, 1.0)
    a = net.sample_actions('cpu', np.random.normal(size=[1, 1, 3, 60, 108]), None)
    print(a)
