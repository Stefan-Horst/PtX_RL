from tqdm import tqdm

from rlptx.environment.environment import PtxEnvironment
from rlptx.environment.weather import WeatherDataProvider
from rlptx.rl.core import load_sac_agent
from rlptx.ptx import load_project
from rlptx.logger import log, disable_logger, flush_deferred_logs, configure_logger, Level
from rlptx.util import set_seed


def test_ptx_agent(agent, episodes=100, max_steps_per_episode=None, weather_forecast_days=1, 
                   starting_budget=100, progress_bar=False, seed=None):
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
    """
    disable_logger("main")
    disable_logger("status")
    disable_logger("reward")
    configure_logger("evaluation", console_level=Level.WARNING) # don't write normal logs to console
    print("Starting testing...")
    set_seed(seed)
    ptx_system = load_project()
    ptx_system.set_initial_balance(starting_budget) # starting budget for purchasing commodities in early steps
    weather_data_provider = WeatherDataProvider(test_size=0.1, seed=seed)
    env = PtxEnvironment(
        ptx_system, weather_data_provider, weather_forecast_days=weather_forecast_days, 
        max_steps_per_episode=max_steps_per_episode, seed=seed, evaluation_mode=True
    )
    _test_sac(episodes, env, agent, progress_bar, seed)
    return agent, env # for use in notebooks etc

def test_ptx_agent_from_train(agent, env, episodes=1, progress_bar=True, seed=None):
    """Function to be used for testing after training in train.py."""
    configure_logger("evaluation", console_level=Level.WARNING) # don't write normal logs to console
    assert env.evaluation_mode == True, "Environment must be in evaluation mode."
    print("Starting testing...")
    _test_sac(episodes, env, agent, progress_bar, seed)
    print("Testing complete.")

def _test_sac(episodes, env, agent, use_progress_bar=True, seed=None):
    """Execute the SAC testing loop."""
    log_mode = "deferred" if use_progress_bar else "default"
    observation, info = env.initialize(seed=seed)
    if use_progress_bar:
        progress_bar = tqdm(total=episodes, desc="Test Episodes", ncols=100)
    for episode in range(episodes):
        while not env.truncated and not env.terminated:
            # Select an action based on the current observation. 
            # Make the agent do this deterministically in evaluation mode.
            action = agent.act(observation, evaluation_mode=True)
            next_observation, reward, terminated, truncated, info = env.act(action, log_mode=log_mode)
            observation = next_observation
        observation, info = env.reset()
        if use_progress_bar:
                progress_bar.update(1)
    if use_progress_bar:
        progress_bar.close()
        flush_deferred_logs() # only print logs after progress bar is finished


# command line entry point
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("agent", type=str)
    parser.add_argument("--eps", default=100, type=int)
    parser.add_argument("--maxsteps", default=None, type=int)
    parser.add_argument("--forecast", default=1, type=int)
    parser.add_argument("--seed", default=None, type=int)
    args = parser.parse_args()
    
    disable_logger("main")
    log(f"Test with config: Episodes: {args.eps}, Max steps per episode: {args.maxsteps}, " 
        f"Weather forecast days: {args.forecast}, Seed: {args.seed}", "episode")
    
    agent, _, seed = load_sac_agent(args.agent, seed=args.seed)
    log(f"Agent {args.agent} loaded successfully", "episode")
    
    test_ptx_agent(agent, episodes=args.eps, max_steps_per_episode=args.maxsteps, 
                   weather_forecast_days=args.forecast, seed=seed)
    print("Testing complete.")
