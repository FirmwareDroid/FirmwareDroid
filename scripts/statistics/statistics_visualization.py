import json
import pathlib
from model import ImageFile, JsonFile
from scripts.graphics.matplot_wrapper import plots_to_file, create_box_plot, create_scatter_plot, \
    creat_horizontal_box_plot, close_all_figures
from scripts.utils.file_utils.file_util import delete_files_by_path

#TODO REFACTOR OR REMOVE THIS SCRIPT


def get_box_plots(data_list, label_list, plot_name_list=None):
    if plot_name_list is None:
        plot_name_list = ["boxplot", "boxplot_horizontal"]
    return {plot_name_list[0]: create_box_plot(data_list, label_list),
            plot_name_list[1]: creat_horizontal_box_plot(data_list, label_list)}


def create_scatter_plot_from_report_data(statistics_report, attribute_list):
    """

    :param statistics_report:
    :param attribute_list:
    :return:
    """
    for attribute_name in attribute_list:
        attribute_value_dict = getattr(statistics_report, attribute_name)
        if isinstance(attribute_value_dict, JsonFile):
            attribute_value_dict = json.loads(attribute_value_dict.file.read().decode("utf-8"))

        label_list = attribute_value_dict.keys()
        value_list = attribute_value_dict.values()
        x_label = (min(value_list), max(value_list))
        plot_dict = {"scatter": create_scatter_plot(value_list, x_label)}
        save_plots(plot_dict, statistics_report, attribute_name)


def save_plots(plot_dict, statistics_report, attribute_name):
    """
    Adds a list of plot binary (image) to the statistics report.
    :param statistics_report: document - statistics report.
    :param attribute_name: str - count attribute name.
    """
    plot_file_path_dict = plots_to_file(plot_dict)
    close_all_figures()
    plot_attribute_name = attribute_name.replace("_dict", "_plot_dict")
    plot_attribute_dict = getattr(statistics_report, plot_attribute_name)
    for plot_type_key, plot_file_path in plot_file_path_dict.items():
        path = pathlib.Path(plot_file_path)
        with open(plot_file_path, 'rb') as plot_file:
            plot_file.seek(0)
            image_file = ImageFile(
                file=plot_file.read(),
                filename=path.name,
                file_type=path.suffix).save()
            plot_attribute_dict[plot_type_key] = image_file.id
    setattr(statistics_report, plot_attribute_name, plot_attribute_dict)
    delete_files_by_path(plot_file_path_dict.values())
