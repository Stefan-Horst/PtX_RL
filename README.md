# Optimizing Power-to-X Systems with Reinforcement Learning

Using the Soft Actor-Critic (SAC) RL algorithm to optimize the operation of PtX systems with regards to profitability. 
This project includes two main parts. The first is a flexible PtX system simulation environment. It allows for loading arbitrary configurations of PtX systems regarding commodities, conversions, and storages with their respective properties from a yaml file. The environment features an API similar to that of Gymnasium for usage in RL.
The second part is a customizable implementation of the SAC RL algorithm and utilities for training it in the environment, including agent saving/loading, logging, easy parameter configuration, and result visualization. Other RL algorithms can easily be plugged into the PtX environment instead.

Check out the _evaluation.ipynb_ notebook for the results of some training runs with the provided configuration.

The original component structure of the PtX simulation is adapted from [PtX-Now](https://github.com/ulicious/ptx_now). The included exemplary PtX system configuration and the weather data from Chilean Patagonia are taken from PtX-Now as well.

## Setup

From the project root directory, run `pip install .` to install the required packages and the project itself. 
After that, you can use the project and run scripts like _train.py_ to start model training.

## Training

Training is done via the _train.py_ script which can be run directly in the command line. The script has two options to either run the SAC agent in a test environment, which is set to Gymnasium's Mujoco HalfCheetah by default, or to run the agent in the actual PtX environment which simulates a PtX system with the specified configuration of the yaml file in the data directory.

To run the script, simply use `python src/rlptx/train.py ptx` (or "gym" for agent test). 
Available additional parameters are: 
| Parameter | Description |
| --- | --- |
| `--eps` | Amount of training episodes, default 100 |
| `--warmup` | Sampling steps before actual training, default 1000 |
| `--updateevery` | Amount of steps between agent updates, default 1 |
| `--updates` | Amount of updates during each update phase, default 1 |
| `--maxsteps` | Max amount of steps per episode, default none (set by environment) |
| `--forecast` | Days of weather forecast included in each observation, default 1, only for ptx |
| `--test` | Testing interval, -1 for testing of final model, default 10000 |
| `--testeps` | Amount of testing episodes, default 100 |
| `--savethresh` | Conditional model saving based on performance metric during testing, default none |
| `--save` | Automatic model saving interval, -1 for saving of final model, default none |
| `--load` | Name of save file to load from models dir, default none |
| `--device` | Device to run pytorch on, cpu or gpu, default cpu |
| `--seed` | Seed to guarantee reproducibility, default none |


Trained models can also be directly tested via the _test.py_ script which can also be directly run from the command line. Testing only works for the PtX environment.

To run the script, simply use `python src/rlptx/test.py [model file]`. 
Available additional parameters are: 
| Parameter | Description |
| --- | --- |
| `--eps` | Amount of testing episodes, default 100 |
| `--maxsteps` | Max amount of steps per episode, default none (set by environment) |
| `--forecast` | Days of weather forecast included in each observation, default 1 |
| `--seed` | Seed to guarantee reproducibility, default none |
