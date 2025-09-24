from tqdm import tqdm

from rlptx.environment.environment import PtxEnvironment
from rlptx.environment.weather import WeatherDataProvider
from rlptx.rl.core import load_sac_agent
from rlptx.rl import DEVICE
from rlptx.ptx import load_project
from rlptx.logger import log, disable_logger, flush_deferred_logs
from rlptx.util import set_seed


def test_ptx_agent(agent, episodes=100, max_steps_per_episode=None, weather_forecast_days=1, 
                   starting_budget=100, progress_bar=True, seed=None, device="cpu"):
    """Test a trained SAC agent on the PtX environment.
    
    :param agent: [SacAgent, str] 
        - The agent to test. Either a trained agent object or the name of the agent to load.
    :param episodes: [int] 
        - The number of episodes to test the agent on.
    :param max_steps_per_episode: [int] 
        - The maximum number of steps per episode after which the environment is truncated. 
        With the default value of None, the value is set to the amount of available weather data.
    :param weather_forecast_days: [int] 
        - The amount of days for which the weather forecast is provided in each observation. 
        For each day, there is one forecast per hour (24 total) per energy source.
    :param starting_budget: [float] 
        - The available starting budget in the environment.
    :param progress_bar: [bool] 
        - Whether to show a progress bar for the steps of each episode.
    :param seed: [int] 
        - The seed to use for the random number generators of the used modules.
    :param device: [str] 
        - The device to test the agent on, "cpu" or "gpu". The default is "cpu" as it tends to be faster.
    """
    disable_logger("main")
    disable_logger("status")
    disable_logger("reward")
    device = DEVICE if device == "gpu" else "cpu" # default to cpu if no gpu available
    print(f"Testing on device: {device}")
    set_seed(seed)
    ptx_system = load_project()
    ptx_system.set_initial_balance(starting_budget) # starting budget for purchasing commodities in early steps
    weather_data_provider = WeatherDataProvider()
    if max_steps_per_episode is None: # episode cannot be longer than available weather data
        max_steps_per_episode = len(weather_data_provider.weather_data_joined)
    env = PtxEnvironment(
        ptx_system, weather_data_provider, weather_forecast_days=weather_forecast_days, 
        max_steps_per_episode=max_steps_per_episode, seed=seed
    )
    _test_sac(episodes, env, agent, progress_bar, seed)

def _test_sac(episodes, env, agent, use_progress_bar=True, seed=None):
    """Execute the SAC testing loop."""
    log_mode = "deferred" if use_progress_bar else "default"
    observation, info = env.initialize(seed=seed)
    total_steps = 0
    successful_steps = 0 # steps with positive reward
    non_failed_episodes = 0 # episodes which don't terminate in the first step
    for episode in range(episodes):
        if use_progress_bar:
            progress_bar = tqdm(
                total=env.max_steps_per_episode, desc=f"Episode {episode+1} steps", ncols=100
            )
        while not env.truncated and not env.terminated:
            if use_progress_bar:
                progress_bar.update(1)
            # Select an action based on the current observation. 
            # Make the agent do this deterministically in evaluation mode.
            action = agent.act(observation, evaluation_mode=True)
            next_observation, reward, terminated, truncated, info = env.act(
                action, evaluation_mode=True, log_mode=log_mode
            )
            if reward > 0:
                successful_steps += 1
            total_steps += 1
            observation = next_observation
        if env.step > 1:
            non_failed_episodes += 1
        observation, info = env.reset()
        if use_progress_bar:
            progress_bar.close()
            flush_deferred_logs() # only print logs after progress bar is finished
    log(f"Number of successful steps: {successful_steps}, Total number of steps: "
        f"{total_steps}, Number of non-failed episodes: {non_failed_episodes}", "episode")


# command line entry point
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("agent", type=str)
    parser.add_argument("--eps", default=100, type=int)
    parser.add_argument("--maxsteps", default=None, type=int)
    parser.add_argument("--forecast", default=1, type=int)
    parser.add_argument("--device", choices=["cpu", "gpu"], default="cpu", type=str)
    parser.add_argument("--seed", default=None, type=int)
    args = parser.parse_args()
    
    disable_logger("main")
    log(f"Test with config: Episodes: {args.eps}, Max steps per episode: {args.maxsteps}, Weather " 
        f"forecast days: {args.forecast}, Device: {args.device}, Seed: {args.seed}", "episode")
    
    agent, _, seed = load_sac_agent(args.agent, seed=args.seed)
    log(f"Agent {args.agent} loaded successfully", "episode")
    
    test_ptx_agent(agent, episodes=args.eps, max_steps_per_episode=args.maxsteps, 
                   weather_forecast_days=args.forecast, device=args.device, seed=seed)
    print("Testing complete.")
