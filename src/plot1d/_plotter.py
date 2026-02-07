from bokeh.plotting import figure
from .config import *
from src._math import evaluate_expression
import numpy as np


def line_plot(ds, time_dim, x_dim, time_idx, x_coords, vars_list):
    

    p = figure(
        title=f"{time_dim} = {ds[time_dim].values[time_idx]:.3f}",
        x_axis_label=x_dim,
        y_axis_label='value',
        sizing_mode='stretch_width',
        height=PLOT_HEIGHT
    )

    for var in vars_list:

        var_evaluation = evaluate_expression(ds, var)

        y_values = var_evaluation.isel({time_dim: time_idx}).values

        p.line(
            x_coords,
            y_values,
            legend_label=var,
            line_width=LINE_WIDTH,
        )
    
    p.x_range.start = np.min(x_coords)
    p.x_range.end = np.max(x_coords)

    return p
