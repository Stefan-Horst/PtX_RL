# Optimizing Power-to-X Systems with Reinforcement Learning

Using Soft Actor-Critic RL algorithm to optimize the operation of PtX systems with regards to profitability as part of my master's thesis.
This project includes two main parts. The first is a flexible PtX system simulation environment. It allows for loading arbitrary configurations of PtX systems regarding commodities, conversions, and storages with their respective properties from a yaml file. The environment features an API similar to that of gym for usage in RL.
The second part is a customizable implementation of the SAC RL algorithm and utilities for training it in the environment, including agent saving/loading, logging, easy parameter configuration, and result visualization.

## Setup

From the project root direcetory, run `pip install -r requirements.txt` to install the required packages. 
Then run `pip install .` to install the project itself. 
After that, you can use the project and run scripts like _train.py_ to start model training.

## Training

Training is done via the _train.py_ script which can be run directly in the command line. The script has two options to either run the SAC agent in a test environment, which is set to Gymnasium's Mujoco HalfCheetah by default, or to run the agent in the actual PtX environment which simulates a PtX system with the specified configuration of the yaml file in the data directory.

To run the script, simply use `python src/rlptx/train.py ptx` (or "gym" for agent test). 
Available additional parameters are: 
| Parameter | Description |
| --- | --- |
| `--eps` | Number of training episodes, default 100 |
| `--warmup` | Sampling steps before actual training, default 1000 |
| `--update` | Number of steps between agent updates, default 1 |
| `--maxsteps` | Max number of steps per episode, default set by environment |
| `--forecast` | Days of weather forecast included in each observation, default 7, only for ptx |
| `--save` | Model save interval, -1 for saving of final model, default none |
| `--load` | Name of save file to load from models dir, default none |
| `--device` | Device to run pytorch on, cpu or gpu, default cpu |
