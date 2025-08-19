from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any
import torch
import torch.nn.functional as F

from rlptx.rl.network import Actor, Critic


# hyperparameters taken from sac paper
DISCOUNT_FACTOR = 0.99 # (/gamma) used in calculating critic loss
POLYAK_COEFFICIENT = 0.995 # (/tau) for polyak averaging in target
# hyperparameters not used in paper
ENTROPY_REGULARIZATION_COEFFICIENT = 0.01 # (/alpha) for calculating actor loss


class Agent(ABC):
    
    @abstractmethod
    def act(self, observation: Any) -> Any:
        """Return an action determined by the agent's policy for the given observation."""
        pass
    
    @abstractmethod
    def update(self, observation: Any, action: Any, next_observation: Any, 
               reward: float, terminated: bool) -> None:
        """Update the agent's networks based on the given observation, action, 
        next observation, reward, and whether the itertaion is terminated."""
        pass


class SacAgent(Agent):
    
    def __init__(self, observation_size, action_size, action_upper_bounds, 
                 discount=DISCOUNT_FACTOR, entropy=ENTROPY_REGULARIZATION_COEFFICIENT, 
                 polyak=POLYAK_COEFFICIENT):
        self.actor = Actor(observation_size, action_size, action_upper_bounds)
        self.critic = Critic(observation_size, action_size)
        self.discount = discount # factor for discounting future rewards
        self.entropy_regularization = entropy # coefficient for entropy importance
        # Separate target critic to improve stability.
        # Its networks are slowly updated to match the critic networks.
        self.target_critic = deepcopy(self.critic)
        self.polyak = polyak # coefficient for soft target network updates
    
    def act(self, observation):
        with torch.no_grad():
            action, _ = self.actor(observation) # log_probs not needed
        return action.numpy() # return numpy array instead of tensor
    
    def update(self, observation, action, next_observation, reward, terminated):
        # Perform pytorch gradient descent steps for actor.
        self.critic.optimizer.zero_grad()
        loss_critic = self._calculate_critic_loss(
            observation, action, next_observation, reward, terminated
        )
        loss_critic.backward()
        self.critic.optimizer.step()
        
        # Perform pytorch gradient descent steps for actor.
        # Freeze critic parameters during this as they were already updated.
        for parameter in self.critic.parameters():
            parameter.requires_grad = False
        self.actor.optimizer.zero_grad()
        loss_actor = self._calculate_actor_loss(observation)
        loss_actor.backward()
        self.actor.optimizer.step()
        for parameter in self.critic.parameters():
            parameter.requires_grad = True
        
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
            next_action, next_log_probs = self.actor(next_observation)
            next_q1, next_q2 = self.target_critic(next_observation, next_action)
            next_q = torch.min(next_q1, next_q2)
            # Calculate bellman backup of bellman equation: this target value is 
            # the reward of the current state plus the value of the next state.
            # The value of the next state is 0 if the iteration is terminated.
            target_q = (reward + self.discount * (1 - terminated) 
                        * (next_q - self.entropy_regularization * next_log_probs))
        loss_q1 = F.mse_loss(q1, target_q)
        loss_q2 = F.mse_loss(q2, target_q)
        loss = loss_q1 + loss_q2
        return loss
    
    def _calculate_actor_loss(self, observation):
        """Actor loss is determined by the entropy of the action (i.e. how 
        unlikely it is) balanced by the quality value of the action. This 
        trains the actor to choose actions with high quality while also 
        rewarding unlikely actions, encouraging exploration."""
        action, log_probabilities = self.actor(observation)
        # Clipped double q trick: use two q networks and take the minimum value.
        # This improves the q value because it counteracts overestimation.
        q1, q2 = self.critic(observation, action)
        q = torch.min(q1, q2)
        # Calculate mean just to get scalar value from tensor.
        loss = (self.entropy_regularization * log_probabilities - q).mean()
        return loss
    