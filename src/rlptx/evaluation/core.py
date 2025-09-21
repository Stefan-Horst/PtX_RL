import pandas as pd

from rlptx.util import PROJECT_DIR
from rlptx.logger import LOGFILE_PATH


def load_agent_log(filename, path=LOGFILE_PATH):
    """Load an agent log from a txt file and return it as a dataframe."""
    assert "agent" in filename, "File is not an agent log."
    filepath = PROJECT_DIR / (path + filename + ".txt")
    agent_log = {}
    with open(filepath, "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.split(" - ")[-1].replace("\n", "")
            elements = line.split(",")
            for element in elements:
                name, value = element.split(":", maxsplit=1)
                name = name.strip()
                if name in agent_log.keys():
                    agent_log[name].append(value)
                else:
                    agent_log[name] = [value]
    log_df = pd.DataFrame(agent_log, dtype=float)
    return log_df

def load_episode_log(filename, path=LOGFILE_PATH):
    """Load an episode log from a txt file and return it as a dataframe."""
    assert "episode" in filename, "File is not an episode log."
    filepath = PROJECT_DIR / (path + filename + ".txt")
    episode_log = {}
    with open(filepath, "r") as f:
        lines = f.readlines()
        for line in lines:
            if "reward" not in line:
                continue # ignore log lines before first or after last episode or not including stats
            elements = line.replace("\n", "").split(" - ")[4:]
            for element in elements:
                name, value = element.split(": ", maxsplit=1)
                if "(" in value: # handle step in brackets
                    values = value.split("(", maxsplit=1)
                    value = values[0]
                    n, v = values[1][:-1].split(": ", maxsplit=1)
                    if n in episode_log.keys():
                        episode_log[n].append(v)
                    else:
                        episode_log[n] = [v]
                if name in episode_log.keys():
                    episode_log[name].append(value)
                else:
                    episode_log[name] = [value]
    log_df = pd.DataFrame(episode_log, dtype=float)
    return log_df
