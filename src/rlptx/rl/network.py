import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


# hyperparameters taken from sac paper (as well as activation function and optimizer)
HIDDEN_SIZES = (256, 256)
LEARNING_RATE = 3e-4
STANDARD_DEVIATION_BOUNDS = (-20, 2) # values from spinningup implementation


class Actor(nn.Module):
    """Probabilistic actor network representing the policy function of the agent. 
    The policy network consists of a multi-layer perceptron and two additional 
    parallel output layers for mean and standard deviation values. They are used to 
    create normal distributions from which the actual output values are sampled."""
    
    def __init__(self, observation_size, action_size, action_upper_bounds, 
                 hidden_sizes=HIDDEN_SIZES, learning_rate=LEARNING_RATE):
        super().__init__()
        self.policy_net = create_mlp([observation_size, *hidden_sizes])
        self.mean_layer = nn.Linear(hidden_sizes[-1], action_size)
        self.standard_deviation_layer = nn.Linear(hidden_sizes[-1], action_size)
        self.action_upper_bounds = action_upper_bounds
        self.learning_rate = learning_rate
        self.optimizer = torch.optim.Adam(self.parameters(), lr=learning_rate, weight_decay=0)
    
    def forward(self, observation):
        """The observation is fed into the network which generates an action. The network outputs mean 
        and standard deviation values which are used to create normal distributions from which actions 
        are sampled. Returns the actions and their total log probability (entropy value)."""
        observation = (torch.tensor(observation, dtype=torch.float32) 
                       if not isinstance(observation, torch.Tensor) else observation)
        policy_output = self.policy_net(observation)
        
        means = self.mean_layer(policy_output)
        # The network outputs the log of the standard deviation, meaning the actual 
        # standard deviation needs to be calculated. The log values have the advantage 
        # that they are more numerically stable by having a wider range of values with 
        # negative values being legal. They are clamped before being exponentiated so that 
        # the resulting actual standard deviation is not too small to computationally handle.
        log_standard_deviations = self.standard_deviation_layer(policy_output)
        log_standard_deviations = torch.clamp(log_standard_deviations, *STANDARD_DEVIATION_BOUNDS)
        standard_deviations = torch.exp(log_standard_deviations)
        probability_distributions = torch.distributions.Normal(means, standard_deviations)
        
        # Apply reparameterization trick to address problem of backpropagation through 
        # a node with a source of randomness (sampling from distribution). 
        # This is done by splitting the distribution to train into two parts: one that 
        # takes the trainable parameters as inputs and is trained during backpropagation 
        # and another consisting of a static standard normal distribution as the source of 
        # randomness which can therefore be ignored during backpropagation.
        actions = probability_distributions.rsample()
        # Squash actions to [-1, 1] with tanh and scale them to their environment bounds.
        squashed_actions = torch.tanh(actions) * torch.tensor(self.action_upper_bounds, dtype=torch.float32)
        
        # Compute log probabilities, rescaling probabilities from [0, 1] to [-inf, 0].
        # They are added and used as the entropy term in the loss function with a lower 
        # value meaning higher entropy as the action tuple is less likely to occur.
        # Lower values of higher entropy are rewarded because they encourage exploration.
        log_probability = probability_distributions.log_prob(actions).sum(dim=-1)
        # Correction for tanh squashing, using alternative formula from spinningup.
        # Original formula: log_probability -= torch.log(1 - squashed_action.pow(2) + noise)
        log_probability -= (2*(np.log(2) - actions - F.softplus(-2*actions))).sum(dim=-1)
        return squashed_actions, log_probability


class Critic(nn.Module):
    """Critic network representing the Q-value function of the agent. This quality 
    value expresses the expected reward for taking an action in a given state.
    SAC uses two separate twin networks for the Q-value function. 
    Therefore, the forward method returns two single values for Q1 and Q2."""
    
    def __init__(self, observation_size, action_size, 
                 hidden_sizes=HIDDEN_SIZES, learning_rate=LEARNING_RATE):
        super().__init__()
        # fixed output layer of size one for returning a single q value
        self.q1_net = create_mlp([observation_size + action_size, *hidden_sizes, 1])
        self.q2_net = create_mlp([observation_size + action_size, *hidden_sizes, 1])
        self.optimizer = torch.optim.Adam(self.parameters(), lr=learning_rate, weight_decay=0)
    
    def forward(self, observation, action):
        """Combines observation and action into a single input tensor which 
        is fed into the two networks. Returns output values of both networks."""
        inputs = torch.cat([observation, action], dim=-1).to(torch.float32)
        q1 = self.q1_net(inputs)
        q2 = self.q2_net(inputs)
        return q1, q2


def create_mlp(layer_sizes, activation=nn.ReLU(), output_activation=nn.ReLU()):
    """Create a multi-layer perceptron with the specified layer sizes and activation functions."""
    layers = []
    for i in range(len(layer_sizes) - 1):
        layers.append(nn.Linear(layer_sizes[i], layer_sizes[i + 1]))
        if i < len(layer_sizes) - 2:
            layers.append(activation)
        else:
            layers.append(output_activation)
    model = nn.Sequential(*layers)
    return model
