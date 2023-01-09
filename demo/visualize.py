import streamlit as st
import matplotlib.pyplot as plt
from plotnine import *
import pandas as pd

def draw_distribution(
        data_points,
        x="index", 
        y="points", 
        figsize=(14,2), 
        title=""
    ):
    df = pd.DataFrame({x: range(1, len(data_points) + 1), y: data_points})
    plot = (
       ggplot(df, aes(x=x, y=y))
       + geom_line()
       + xlab(x)
       + ylab(y)
       + labs(title=title)
    )
    # you can add functionalty like this
    plot += theme(figure_size=figsize)
    return plot.draw()

def draw_scatter_plot(
        df, 
        x="factor(grade)",
        y="f__description.bm25",
        figsize=(14, 2)):
    plot = (
        ggplot(df, aes(x=x, y=y))
        + geom_boxplot()
        + geom_jitter()
    )
    # you can add functionalty like this
    plot += theme(figure_size=figsize)
    return plot.draw()



























def draw_dist(data_list, writer=None, xlabel=None, ylabel=None, figsize=(14,2), hlines=None, title=None):
    plt.figure(figsize=figsize)
    plt.xticks(range(1, len(data_list)+1))
    plt.plot(range(1, len(data_list)+1), data_list)
    if xlabel is not None: 
        plt.xlabel(xlabel)
    if ylabel is not None: 
        plt.ylabel(ylabel)
    if hlines is not None:
        for v in hlines:
            plt.axhline(y=v, color='b', linestyle='-')
    if title is not None:
        plt.title(title)
    if writer is not None:
        writer.pyplot(plt)
    else:
        st.pyplot(plt)