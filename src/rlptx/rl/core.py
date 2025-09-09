from copy import deepcopy
import numpy as np
import torch

from rlptx.rl.network import Actor, Critic
from rlptx.rl.agent import SacAgent
from rlptx.util import mkdir, PROJECT_DIR
from rlptx.rl import DEVICE


MODEL_SAVE_PATH = "models/"


class ReplayBuffer:
    """Replay buffer for storing and sampling transitions from an environment. 
    Every environment step produces transition data that is stored in the replay buffer. 
    The replay buffer has a fixed capacity and overwrites the oldest transition if the buffer is full. 
    Transition data consists of observations, actions, rewards, next observations, and terminateds."""
    
    def __init__(self, capacity, observations_shape, actions_shape, seed=None):
        """Create a replay buffer with the given capacity of transitions that can be stored. 
        A seed to control the random sampling can be specified."""
        self.observations = np.empty((capacity, observations_shape), dtype=np.float32)
        self.actions = np.empty((capacity, actions_shape), dtype=np.float32)
        self.rewards = np.empty((capacity, 1), dtype=np.float32)
        self.next_observations = np.empty((capacity, observations_shape), dtype=np.float32)
        self.terminateds = np.empty((capacity, 1), dtype=bool)
        self.capacity = capacity
        self.index = 0
        self.full = False
        self.rng = np.random.default_rng(seed)
    
    def add(self, observation, action, reward, next_observation, terminated):
        """Add a new transition from an environment step to the replay buffer. 
        If the buffer is full, the oldest transition is overwritten."""
        self.observations[self.index] = observation
        self.actions[self.index] = action
        self.rewards[self.index] = reward
        self.next_observations[self.index] = next_observation
        self.terminateds[self.index] = terminated
        self.index += 1
        if self.index >= self.capacity:
            self.index = 0
            self.full = True
    
    def sample(self, batch_size=1):
        """Sample a (batch of) transition(s) randomly from the replay buffer."""
        length = self.capacity if self.full else self.index
        indices = self.rng.integers(0, length, size=batch_size)
        return (
            torch.as_tensor(self.observations[indices], dtype=torch.float32, device=DEVICE),
            torch.as_tensor(self.actions[indices], dtype=torch.float32, device=DEVICE),
            torch.as_tensor(self.rewards[indices], dtype=torch.float32, device=DEVICE),
            torch.as_tensor(self.next_observations[indices], dtype=torch.float32, device=DEVICE),
            torch.as_tensor(self.terminateds[indices], dtype=torch.float32, device=DEVICE)
        )


def save_sac_agent(agent, filename, path=MODEL_SAVE_PATH):
    """Save a SAC agent to a file including all its hyperparameters and its networks' parameters."""
    actor = agent.actor
    critic = agent.critic
    target_critic = agent.target_critic
    mkdir(path)
    file_path = PROJECT_DIR / (path + filename + ".tar")
    torch.save({
        "actor": actor.state_dict(), 
        "critic": critic.state_dict(), 
        "target_critic": target_critic.state_dict(), 
        "initial_entropy": agent.initial_entropy, 
        "log_entropy_regularization": agent.log_entropy_regularization, 
        "entropy_learning_rate": agent.entropy_learning_rate,
        "discount": agent.discount, 
        "polyak": agent.polyak, 
        "action_upper_bounds": actor.action_upper_bounds, 
        "actor_learning_rate": actor.learning_rate, 
        "actor_hidden_sizes": actor.hidden_sizes,
        "critic_learning_rate": critic.learning_rate, 
        "critic_hidden_sizes": critic.hidden_sizes,
        "observation_size": agent.observation_size, 
        "action_size": agent.action_size
    }, file_path)
    return file_path

def load_sac_agent(filename, path=MODEL_SAVE_PATH):
    """Load a SAC agent from a file. Returns the agent with all its networks and hyperparameters set."""
    model = torch.load(PROJECT_DIR / (path + filename + ".tar"), weights_only=True)
    actor = Actor(model["observation_size"], model["action_size"], model["action_upper_bounds"], 
                  hidden_sizes=model["actor_hidden_sizes"], learning_rate=model["actor_learning_rate"])
    actor.load_state_dict(model["actor"])
    critic = Critic(model["observation_size"], model["action_size"], hidden_sizes=model["critic_hidden_sizes"], 
                    learning_rate=model["critic_learning_rate"])
    critic.load_state_dict(model["critic"])
    target_critic = deepcopy(critic)
    target_critic.load_state_dict(model["target_critic"])
    agent = SacAgent(model["observation_size"], model["action_size"], model["action_upper_bounds"], 
                     discount=model["discount"], polyak=model["polyak"], initial_entropy=model["initial_entropy"], 
                     entropy_learning_rate=model["entropy_learning_rate"], actor=actor, critic=critic)
    agent.target_critic = target_critic
    with torch.no_grad(): # set value of tensor; no_grad necessary to avoid error
        agent.log_entropy_regularization.fill_(model["log_entropy_regularization"])
    return agent
