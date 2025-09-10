from tqdm import tqdm
import numpy as np

from rlptx.environment.environment import GymEnvironment, PtxEnvironment
from rlptx.environment.weather import WeatherDataProvider
from rlptx.rl.agent import SacAgent
from rlptx.rl.core import ReplayBuffer, save_sac_agent, load_sac_agent
from rlptx.rl import DEVICE
from rlptx.ptx import load_project
from rlptx.logger import log, disable_logger, flush_deferred_logs
from rlptx.util import get_timestamp


REPLAY_BUFFER_SIZE = 10**6


def train_gym_half_cheetah(episodes=100, warmup_steps=1000, update_interval=1, max_steps_per_episode=None, 
                           epoch_save_interval=None, agent=None, progress_bar=False, device="cpu"):
    """Train the SAC agent on the gym HalfCheetah-v5 environment for testing. Returns the trained agent."""
    disable_logger("main")
    device = DEVICE if device == "gpu" else "cpu" # default to cpu if no gpu available
    print(f"Training on device: {device}")
    env = GymEnvironment("HalfCheetah-v5", max_steps_per_episode=max_steps_per_episode)
    if agent is None:
        agent = SacAgent(
            env.observation_space_size, env.action_space_size, env.action_space_spec["high"], device=device
        )
    replay_buffer = ReplayBuffer(
        REPLAY_BUFFER_SIZE, env.observation_space_size, env.action_space_size, device=device
    )
    _train_sac(episodes, warmup_steps, update_interval, env, agent, replay_buffer, epoch_save_interval, progress_bar)
    return agent # for use in notebooks etc

def train_ptx_system(episodes=100, warmup_steps=1000, update_interval=1, max_steps_per_episode=None, 
                     weather_forecast_days=7, epoch_save_interval=None, agent=None, progress_bar=True, device="cpu"):
    """Train the SAC agent on the PtX environment. Returns the trained agent.

    :param episodes: [int] 
        - The number of episodes to train the agent on.
    :param warmup_steps: [int] 
        - The number of steps before training where actions are sampled to the replay buffer.
    :param update_interval: [int] 
        - The number of steps between agent updates. The agent is updated the same 
        amount of times so that the amount of steps and updates is equal.
    :param max_steps_per_episode: [int] 
        - The maximum number of steps per episode after which the environment is truncated. 
        With the default value of None, the value is set to the amount of available weather data.
    :param weather_forecast_days: [int] 
        - The amount of days for which the weather forecast is provided in each observation.
    :param epoch_save_interval: [int] 
        - The interval at which the agent should be saved. If None, the agent is not saved. 
        If -1, the agent is saved at the end of training.
    :param agent: [SacAgent] 
        - The agent to train. If None, a new one is created.
    :param progress_bar: [bool] 
        - Whether to show a progress bar for the steps of each episode.
    :param device: [str] 
        - The device to train the agent on, "cpu" or "gpu". The default is "cpu" as it tends to be faster.
    """
    disable_logger("main")
    disable_logger("status")
    disable_logger("reward")
    device = DEVICE if device == "gpu" else "cpu" # default to cpu if no gpu available
    print(f"Training on device: {device}")
    ptx_system = load_project()
    weather_data_provider = WeatherDataProvider()
    if max_steps_per_episode is None: # episode cannot be longer than available weather data
        max_steps_per_episode = len(weather_data_provider.weather_data_joined)
    env = PtxEnvironment(
        ptx_system, weather_data_provider, weather_forecast_days=weather_forecast_days, 
        max_steps_per_episode=max_steps_per_episode
    )
    if agent is None:
        agent = SacAgent(
            env.observation_space_size, env.action_space_size, env.action_space_spec["high"], device=device
        )
    replay_buffer = ReplayBuffer(
        REPLAY_BUFFER_SIZE, env.observation_space_size, env.action_space_size, device=device
    )
    _train_sac(episodes, warmup_steps, update_interval, env, agent, 
               replay_buffer, epoch_save_interval, progress_bar)
    return agent # for use in notebooks etc

def _train_sac(episodes, warmup_steps, update_interval, env, agent, 
               replay_buffer, epoch_save_interval, use_progress_bar=True):
    """Execute the main SAC training loop."""
    observation, info = env.initialize()
    total_steps = 0
    for episode in range(episodes):
        if use_progress_bar:
            progress_bar = tqdm(
                total=env.max_steps_per_episode, desc=f"Episode {episode+1} steps", ncols=100
            )   
        # The current episode ends when the environment is truncated (meaning 
        # max_steps_per_episode is reached) or when it is terminated (meaning it has 
        # reached a failure state from which there is no recovery).
        while not env.truncated and not env.terminated:
            if use_progress_bar:
                progress_bar.update(1)
            # Randomly sample actions for more thorough exploration in the beginning 
            # and only then switch to the agent's policy to determine actions.
            if env.step < warmup_steps:
                action = env.sample_action()
            else:
                action = agent.act(observation)
            # Apply the chosen action the environment and add the transition data 
            # to the replay buffer so the agent can be trained on it later.
            next_observation, reward, terminated, truncated, info = env.act(action, defer_logs=use_progress_bar)
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
        current_episode_steps = env.step
        observation, info = env.reset()
        
        if use_progress_bar:
            progress_bar.close()
            flush_deferred_logs() # only print logs after progress bar is finished
        _log_episode_stats(episode, current_episode_steps, agent.stats_log)
        
        if epoch_save_interval not in (None, -1) and (episode + 1) % epoch_save_interval == 0:
            filename = save_sac_agent(agent, f"{get_timestamp()}_sac_agent_e{episode+1}")
            print(f"Saved agent from episode {episode+1} to file: {filename}")
    if epoch_save_interval == -1:
            filename = save_sac_agent(agent, f"{get_timestamp()}_sac_agent_final")
            print(f"Saved final agent to file: {filename}")

def _log_episode_stats(episode, step, stats_log):
    """Log the stats of the last episode by taking the mean of all its steps' values."""
    episode_stats = {}
    for k, v in stats_log.items():
        episode_stats[k] = np.mean(v[-step:])
    log(f"Episode {episode+1} - Actor loss: {episode_stats['loss_actor']:.4f}, Critic loss: " 
        f"{episode_stats['loss_critic']:.4f}, Entropy log coef: {episode_stats['log_entropy_regularization']:.4f}, " 
        f"Entropy coef loss: {episode_stats['loss_entropy']:.4f}", "agent")


# command line entry point
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("env", choices=["gym", "ptx"])
    parser.add_argument("--eps", default=100, type=int)
    parser.add_argument("--warmup", default=1000, type=int)
    parser.add_argument("--update", default=1, type=int)
    parser.add_argument("--maxsteps", default=None, type=int)
    parser.add_argument("--forecast", default=7, type=int)
    parser.add_argument("--save", default=None, type=int)
    parser.add_argument("--load", default=None, type=str)
    parser.add_argument("--device", choices=["cpu", "gpu"], default="cpu", type=str)
    args = parser.parse_args()
    
    if args.load is not None:
        agent = load_sac_agent(args.load)
        print("Agent loaded successfully.")
    else:
        agent = None
    
    print("Training agent...")
    if args.env == "gym":
        train_gym_half_cheetah(episodes=args.eps, warmup_steps=args.warmup, update_interval=args.update, 
                               max_steps_per_episode=args.maxsteps, epoch_save_interval=args.save, 
                               device=args.device, agent=agent)
    elif args.env == "ptx":
        train_ptx_system(episodes=args.eps, warmup_steps=args.warmup, update_interval=args.update,
                         max_steps_per_episode=args.maxsteps, weather_forecast_days=args.forecast, 
                         epoch_save_interval=args.save, device=args.device, agent=agent)
    print("Training complete.")
