import plotly.graph_objects as go
import numpy as np

def line_plot(ds, time_dim, time_idx, x_coords, var):
    """
    Create a 1D line plot using Plotly.

    Args:
        ds: xarray.Dataset
        time_dim: Name of the time dimension
        time_idx: Index of the time step to plot
        x_coords: Coordinates for the X axis
        var: Variable name to plot

    Returns:
        plotly.graph_objects.Figure
    """
    
    fig = go.Figure()
    for v in var:
        values = ds[v].isel({time_dim: time_idx}).values
        fig.add_trace(go.Scatter(x=x_coords, y=values, mode='lines', name=v))

    fig.update_layout(
        showlegend=True,
        title={
            'text': f"{time_dim} = {ds[time_dim].values[time_idx]:.3f} (iteration: {time_idx})",
            'x': 0.5,
            'xanchor': 'center'
        }
    )
    return fig