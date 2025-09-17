import os
from pathlib import Path
from matplotlib import pyplot as plt

from rlptx.evaluation.core import load_episode_log, load_agent_log
from rlptx.logger import LOGFILE_PATH
from rlptx.util import get_most_recent_file, PROJECT_DIR


def plot_episode_log(filename="", path=LOGFILE_PATH, plot_variables=[]):
    if filename == "": # use most recent file
        filename = get_most_recent_file(path, search_string="episode")
    log_df = load_episode_log(filename, path=path)
    _plot_log(log_df, filename, plot_variables)

def plot_agent_log(filename="", path=LOGFILE_PATH, plot_variables=[]):
    if filename == "": # use most recent file
        filename = get_most_recent_file(path, search_string="agent")
    log_df = load_agent_log(filename, path=path)
    _plot_log(log_df, filename, plot_variables)

def _plot_log(log_df, name, plot_variables):
    if len(plot_variables) > 0:
        assert plot_variables in log_df.columns, "Log file does not contain all specified plot variables."
    else:
        plot_variables = log_df.columns
    for variable in plot_variables:
        fig, ax = plt.subplots()
        ax.plot(log_df.index, log_df[variable])
        ax.set(title=f"{variable} of {name}", xlabel="episode", ylabel=variable)
        ax.grid(axis="y")
        plt.show()
    plt.close()
