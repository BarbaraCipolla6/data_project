import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Union, Tuple, List, Optional, Dict

def setup_style() -> None:
    """Sets up a consistent, professional style for all plots.
    
    Uses seaborn 'whitegrid' style, sets figure DPI, default sizes, 
    fonts, and a custom color palette.
    """
    sns.set_style("whitegrid")
    
    plt.rcParams.update({
        'figure.dpi': 100,
        'figure.figsize': (12, 6),
        'axes.titlesize': 16,
        'axes.labelsize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
    })
    
    # Custom color palette with 10 distinct colors
    custom_palette = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]
    sns.set_palette(custom_palette)

def save_figure(fig: plt.Figure, filename: str, output_dir: str = 'output/figures', dpi: int = 300) -> None:
    """Saves figure to the specified directory.
    
    Args:
        fig (plt.Figure): The matplotlib figure object to save.
        filename (str): The name of the file (should end with .png).
        output_dir (str, optional): Directory to save the figure. Defaults to 'output/figures'.
        dpi (int, optional): The resolution in dots per inch. Defaults to 300.
    """
    os.makedirs(output_dir, exist_ok=True)
    if not filename.endswith('.png'):
        filename += '.png'
    filepath = os.path.join(output_dir, filename)
    fig.tight_layout()
    fig.savefig(filepath, dpi=dpi, bbox_inches='tight')

def plot_bar_horizontal(data: Union[pd.Series, Dict], title: str, xlabel: str = '', ylabel: str = '', 
                       color_palette: Optional[str] = None, figsize: Tuple[int, int] = (12, 8), 
                       top_n: Optional[int] = None) -> Tuple[plt.Figure, plt.Axes]:
    """Plots a horizontal bar chart.
    
    Args:
        data (Union[pd.Series, dict]): Data to plot. Keys/index are labels, values are bar lengths.
        title (str): Title of the plot.
        xlabel (str, optional): X-axis label. Defaults to ''.
        ylabel (str, optional): Y-axis label. Defaults to ''.
        color_palette (Optional[str], optional): Seaborn color palette. Defaults to None.
        figsize (Tuple[int, int], optional): Figure size. Defaults to (12, 8).
        top_n (Optional[int], optional): Number of top items to show. Defaults to None.
        
    Returns:
        Tuple[plt.Figure, plt.Axes]: The figure and axes objects.
    """
    if isinstance(data, dict):
        data = pd.Series(data)
        
    data = data.sort_values(ascending=False)
    if top_n is not None:
        data = data.head(top_n)
        
    data = data.sort_values(ascending=True) # Reverse for horizontal bar
    
    fig, ax = plt.subplots(figsize=figsize)
    sns.barplot(x=data.values, y=data.index, ax=ax, palette=color_palette)
    
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    fig.tight_layout()
    return fig, ax

def plot_time_series(x, y, title: str, xlabel: str = 'Year', ylabel: str = '', 
                    figsize: Tuple[int, int] = (14, 6), marker: str = 'o', 
                    color: Optional[str] = None, fill_under: bool = False) -> Tuple[plt.Figure, plt.Axes]:
    """Plots a time series line chart.
    
    Args:
        x: X-axis data (time).
        y: Y-axis data (values).
        title (str): Plot title.
        xlabel (str, optional): X-axis label. Defaults to 'Year'.
        ylabel (str, optional): Y-axis label. Defaults to ''.
        figsize (Tuple[int, int], optional): Figure size. Defaults to (14, 6).
        marker (str, optional): Line marker style. Defaults to 'o'.
        color (Optional[str], optional): Line color. Defaults to None.
        fill_under (bool, optional): Whether to fill area under curve. Defaults to False.
        
    Returns:
        Tuple[plt.Figure, plt.Axes]: The figure and axes objects.
    """
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(x, y, marker=marker, color=color, linewidth=2)
    
    if fill_under:
        ax.fill_between(x, y, alpha=0.3, color=color)
        
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle='--', alpha=0.7)
    
    fig.tight_layout()
    return fig, ax

def plot_heatmap(data: pd.DataFrame, title: str, figsize: Tuple[int, int] = (12, 10), 
                cmap: str = 'YlOrRd', annot: bool = True, fmt: str = '.1f') -> Tuple[plt.Figure, plt.Axes]:
    """Plots a heatmap.
    
    Args:
        data (pd.DataFrame): Data matrix for the heatmap.
        title (str): Plot title.
        figsize (Tuple[int, int], optional): Figure size. Defaults to (12, 10).
        cmap (str, optional): Colormap. Defaults to 'YlOrRd'.
        annot (bool, optional): Whether to annotate cells with values. Defaults to True.
        fmt (str, optional): String formatting for annotations. Defaults to '.1f'.
        
    Returns:
        Tuple[plt.Figure, plt.Axes]: The figure and axes objects.
    """
    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(data, annot=annot, fmt=fmt, cmap=cmap, ax=ax, cbar_kws={'shrink': 0.8})
    
    ax.set_title(title)
    
    fig.tight_layout()
    return fig, ax

def plot_scatter_with_regression(x, y, title: str, xlabel: str = '', ylabel: str = '', 
                               hue=None, figsize: Tuple[int, int] = (10, 8), 
                               alpha: float = 0.5, log_scale: bool = False) -> Tuple[plt.Figure, plt.Axes]:
    """Plots a scatter plot with an optional linear regression line.
    
    Args:
        x: X-axis data.
        y: Y-axis data.
        title (str): Plot title.
        xlabel (str, optional): X-axis label. Defaults to ''.
        ylabel (str, optional): Y-axis label. Defaults to ''.
        hue: Grouping variable for coloring points. Defaults to None.
        figsize (Tuple[int, int], optional): Figure size. Defaults to (10, 8).
        alpha (float, optional): Point opacity. Defaults to 0.5.
        log_scale (bool, optional): Whether to use log scale for both axes. Defaults to False.
        
    Returns:
        Tuple[plt.Figure, plt.Axes]: The figure and axes objects.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    if hue is not None:
        sns.scatterplot(x=x, y=y, hue=hue, alpha=alpha, ax=ax)
    else:
        sns.scatterplot(x=x, y=y, alpha=alpha, ax=ax)
        
    # Drop NaNs to compute regression safely
    df = pd.DataFrame({'x': x, 'y': y}).dropna()
    
    if len(df) > 1:
        # Calculate linear regression
        z = np.polyfit(df['x'], df['y'], 1)
        p = np.poly1d(z)
        
        # Calculate R^2
        yhat = p(df['x'])
        ybar = np.sum(df['y']) / len(df['y'])
        ssreg = np.sum((yhat - ybar)**2)
        sstot = np.sum((df['y'] - ybar)**2)
        r_squared = ssreg / sstot if sstot != 0 else 0
        
        # Plot regression line
        x_seq = np.linspace(df['x'].min(), df['x'].max(), 100)
        ax.plot(x_seq, p(x_seq), color='red', linestyle='--', 
                label=f'Regression (R²={r_squared:.2f})')
        ax.legend()
        
    if log_scale:
        ax.set_xscale('log')
        ax.set_yscale('log')
        
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle='--', alpha=0.7)
    
    fig.tight_layout()
    return fig, ax

def plot_distribution(data, title: str, xlabel: str = '', bins: int = 50, 
                     kde: bool = True, figsize: Tuple[int, int] = (12, 6), 
                     log_scale: bool = False) -> Tuple[plt.Figure, plt.Axes]:
    """Plots a histogram with optional KDE overlay.
    
    Args:
        data: Data to plot the distribution for.
        title (str): Plot title.
        xlabel (str, optional): X-axis label. Defaults to ''.
        bins (int, optional): Number of histogram bins. Defaults to 50.
        kde (bool, optional): Whether to overlay KDE. Defaults to True.
        figsize (Tuple[int, int], optional): Figure size. Defaults to (12, 6).
        log_scale (bool, optional): Whether to use log scale for X axis. Defaults to False.
        
    Returns:
        Tuple[plt.Figure, plt.Axes]: The figure and axes objects.
    """
    fig, ax = plt.subplots(figsize=figsize)
    sns.histplot(data, bins=bins, kde=kde, ax=ax, log_scale=log_scale)
    
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel('Frequency / Frecuencia')
    ax.grid(True, linestyle='--', alpha=0.7)
    
    fig.tight_layout()
    return fig, ax

def plot_boxplot_by_category(data: pd.DataFrame, x: str, y: str, title: str, 
                            figsize: Tuple[int, int] = (14, 8), order: Optional[List[str]] = None, 
                            horizontal: bool = False) -> Tuple[plt.Figure, plt.Axes]:
    """Plots a boxplot categorized by a column.
    
    Args:
        data (pd.DataFrame): Data containing x and y columns.
        x (str): Categorical column name.
        y (str): Numerical column name.
        title (str): Plot title.
        figsize (Tuple[int, int], optional): Figure size. Defaults to (14, 8).
        order (Optional[List[str]], optional): Order of categories. Defaults to None.
        horizontal (bool, optional): Whether to plot horizontally. Defaults to False.
        
    Returns:
        Tuple[plt.Figure, plt.Axes]: The figure and axes objects.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    if horizontal:
        sns.boxplot(data=data, x=y, y=x, order=order, ax=ax)
        ax.grid(axis='x', linestyle='--', alpha=0.7)
    else:
        sns.boxplot(data=data, x=x, y=y, order=order, ax=ax)
        plt.xticks(rotation=45, ha='right')
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
    ax.set_title(title)
    
    fig.tight_layout()
    return fig, ax

def plot_stacked_area(data: pd.DataFrame, title: str, xlabel: str = '', ylabel: str = '', 
                     figsize: Tuple[int, int] = (14, 7), alpha: float = 0.7) -> Tuple[plt.Figure, plt.Axes]:
    """Plots a stacked area chart.
    
    Args:
        data (pd.DataFrame): Data to plot, where index is X-axis and columns are stacked areas.
        title (str): Plot title.
        xlabel (str, optional): X-axis label. Defaults to ''.
        ylabel (str, optional): Y-axis label. Defaults to ''.
        figsize (Tuple[int, int], optional): Figure size. Defaults to (14, 7).
        alpha (float, optional): Transparency of areas. Defaults to 0.7.
        
    Returns:
        Tuple[plt.Figure, plt.Axes]: The figure and axes objects.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    data.plot.area(ax=ax, alpha=alpha)
    
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1))
    
    fig.tight_layout()
    return fig, ax

def plot_donut_chart(data: Union[pd.Series, Dict], title: str, figsize: Tuple[int, int] = (10, 10), 
                    colors: Optional[List[str]] = None) -> Tuple[plt.Figure, plt.Axes]:
    """Plots a donut chart.
    
    Args:
        data (Union[pd.Series, Dict]): Data to plot. Keys are labels, values are sizes.
        title (str): Plot title.
        figsize (Tuple[int, int], optional): Figure size. Defaults to (10, 10).
        colors (Optional[List[str]], optional): List of colors. Defaults to None.
        
    Returns:
        Tuple[plt.Figure, plt.Axes]: The figure and axes objects.
    """
    if isinstance(data, dict):
        data = pd.Series(data)
        
    fig, ax = plt.subplots(figsize=figsize)
    
    wedges, texts, autotexts = ax.pie(data, labels=data.index, autopct='%1.1f%%', 
                                     startangle=90, colors=colors, wedgeprops=dict(width=0.3))
    
    ax.set_title(title)
    
    fig.tight_layout()
    return fig, ax

def plot_grouped_bars(data: pd.DataFrame, title: str, xlabel: str = '', ylabel: str = '', 
                     figsize: Tuple[int, int] = (14, 8)) -> Tuple[plt.Figure, plt.Axes]:
    """Plots a grouped bar chart.
    
    Args:
        data (pd.DataFrame): Data to plot, where index is groups (X-axis) and columns are bars per group.
        title (str): Plot title.
        xlabel (str, optional): X-axis label. Defaults to ''.
        ylabel (str, optional): Y-axis label. Defaults to ''.
        figsize (Tuple[int, int], optional): Figure size. Defaults to (14, 8).
        
    Returns:
        Tuple[plt.Figure, plt.Axes]: The figure and axes objects.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    data.plot(kind='bar', ax=ax)
    
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.xticks(rotation=45, ha='right')
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1))
    
    fig.tight_layout()
    return fig, ax
