import panel as pn
import panel.widgets as widget
from .config import *

def create_widgets_1d(ds, time_dim, x_coords):
    """
    Create all Panel widgets for interactive control.

    Parameters
    ----------
    ds : xarray.Dataset
        The loaded NetCDF dataset
    time_dim : str
        Name of the time dimension
    x_coords : np.ndarray
        X coordinate values

    Returns
    -------
    dict
        Dictionary containing all widget objects organized by category
    """

    time_player = pn.widgets.Player(
        name='Play',
        start=0,
        end=len(ds[time_dim]) - 1,
        value=0,
        step=1,
        interval=int(1000 / DEFAULT_FPS),
        loop_policy='once',
        sizing_mode='stretch_width'
    )
    
    variable_simulation_selector = widget.MultiChoice(
        name='Variables',
        options=list(ds.data_vars.keys()),
        value=[list(ds.data_vars.keys())[0]]
    )
    
    return {
        'simulation': {
            'time_player': time_player,
            'variable': variable_simulation_selector
        }
    }