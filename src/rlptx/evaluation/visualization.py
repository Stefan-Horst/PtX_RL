from matplotlib import pyplot as plt

from rlptx.evaluation.core import load_log
from rlptx.util import get_most_recent_file, PROJECT_DIR
from rlptx.logger import LOGFILE_PATH


def plot_log(filename="", type="episode", path=LOGFILE_PATH, plot_variables=[], 
             cycle=[1], episode=[], save=False, save_path=LOGFILE_PATH):
    """Plot a log file for the given log of the given type or the most recent one of 
    that type if no filename is given. If only some variables should be plotted, they 
    can be specified. Cycle and episode are only relevant for evaluation logs. They 
    determine the test cycles and their episodes to plot the logged variables for. 
    Empty lists as values mean that all cycles or episodes will be plotted."""
    if filename == "": # use most recent file
        filename = get_most_recent_file(path, search_string=type)
    log_df = load_log(filename, type=type, path=path)
    
    if len(plot_variables) > 0:
        assert plot_variables in log_df.columns, "Log file does not contain all specified plot variables."
    else:
        plot_variables = log_df.columns
        plot_variables = plot_variables.drop(["Cycle", "Episode", "Step"], errors="ignore")
    
    if type == "evaluation":
        # plot variables for the given episodes of the given testing cycle in separate plots
        log_df = log_df[log_df["Cycle"].isin(cycle)] if len(cycle) > 0 else log_df
        log_df = log_df[log_df["Episode"].isin(episode)] if len(episode) > 0 else log_df
        unique_cycles = log_df["Cycle"].unique()
        unique_episodes = log_df["Episode"].unique()
        print(f"Creating {len(unique_cycles) * len(unique_episodes) * len(plot_variables)} "
              f"plots for {len(unique_cycles)} cycle with each {len(unique_episodes)} "
              f"episodes with {len(plot_variables)} variables...")
        empty_plots = 0
        for cycle in unique_cycles:
            for episode in unique_episodes:
                episode_df = log_df[log_df["Cycle"] == cycle][log_df["Episode"] == episode]
                if len(episode_df) <= 1:
                    empty_plots += 1
                    continue # don't plot episodes with just one step
                for variable in plot_variables:
                    _plot_log(
                        episode_df, f"{filename} - cycle {cycle} - episode {episode}", variable, type, x="Step"
                    )
        if empty_plots > 0:
            print(f"Skipped plots for {empty_plots} episodes because they only contain one step.")
    else:
        for variable in plot_variables:
            _plot_log(log_df, filename, variable, type, save=save, save_path=save_path)

def _plot_log(log_df, name, variable, type, x="", save=False, save_path=LOGFILE_PATH):
    """Plot a single variable of a log file."""
    x, xlabel = (log_df.index, "Episode") if x == "" else (log_df[x], "Step")
    fig, ax = plt.subplots()
    main_linewidth = 1 if type == "evaluation" else 0.5
    ax.plot(x, log_df[variable], color="#00C1A7", linewidth=main_linewidth)
    if type != "evaluation":
        rolling_window = 100 if type == "test" else 10000
        var_smoothed = log_df[variable].rolling(window=rolling_window).mean()
        ax.plot(x, var_smoothed, color="#3B5799", linewidth=1)
    ax.set(title=f"{variable} of {name}", xlabel=xlabel, ylabel=variable)
    ax.grid(axis="y")
    if save:
        filename = f"{name}_{variable}".replace(" ", "_").replace("/", "_").replace(":", "_").lower()
        plt.savefig(PROJECT_DIR / (save_path + f"{filename}.png"), format="png")
    plt.show()
    