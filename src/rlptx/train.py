from copy import deepcopy
from tqdm import tqdm
import numpy as np

from rlptx.environment.environment import GymEnvironment, PtxEnvironment
from rlptx.environment.weather import WeatherDataProvider
from rlptx.rl.agent import SacAgent
from rlptx.rl.core import ReplayBuffer, save_sac_agent, load_sac_agent
from rlptx.rl import DEVICE
from rlptx.ptx import load_project
from rlptx.logger import log, disable_logger, flush_deferred_logs
from rlptx.util import get_timestamp, set_seed
from rlptx.test import test_ptx_agent_from_train


REPLAY_BUFFER_SIZE = 10**6


def train_gym_half_cheetah(episodes=100, warmup_steps=1000, update_interval=1, max_steps_per_episode=None, 
                           test_interval=10, test_episodes=10, save_threshold=None, epoch_save_interval=None, 
                           agent=None, replay_buffer=None, progress_bar=False, seed=None, device="cpu"):
    """Train the SAC agent on the gym HalfCheetah-v5 environment for testing. Returns the trained agent."""
    disable_logger("main")
    device = DEVICE if device == "gpu" else "cpu" # default to cpu if no gpu available
    print(f"Training on device: {device}")
    set_seed(seed)
    env = GymEnvironment("HalfCheetah-v5", max_steps_per_episode=max_steps_per_episode)
    if agent is None:
        agent = SacAgent(
            env.observation_space_size, env.action_space_size, env.action_space_spec["high"], device=device, seed=seed
        )
    if replay_buffer is None:
        replay_buffer = ReplayBuffer(
            REPLAY_BUFFER_SIZE, env.observation_space_size, env.action_space_size, device=device, seed=seed
        )
    _train_sac(episodes, warmup_steps, update_interval, env, agent, replay_buffer, test_interval, 
               test_episodes, save_threshold, epoch_save_interval, progress_bar, seed)
    return agent, replay_buffer, env # for use in notebooks etc

def train_ptx_system(episodes=100, warmup_steps=1000, update_interval=1, max_steps_per_episode=None, 
                     weather_forecast_days=1, test_interval=10000, test_episodes=10, 
                     save_threshold=1000, epoch_save_interval=None, agent=None, replay_buffer=None, 
                     progress_bar=True, seed=None, device="cpu"):
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
        For each day, there is one forecast per hour (24 total) per energy source.
    :param test_interval: [int] 
        - The interval in epsiodes at which the agent should be tested. 
        If None, the agent is not tested. If -1, the agent is tested at the end of training.
    :param test_episodes: [int] 
        - The number of episodes to test the agent on during each test.
    :param save_threshold: [int] 
        - Average episode revenue during testing that triggers the agent to be saved. 
        If None, the agent is not saved. This controls conditional saving based on agent performance.
    :param epoch_save_interval: [int] 
        - The interval at which the agent should be saved. If None, the agent is not saved. 
        If -1, the agent is saved at the end of training. This controls automatically saving checkpoints.
    :param agent: [SacAgent] 
        - The agent to train. If None, a new one is created.
    :param replay_buffer: [ReplayBuffer] 
        - The replay buffer to use. If None, a new one is created.
    :param progress_bar: [bool] 
        - Whether to show a progress bar for the steps of each episode.
    :param seed: [int] 
        - The seed to use for the random number generators of the used modules.
    :param device: [str] 
        - The device to train the agent on, "cpu" or "gpu". The default is "cpu" as it tends to be faster.
    """
    disable_logger("main")
    disable_logger("status")
    disable_logger("reward")
    device = DEVICE if device == "gpu" else "cpu" # default to cpu if no gpu available
    print(f"Training on device: {device}")
    set_seed(seed)
    ptx_system = load_project()
    ptx_system.set_initial_balance(100) # starting budget for purchasing commodities in early steps
    weather_data_provider = WeatherDataProvider(test_size=0.1, seed=seed)
    env = PtxEnvironment(
        ptx_system, weather_data_provider, weather_forecast_days=weather_forecast_days, 
        max_steps_per_episode=max_steps_per_episode, seed=seed
    )
    if agent is None:
        agent = SacAgent(
            env.observation_space_size, env.action_space_size, env.action_space_spec["high"], device=device, seed=seed
        )
    if replay_buffer is None:
        replay_buffer = ReplayBuffer(
            REPLAY_BUFFER_SIZE, env.observation_space_size, env.action_space_size, device=device, seed=seed
        )
    _train_sac(episodes, warmup_steps, update_interval, env, agent, replay_buffer, test_interval, 
               test_episodes, save_threshold, epoch_save_interval, progress_bar, seed)
    return agent, replay_buffer, env # for use in notebooks etc

def _train_sac(episodes, warmup_steps, update_interval, env, agent, replay_buffer, test_interval, 
               test_episodes, save_threshold, epoch_save_interval, use_progress_bar=True, seed=None):
    """Execute the main SAC training loop."""
    log_mode = "deferred" if use_progress_bar else "default"
    if test_interval is not None:
        testenv = deepcopy(env)
        testenv.evaluation_mode = True
    observation, info = env.initialize(seed=seed)
    total_steps = 0
    
    ### Warmup
    # Randomly sample actions for more thorough exploration in the beginning and save them to 
    # the replay buffer before switching to the agent's policy to determine actions. 
    # This is done in one single pseudo-episode.
    if warmup_steps > 0:
        if use_progress_bar:
            progress_bar = tqdm(
                total=warmup_steps, desc="Warmup steps", ncols=100
            )
        reset_amount = 0
        warmup_reward = 0
        # The current episode ends when the environment is truncated (meaning 
        # max_steps_per_episode is reached) or when it is terminated (meaning 
        # it has reached a failure state from which there is no recovery).
        while total_steps < warmup_steps:
            while not env.truncated and not env.terminated:
                if use_progress_bar:
                    progress_bar.update(1)
                # Sample an action from the environment.
                action = env.sample_action()
                # Apply the chosen action the environment and add the transition data 
                # to the replay buffer so the agent can be trained on it later.
                next_observation, reward, terminated, truncated, info = env.act(action, log_mode="silent")
                replay_buffer.add(observation, action, reward, next_observation, terminated)
                warmup_reward += reward
                total_steps += 1
                observation = next_observation
            observation, info = env.reset()
            reset_amount += 1
        if use_progress_bar:
            progress_bar.close()
        log(f"Warmup - {warmup_steps} steps in {reset_amount} episode{'s' if reset_amount > 1 else ''} (Total "
            f"Reward: {warmup_reward:.4f} - Reward/Step: {(warmup_reward / warmup_steps):.4f})", "episode")

    ### Training
    # Now use the agent to determine actions and save them to the replay buffer. 
    # The agent is trained every update_interval steps on data from the replay buffer.
    observation, info = env.initialize(seed=seed) # start training with fresh environment
    successful_steps = 0 # steps with positive reward
    non_failed_episodes = 0 # episodes which don't terminate in the first step
    save_flag = False # determine whether the agent should be saved (based on performance)
    for episode in range(episodes):
        if use_progress_bar:
            progress_bar = tqdm(
                total=env.max_steps_per_episode, desc=f"Episode {episode+1} steps", ncols=100
            )
        while not env.truncated and not env.terminated:
            if use_progress_bar:
                progress_bar.update(1)
            # Select an action based on the current observation.
            action = agent.act(observation)
            next_observation, reward, terminated, truncated, info = env.act(action, log_mode=log_mode)
            replay_buffer.add(observation, action, reward, next_observation, terminated)
            if reward > 0:
                successful_steps += 1
            
            # Train the agent every update_interval steps. The agent is updated an equal number 
            # of times so that the update amount is equal to the total number of steps.
            # As SAC is an off-policy algorithm, it is not trained on the data of the 
            # current step, but on random samples from the replay buffer.
            if total_steps % update_interval == 0:
                for _ in range(update_interval):
                    o, a, r, o2, t = replay_buffer.sample()
                    agent.update(o, a, r, o2, t)
            
            total_steps += 1
            observation = next_observation
        current_episode_steps = env.step
        if current_episode_steps > 1:
            non_failed_episodes += 1
        observation, info = env.reset()
        if use_progress_bar:
            progress_bar.close()
            flush_deferred_logs() # only print logs after progress bar is finished
        _log_episode_stats(episode, current_episode_steps, agent.stats_log)
        
        # Test the agent every test_interval episodes
        if test_interval not in (None, -1) and (episode+1) % test_interval == 0:
            average_episode_revenue = test_ptx_agent_from_train(
                agent, testenv, episode+1, test_episodes, progress_bar, seed
            )
            save_flag = save_threshold is not None and average_episode_revenue >= save_threshold
        # Save the agent every epoch_save_interval episodes and/or based on performance
        if (epoch_save_interval not in (None, -1) and (episode+1) % epoch_save_interval == 0 or save_flag):
            name_appendix = "_TOP" if save_flag else "" # mark agents saved due to good performance
            filename = save_sac_agent(
                agent, replay_buffer, f"{get_timestamp()}_sac_agent_e{episode+1}{name_appendix}"
            )
            print(f"Saved agent from episode {episode+1} to file: {filename}")
            save_flag = False
    log(f"Training Review - Number of successful steps: {successful_steps}, Total number of steps: "
        f"{total_steps}, Number of non-failed episodes: {non_failed_episodes}", "episode")
    # Final testing after training
    if test_interval == -1:
        average_episode_revenue = test_ptx_agent_from_train(
            agent, testenv, episode+1, test_episodes, progress_bar, seed
        )
        save_flag = save_threshold is not None and average_episode_revenue >= save_threshold
    # Save the final agent
    if epoch_save_interval == -1 or save_flag:
            name_appendix = "_TOP" if save_flag else "" # mark agent saved due to good performance
            filename = save_sac_agent(agent, replay_buffer, f"{get_timestamp()}_sac_agent_final{name_appendix}")
            print(f"Saved final agent to file: {filename}")
    

def _log_episode_stats(episode, step, stats_log):
    """Log the stats of the last episode by taking the mean of all its steps' values."""
    episode_stats = {}
    for k, v in stats_log.items():
        values = v[-step:]
        if len(values) != 0: # values empty if whole episode only consists of sampled warmup steps
            episode_stats[k] = np.mean(values)
        else:
            episode_stats[k] = np.nan
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
    parser.add_argument("--forecast", default=1, type=int)
    parser.add_argument("--test", default=10000, type=int)
    parser.add_argument("--testeps", default=100, type=int)
    parser.add_argument("--savethresh", default=None, type=int)
    parser.add_argument("--save", default=None, type=int)
    parser.add_argument("--load", default=None, type=str)
    parser.add_argument("--device", choices=["cpu", "gpu"], default="cpu", type=str)
    parser.add_argument("--seed", default=None, type=int)
    args = parser.parse_args()
    
    disable_logger("main")
    log(f"Train with config: Environment: {args.env}, Episodes: {args.eps}, Warmup steps: {args.warmup}, " 
        f"Update interval: {args.update}, Max steps per episode: {args.maxsteps}, Weather forecast " 
        f"days: {args.forecast}, Test interval: {args.test}, Test episodes: {args.testeps}, Save threshold: " 
        f"{args.savethresh}, Epoch save interval: {args.save}, Device: {args.device}, Seed: {args.seed}", "episode")
    
    if args.load is not None:
        agent, replay_buffer, seed = load_sac_agent(args.load, seed=args.seed)
        log(f"Agent {args.load} loaded successfully", "episode")
    else:
        agent = None
        replay_buffer = None
        seed = args.seed
    
    if args.env == "gym":
        train_gym_half_cheetah(
            episodes=args.eps, warmup_steps=args.warmup, update_interval=args.update, max_steps_per_episode=args.maxsteps, 
            test_interval=args.test, test_episodes=args.testeps, save_threshold=args.savethresh, 
            epoch_save_interval=args.save, device=args.device, agent=agent, replay_buffer=replay_buffer, seed=seed
        )
    elif args.env == "ptx":
        train_ptx_system(
            episodes=args.eps, warmup_steps=args.warmup, update_interval=args.update,
            max_steps_per_episode=args.maxsteps, weather_forecast_days=args.forecast, test_interval=args.test, 
            test_episodes=args.testeps, save_threshold=args.savethresh, epoch_save_interval=args.save, 
            device=args.device, agent=agent, replay_buffer=replay_buffer, seed=seed
        )
    print("Training complete.")
