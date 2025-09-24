from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any
import numpy as np
import torch
import torch.nn.functional as F

from rlptx.rl.network import Actor, Critic
from rlptx.rl import DEVICE


# hyperparameters taken from sac paper
DISCOUNT_FACTOR = 0.99 # (/gamma) used in calculating critic loss
POLYAK_COEFFICIENT = 0.995 # (/tau) for polyak averaging in target
# hyperparameters not used in paper
INITIAL_ENTROPY_COEFFICIENT = 0.2 # (/alpha) for calculating actor loss
ENTROPY_LEARNING_RATE = 3e-4


class Agent(ABC):
    """Abstract base class for all agents."""
    
    @abstractmethod
    def act(self, observation: Any) -> Any:
        """Return an action determined by the agent's policy for the given observation."""
        pass
    
    @abstractmethod
    def update(self, observation: Any, action: Any, reward: float, 
               next_observation: Any, terminated: bool) -> None:
        """Update the agent's networks based on the given observation, action, 
        reward, next observation, and whether the itertaion is terminated."""
        pass


class SacAgent(Agent):
    """Soft actor-critic agent implementation following the two original 
    SAC papers by Haarnoja et al. (2018). This includes the actor and 
    critic classes from the network module."""
    
    def __init__(self, observation_size, action_size, action_upper_bounds, discount=DISCOUNT_FACTOR, 
                 polyak=POLYAK_COEFFICIENT, initial_entropy=INITIAL_ENTROPY_COEFFICIENT, 
                 entropy_learning_rate=ENTROPY_LEARNING_RATE, actor=None, critic=None, seed=None, device=DEVICE):
        self.seed = seed
        self.observation_size = observation_size
        self.action_size = action_size
        self.actor = Actor(
            observation_size, action_size, action_upper_bounds, device=device
        ) if actor is None else actor
        self.critic = Critic(
            observation_size, action_size, device=device
        ) if critic is None else critic
        self.discount = discount # factor for discounting future rewards
        # The entropy regularization coefficient is not fixed, but instead varies to enforce 
        # an entropy constraint. It is trained together with the actor and critic. The log 
        # value is used to stabilize training by preventing negative values for the coefficient. 
        # The target entropy is determined heuristically and used in the loss.
        self.initial_entropy = initial_entropy
        self.entropy_learning_rate = entropy_learning_rate
        self.log_entropy_regularization = torch.tensor(
            np.log(initial_entropy), requires_grad=True, dtype=torch.float32, device=device
        )
        self.target_entropy = torch.tensor(-action_size, dtype=torch.float32, device=device)
        self.entropy_optimizer = torch.optim.Adam(
            [self.log_entropy_regularization], lr=entropy_learning_rate, weight_decay=0
        )
        # Separate target critic to improve stability.
        # Its networks are slowly updated to match the critic networks.
        self.target_critic = deepcopy(self.critic)
        for parameter in self.target_critic.parameters():
            parameter.requires_grad = False
        self.polyak = polyak # coefficient for soft target network updates
        self.stats_log = {"loss_critic": [], "loss_actor": [], "log_prob_actor": [], 
                          "loss_entropy": [], "log_entropy_regularization": []}
    
    def act(self, observation, evaluation_mode=False):
        """Return an action determined by the policy of the agent for the given observation. Calling 
        this method does not update the agent's networks or change its state. If in evaluation 
        mode, the action is deterministic instead of being sampled from a normal distribution."""
        with torch.no_grad():
            action, _ = self.actor(observation, evaluation_mode) # log_probs never needed here
        return action.cpu().numpy() # return numpy array instead of tensor
    
    def update(self, observation, action, reward, next_observation, terminated):
        """Update the agent's networks by calculating their losses and applying gradient descent. 
        This is also done for the entropy coefficient. The target critic network is updated 
        separately using polyak averaging instead of gradient descent."""
        # Perform pytorch gradient descent steps for actor.
        self.critic.optimizer.zero_grad()
        loss_critic = self._calculate_critic_loss(
            observation, action, next_observation, reward, terminated
        )
        loss_critic.backward()
        self.critic.optimizer.step()
        self.stats_log["loss_critic"].append(loss_critic.item())
        
        # Perform pytorch gradient descent steps for actor.
        # Freeze critic parameters during this as they were already updated.
        for parameter in self.critic.parameters():
            parameter.requires_grad = False
        self.actor.optimizer.zero_grad()
        loss_actor, log_prob_actor = self._calculate_actor_loss(observation)
        loss_actor.backward()
        self.actor.optimizer.step()
        for parameter in self.critic.parameters():
            parameter.requires_grad = True
        self.stats_log["loss_actor"].append(loss_actor.item())
        self.stats_log["log_prob_actor"].append(log_prob_actor.item())
        
        # Soft update target critic networks gradually using polyak averaging.
        # This enables not directly copying the critic networks into the target 
        # networks, but to more slowly update the target network by taking a 
        # weighted average of the critic and target networks with the polyak 
        # coefficient controlling the weighting; this increases stability.
        for critic_param, target_param in zip(
            self.critic.parameters(), self.target_critic.parameters()
        ):
            target_param.data.copy_(
                self.polyak * critic_param.data + (1 - self.polyak) * target_param.data
            )
        
        # Perform gradient descent steps for entropy coefficient. This is a more simple 
        # process as the entropy coefficient is a single value and not a network. 
        # The entropy loss is determined by the entropy of the action plus the 
        # (always negative) heuristic target entropy value (action dimension). 
        # This trains the coefficient to converge to the target entropy value.
        self.entropy_optimizer.zero_grad()
        loss_entropy = (-self.log_entropy_regularization 
                        * (log_prob_actor.detach() + self.target_entropy))
        loss_entropy.backward()
        self.entropy_optimizer.step()
        self.stats_log["loss_entropy"].append(loss_entropy.item())
        self.stats_log["log_entropy_regularization"].append(self.log_entropy_regularization.item())
    
    def _calculate_critic_loss(self, observation, action, next_observation, 
                               reward, terminated):
        """Critic loss is determined by how much the quality value of the current 
        action in the current state differs from the received reward for the current 
        action and the discounted expected quality of the next action in the next 
        state as well as the entropy of that action (i.e. how unlikely it is). This 
        trains the critic to predict the quality of the current and next action while 
        rewarding overvaluing of more unlikely next actions, encouraging exploration."""
        q1, q2 = self.critic(observation, action)
        with torch.no_grad():
            next_action, next_log_probability = self.actor(next_observation)
            next_q1, next_q2 = self.target_critic(next_observation, next_action)
            next_q = torch.min(next_q1, next_q2)
            # entropy_regularization is converted from log value to value
            entropy_regularization = torch.exp(self.log_entropy_regularization.detach())
            # Calculate bellman backup of bellman equation: this target value is 
            # the reward of the current state plus the value of the next state.
            # The value of the next state is 0 if the iteration is terminated.
            target_q = (reward + self.discount * (1 - terminated) 
                        * (next_q - entropy_regularization * next_log_probability))
        loss_q1 = F.mse_loss(q1, target_q)
        loss_q2 = F.mse_loss(q2, target_q)
        loss = loss_q1 + loss_q2
        return loss
    
    def _calculate_actor_loss(self, observation):
        """Actor loss is determined by the entropy of the action (i.e. how 
        unlikely it is) balanced by the quality value of the action. This 
        trains the actor to choose actions with high quality while also 
        rewarding unlikely actions, encouraging exploration."""
        action, log_probability = self.actor(observation)
        # Clipped double q trick: use two q networks and take the minimum value.
        # This improves the q value because it counteracts overestimation.
        q1, q2 = self.critic(observation, action)
        q = torch.min(q1, q2)
        # entropy_regularization is converted from log value to value
        entropy_regularization = torch.exp(self.log_entropy_regularization.detach())
        loss = entropy_regularization * log_probability - q
        return loss, log_probability
    