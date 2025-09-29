from matplotlib import pyplot as plt

from rlptx.evaluation.core import load_log
from rlptx.logger import LOGFILE_PATH
from rlptx.util import get_most_recent_file


def plot_log(filename="", type="episode", path=LOGFILE_PATH, plot_variables=[], cycle=1):
    """Plot a log file for the given log of the given type or the most recent one of that type if no 
    filename is given. If only some variables should be plotted, they can be specified. Cycle is 
    only relevant for evaluation logs. It determines the test cycle to plot the logged variables for."""
    if filename == "": # use most recent file
        filename = get_most_recent_file(path, search_string=type)
    log_df = load_log(filename, type=type, path=path)
    
    if len(plot_variables) > 0:
        assert plot_variables in log_df.columns, "Log file does not contain all specified plot variables."
    else:
        plot_variables = log_df.columns
        plot_variables = plot_variables.drop(["Cycle", "Episode", "Step"], errors="ignore")
    
    if type == "evaluation":
        # plot variables for each episode of the given testing cycle in separate plots
        log_df = log_df[log_df["Cycle"] == cycle]
        unique_episodes = log_df["Episode"].unique()
        print(f"Creating {len(unique_episodes) * len(plot_variables)} plots for "
              f"{len(unique_episodes)} episodes with {len(plot_variables)} variables...")
        empty_plots = 0
        for episode in unique_episodes:
            episode_df = log_df[log_df["Episode"] == episode]
            if len(episode_df) <= 1:
                empty_plots += 1
                continue # don't plot episodes with just one step
            for variable in plot_variables:
                _plot_log(
                    episode_df, f"{filename} - cycle {cycle} - episode {episode}", variable, x="Step"
                )
        if empty_plots > 0:
            print(f"Skipped plots for {empty_plots} episodes because they only contain one step.")
    else:
        for variable in plot_variables:
            _plot_log(log_df, filename, variable)

def _plot_log(log_df, name, variable, x=""):
    """Plot a single variable of a log file."""
    x, xlabel = (log_df.index, "Episode") if x == "" else (log_df[x], "Step")
    fig, ax = plt.subplots()
    ax.plot(x, log_df[variable])
    ax.set(title=f"{variable} of {name}", xlabel=xlabel, ylabel=variable)
    ax.grid(axis="y")
    plt.show()
    plt.close()
