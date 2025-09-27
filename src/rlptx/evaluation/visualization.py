from matplotlib import pyplot as plt

from rlptx.evaluation.core import load_log
from rlptx.logger import LOGFILE_PATH
from rlptx.util import get_most_recent_file


def plot_log(filename="", type="episode", path=LOGFILE_PATH, plot_variables=[]):
    """Plot a log file for the given log of the given type or 
    the most recent one of that type if no filename is given."""
    if filename == "": # use most recent file
        filename = get_most_recent_file(path, search_string=type)
    log_df = load_log(filename, type=type, path=path)
    
    if len(plot_variables) > 0:
        assert plot_variables in log_df.columns, "Log file does not contain all specified plot variables."
    else:
        plot_variables = log_df.columns
    
    for variable in plot_variables:
        _plot_log(log_df, filename, variable)

def _plot_log(log_df, name, variable):
    """Plot a single variable of a log file."""
    fig, ax = plt.subplots()
    ax.plot(log_df.index, log_df[variable])
    ax.set(title=f"{variable} of {name}", xlabel="episode", ylabel=variable)
    ax.grid(axis="y")
    plt.show()
    plt.close()
