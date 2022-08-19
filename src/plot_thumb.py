import argparse
import csv
import datetime
import matplotlib.pyplot as plt
from matplotlib.offsetbox import (OffsetImage, AnnotationBbox)
import matplotlib.colors as mcolors
from typing import List


def create_thumbnail_pictures(ax: plt.axes, data: List[List]) -> None:
    """
    Inserts thumbnail picture into the plot.
    :param ax: (plt.axes) matplotlib axes
    :param data: (List[List]) list containing [filename, date, value]
    :return:
    """
    previous_percentage = None
    for i in range(len(data)):
        image_filename = data[i][0]
        current_percentage = data[i][2]
        date = data[i][1]

        if (previous_percentage != current_percentage) or (i == len(data) - 1):
            image = plt.imread(image_filename, format='png')
            imagebox = OffsetImage(image, zoom=1.5)
            imagebox.image.axes = ax
            xy = [datetime.datetime.strptime(date, "%Y-%m-%d").date(), current_percentage]
            ab = AnnotationBbox(imagebox,
                                xy,
                                xybox=(300, 300),
                                xycoords='data',
                                boxcoords="offset points",
                                pad=2.5,
                                arrowprops=dict(
                                    arrowstyle="->", linestyle="--", linewidth=5,
                                    color=mcolors.CSS4_COLORS['gray']),
                                )

            ax.add_artist(ab)
        previous_percentage = current_percentage


def plot_data(data: List[List], output_filename: str) -> None:
    """
    Plots the value (Y) versus date (X).
    :param data: (List[List]) list containing [filename, date, value]
    :param output_filename: (str) output filename
    :return:
    """
    x = []
    y = []
    for i in range(len(data)):
        x.append(data[i][1])  # date
        y.append(data[i][2])  # percentage
    x = [datetime.datetime.strptime(d, "%Y-%m-%d").date() for d in x]
    plt.plot(x, y, 'o-', linewidth=10, markerfacecolor='lightgreen', markeredgewidth=10, markersize=40)
    plt.xticks(rotation=45, fontsize=65)
    plt.yticks(fontsize=65)
    plt.ylabel('Percentage of plant coverage', fontsize=65)
    plt.grid(color='0.6', linestyle='--', linewidth=0.2)
    plt.ylim([-0.1, 1.1])

    ax = plt.gca()
    create_thumbnail_pictures(ax, data)
    figure = plt.gcf()
    figure.set_size_inches(90, 45)
    plt.savefig(output_filename)


def load_csv(csv_filename: str) -> List[List]:
    """
    Loads the csv file with list containing [filename, date, value].
    :param csv_filename: (str) location and filename of csv file
    :return:
    data: List[List] list containing [filename, date, value]
    """
    data = []
    with open(csv_filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        line_count = 0
        for row in csv_reader:
            if line_count > 0:
                data.append([row[0], row[1], float(row[2])])
            line_count += 1
    return data


if __name__ == "__main__":
    ap = argparse.ArgumentParser()

    ap.add_argument("-i", "--input_csv", required=True, help="images path to folders collection")
    ap.add_argument("-o", "--output_path", required=False, default=None, type=str,
                    help="image debug path")
    args = ap.parse_args()
    output_path = "data-example/"
    if args.output_path is not None:
        output_path = args.output_path

    csv_filename = args.input_csv
    data = load_csv(csv_filename)
    plot_data(data, output_path + '/results.pdf')

