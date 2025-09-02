import numpy as np
import torch



from rlptx.rl import DEVICE


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
