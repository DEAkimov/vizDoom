import torchvision.transforms as transforms
import numpy as np


def reward_shaping_basic(reward, prev_obs, next_obs):
    # no observations needed here
    return reward


# deadly corridor
def reward_shaping_dcr(reward, prev_obs, next_obs):
    # observation = [ammo, health, kill count]
    ammo_health_decrease = next_obs[:2] - prev_obs[:2] < 0
    kill_reward = int(next_obs[2] - prev_obs[2] > 0) * 40.0
    penalty = np.dot(ammo_health_decrease.astype(int), [-5.0, -5.0])
    return reward - penalty + kill_reward


# defend the center
def reward_shaping_dtc(reward, prev_obs, next_obs):
    # observation = [ammo, health]
    ammo_health_decrease = next_obs - prev_obs < 0
    penalty = np.dot(ammo_health_decrease.astype(int), [-0.2, -0.2])
    return reward + penalty


def reward_shaping_hg(reward, prev_obs, next_obs):
    health = next_obs[0] - prev_obs[0]
    return reward + int(health > 0) * health


reward_shaping = {
    'basic': reward_shaping_basic,
    'defend_the_center': reward_shaping_dtc,
    'deadly_corridor': reward_shaping_dcr,
    'health_gathering': reward_shaping_hg
}

basic_transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Grayscale(),
    transforms.Resize((30, 45)),
    transforms.ToTensor(),
])

transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((60, 108)),
    transforms.ToTensor(),
])


def screen_transform(scenario, screen):
    if scenario == 'basic':
        return basic_transform(screen)
    return transform(screen)


def watch_agent(scenario, agent, env):
    """Agent plays in visible environment until done. Returns reward and shaping(reward)"""
    reward = 0.0
    policy_state = None
    env.reset()
    while True:
        screen, features = env.observe()
        action, policy_state = agent.sample_actions(
            'cpu',
            screen_transform(scenario, screen)[None, None],
            policy_state)
        action = action[0]
        r, done = env.advance_action_step(action)
        if not done:
            _, new_features = env.observe()
            reward += reward_shaping[scenario](r, features, new_features)
        else:
            return env.get_episode_reward(), reward + r
