import matplotlib.pyplot as plt
import numpy as np
import tempfile
import flask


def create_pie_plot(value_list, label_list):
    """
    Creates a matplot pie chart.
    :param label_list: list(str) - labels of the chart.
    :param value_list: list(int/float) - list of values to plot.
    :return: matplot.figure
    """
    fig, ax = plt.subplots()
    wedges, texts, autotexts = ax.pie(value_list, labels=label_list, autopct='%1.1f%%', normalize=True)
    for autotext in autotexts:
        autotext.set_color('white')
    return fig


def create_bar_plot(value_list, label_list):
    """
    Creates a bar chart.
    :param label_list: list(str) - labels of the chart.
    :param value_list: list(int/float) - list of values to plot.
    :return: matplot.figure
    """
    fig, ax = plt.subplots()
    add_percantage_lable(ax)
    if len(label_list) < 3:
        plt.bar(label_list, value_list, width=0.4)
    else:
        plt.bar(label_list, value_list)
    plt.xticks(rotation=90, fontsize=8)
    plt.yticks(fontsize=8)
    return fig


def create_horizonzal_bar_plot(value_list, label_list):
    """
    Creates a matplot horizontal bar chart.
    :param label_list: list(str) - labels of the chart.
    :param value_list: list(int/float) - list of values to plot.
    :return: matplot.figure
    """
    plt.rcdefaults()
    fig, ax = plt.subplots()
    add_percantage_lable(ax)
    y_pos = np.arange(len(label_list))
    if len(label_list) < 3:
        plt.barh(y_pos, value_list, align='center', alpha=0.5, width=0.4)
        ax.barh(y_pos, value_list, align='center')
    else:
        plt.barh(y_pos, value_list, align='center', alpha=0.5)
        ax.barh(y_pos, value_list, align='center')

    if len(label_list) > 5:
        plt.xticks(rotation=45, fontsize=8)

    plt.yticks(fontsize=8)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(label_list)
    ax.invert_yaxis()

    # Add value at end of bar
    for index, value in enumerate(value_list):
        plt.text(value, index, str(value), fontsize=8)
    return fig


def add_percantage_lable(ax):
    """
    Adds a axis label in percentage.
    :param ax: figure.ax - matplotlib figure axis object.
    """
    for p in ax.patches:
        width = p.get_width()
        height = p.get_height()
        x, y = p.get_xy()
        ax.annotate(f'{height}', (x + width / 2, y + height * 1.02), ha='center')


def create_box_plot(data, x_label_list):
    fig1, ax1 = plt.subplots()
    ax1.boxplot(data, patch_artist=True)
    if len(x_label_list) > 5:
        rotation = 45
    else:
        rotation = 0
    ax1.set_xticklabels(x_label_list, rotation=rotation, fontsize=8)
    return fig1


def creat_horizontal_box_plot(data, y_label_list):
    fig, ax = plt.subplots()

    ax.set_yticklabels(y_label_list, fontsize=10)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()
    bp = ax.boxplot(data, vert=0, patch_artist=True)
    return fig


def create_scatter_plot(x_value_list, y_value_list):
    size = 25
    fig, ax = plt.subplots()
    plt.scatter(x_value_list, y_value_list, s=size)
    return fig


def plots_to_file(plot_dict):
    """
    Takes a matplot figure and writes it to a png image file.
    :param plot_dict: dict(str, figure) - dictionary of plots.
    :return: dict(key, str) - plot_key, path to image file.
    """
    plot_file_path_list = {}
    for plot_key, figure in plot_dict.items():
        fp = tempfile.NamedTemporaryFile(delete=False,
                                         suffix=".png",
                                         dir=flask.current_app.config["FIRMWARE_FOLDER_CACHE"])
        figure.tight_layout()
        figure.savefig(fp.name, transparent=True, bbox_inches='tight')
        plot_file_path_list[plot_key] = fp.name
    return plot_file_path_list


def close_all_figures():
    plt.close("all")
