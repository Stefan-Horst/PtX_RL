import pandas as pd

from rlptx.util import PROJECT_DIR
from rlptx.logger import LOGFILE_PATH


def load_log(filename, type="episode", path=LOGFILE_PATH):
    """Load a log from a txt file and return it as a dataframe."""
    assert type in ["episode", "agent", "test", "evaluation"], "File is not of a valid log type."
    filepath = PROJECT_DIR / (path + filename + ".txt")

    if type in ["episode", "test"]:
        line_func = _line_episode_and_test
    elif type == "agent":
        line_func = _line_agent
    elif type == "evaluation":
        line_func = _line_evaluation
    
    # loop through the lines of the log file, get all key-value pairs put them into a dataframe
    log = {}
    with open(filepath, "r") as f:
        lines = f.readlines()
        for line in lines:
            elements = line_func(line)
            for element in elements:
                name, value = element.split(": ", maxsplit=1)
                if name in log.keys():
                    log[name].append(value)
                else:
                    log[name] = [value]
    
    log_df = pd.DataFrame(log, dtype=float)
    return log_df

# Helper functions for parsing log lines of the different log types.
# Each returns a list of elements in the form ["name1: value1", ...].

def _line_episode_and_test(line):
    # ignore log lines before first or after last episode or not including stats
    if "reward" not in line:
        return []
    return line.replace("\n", "").split(" - ")[4:]

def _line_agent(line):
    return line.replace("\n", "").split(" - ")[-1].split(", ")

def _line_evaluation(line):
    episode, elements = line.replace("\n", "").split(" - ")[-2:]
    episode = episode.split(" ")
    episode = [f"{episode[i]}: {episode[i+1]}" for i in range(0, len(episode)-1, 2)]
    episode.extend(elements.split(", "))
    return episode
