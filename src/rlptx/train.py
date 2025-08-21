from rlptx.environment.environment import GymEnvironment
from rlptx.rl.agent import SacAgent
from rlptx.rl.core import ReplayBuffer


REPLAY_BUFFER_SIZE = 10**6


def train_gym_half_cheetah(episodes=100, warmup_steps=1000, update_interval=1):
    """Train the SAC agent on the gym HalfCheetah-v5 environment for testing."""
    env = GymEnvironment("HalfCheetah-v5")
    agent = SacAgent(
        env.observation_space_size, env.action_space_size, env.action_space_spec.high
    )
    replay_buffer = ReplayBuffer(
        REPLAY_BUFFER_SIZE, env.observation_space_size, env.action_space_size
    )
    _train_sac(episodes, warmup_steps, update_interval, env, agent, replay_buffer)

def _train_sac(episodes, warmup_steps, update_interval, env, agent, replay_buffer):
    """Execute the main SAC training loop."""
    observation, info = env.initialize()
    total_steps = 0
    for episode in range(episodes):
        # The current episode ends when the environment is truncated (meaning 
        # max_steps_per_episode is reached) or when it is terminated (meaning it has 
        # reached a failure state from which there is no recovery).
        while not env.truncated and not env.terminated:
            # Randomly sample actions for more thorough exploration in the beginning 
            # and only then switch to the agent's policy to determine actions.
            if env.step < warmup_steps:
                action = env.action_space_spec.sample()
            else:
                action = agent.act(observation)
            # Apply the chosen action the environment and add the transition data 
            # to the replay buffer so the agent can be trained on it later.
            next_observation, reward, terminated, truncated, info = env.act(action)
            replay_buffer.add(observation, action, reward, next_observation, terminated)
            
            # Start training agent only after it is done with randomly sampling actions 
            # and only every update_interval steps. The agent is updated an equal number 
            # of times so that the update amount is equal to the total number of steps.
            # As SAC is an off-policy algorithm, it is not trained on the data of the 
            # current step, but on random samples from the replay buffer.
            if total_steps >= warmup_steps and total_steps % update_interval == 0:
                for _ in range(update_interval):
                    o, a, r, o2, t = replay_buffer.sample()
                    agent.update(o, a, r, o2, t)
            
            total_steps += 1
            observation = next_observation
        observation, info = env.reset()           
