import panel.widgets as widget
from .config import FPS

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
    # ========== Widgets ==========
    time_player = widget.Player(
        name=f'iteration 0',
        start=0,
        end=len(ds[time_dim]) - 1,
        value=0,
        step=1,
        interval=int(1000 / FPS),
        loop_policy='once',
        sizing_mode='stretch_width'
    )

    variables_simulation_input = widget.TextInput(
        name='Variables or Expressions (comma-separated)',
        value=list(ds.data_vars.keys())[0],
        placeholder='e.g., h, H, h-H...'
    )
    

    # ========== Functions ==========

    def update_time_player_name(value):
        time_player.name = f'iteration {value}'

    # === Watchers ===
    
    time_player.param.watch(lambda event: update_time_player_name(event.new), 'value')

    return {
        'simulation': {
            'time_player': time_player,
            'variables_input': variables_simulation_input
        }
    }