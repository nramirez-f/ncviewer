"""Widget definitions for ncplot2d interactive controls"""

import panel as pn
import matplotlib.pyplot as plt
from .config import CONFIG


def create_widgets_2d(ds, time_dim, x_coords, y_coords):
    """
    Create all Panel widgets for interactive control.
    
    Parameters
    ----------
    ds : xarray.Dataset
        The loaded NetCDF dataset
    x_coords : np.ndarray
        X coordinate values
    y_coords : np.ndarray
        Y coordinate values
        
    Returns
    -------
    dict
        Dictionary containing all widget objects organized by category
    """
    
    # Domain Properties
    x_min, x_max = float(x_coords.min()), float(x_coords.max())
    y_min, y_max = float(y_coords.min()), float(y_coords.max())
    x_center = (x_min + x_max) / 2
    y_center = (y_min + y_max) / 2
    
    
    # ========== SIMULATION  CONTROLS ==========
    
    variable_selector = pn.widgets.Select(
        name='Variable',
        options=list(ds.data_vars.keys()),
        value=list(ds.data_vars.keys())[0]
    )
    
    time_player = pn.widgets.Player(
        name=f'Play (índice: 0)',
        start=0,
        end=len(ds[time_dim]) - 1,
        value=0,
        step=1,
        loop_policy='once',
        sizing_mode='stretch_width'
    )

    # Actualiza el nombre del widget dinámicamente con el valor actual
    def update_player_name(value):
        time_player.name = f'Play (índice: {value})'
    time_player.param.watch(lambda event: update_player_name(event.new), 'value')

    x_inicio_slider = pn.widgets.FloatSlider(
        name='x0',
        start=x_min,
        end=x_max,
        step=(x_max - x_min) / 100,
        value=x_center
    )
    
    y_inicio_slider = pn.widgets.FloatSlider(
        name='y0',
        start=y_min,
        end=y_max,
        step=(y_max - y_min) / 100,
        value=y_center
    )

    # ========== CONTOURF CONTROLS ==========
    
    cmap_selector = pn.widgets.Select(
        name='Colormap',
        options=sorted(plt.colormaps()),
        value=CONFIG['defaults']['colormap']
    )
    
    scale_selector = pn.widgets.FloatSlider(
        name='Plot Scale',
        start=CONFIG['scale']['min'],
        end=CONFIG['scale']['max'],
        step=CONFIG['scale']['step'],
        value=CONFIG['scale']['default']
    )
    
    levels_selector = pn.widgets.IntSlider(
        name='Levels',
        start=CONFIG['levels']['min'],
        end=CONFIG['levels']['max'],
        step=CONFIG['levels']['step'],
        value=CONFIG['levels']['default']
    )
    
    independent_scale_checkbox = pn.widgets.Checkbox(
        name='time-dependent colorbar',
        value=CONFIG['checkboxes']['time_dependent_colorbar']
    )
    
    show_crosssection_checkbox = pn.widgets.Checkbox(
        name='show profile',
        value=CONFIG['checkboxes']['show_profile']
    )
    
    # ========== PROFILE CONTROLS ==========
    
    angle_slider = pn.widgets.IntSlider(
        name='Angle (degrees)',
        start=CONFIG['angle']['min'],
        end=CONFIG['angle']['max'],
        step=CONFIG['angle']['step'],
        value=CONFIG['angle']['default']
    )
    
    npoints_slider = pn.widgets.IntSlider(
        name='Interpolation points (%)',
        start=CONFIG['interpolation']['min'],
        end=CONFIG['interpolation']['max'],
        step=CONFIG['interpolation']['step'],
        value=CONFIG['interpolation']['default']
    )
    
    profile_scale_selector = pn.widgets.FloatSlider(
        name='Profile Scale',
        start=CONFIG['scale']['min'],
        end=CONFIG['scale']['max'],
        step=CONFIG['scale']['step'],
        value=CONFIG['scale']['default']
    )
    
    profile_color_selector = pn.widgets.Select(
        name='Line color',
        options=CONFIG['style']['color_options'],
        value=CONFIG['defaults']['profile_color']
    )
    
    profile_linestyle_selector = pn.widgets.Select(
        name='Line style',
        options=CONFIG['style']['linestyle_options'],
        value=CONFIG['defaults']['profile_linestyle']
    )
    
    profile_linewidth_slider = pn.widgets.FloatSlider(
        name='Line width',
        start=CONFIG['linewidth']['min'],
        end=CONFIG['linewidth']['max'],
        step=CONFIG['linewidth']['step'],
        value=CONFIG['linewidth']['default']
    )
    
    profile_marker_selector = pn.widgets.Select(
        name='Marker',
        options=CONFIG['style']['marker_options'],
        value=CONFIG['defaults']['profile_marker']
    )
    
    profile_marker_size = pn.widgets.IntSlider(
        name='Marker size',
        start=CONFIG['markersize']['min'],
        end=CONFIG['markersize']['max'],
        step=CONFIG['markersize']['step'],
        value=CONFIG['markersize']['default']
    )
    
    # ========== TIME-SERIES CONTROLS ==========
    
    ts_scale_selector = pn.widgets.FloatSlider(
        name='Plot Scale',
        start=CONFIG['scale']['min'],
        end=CONFIG['scale']['max'],
        step=CONFIG['scale']['step'],
        value=CONFIG['scale']['default']
    )
    
    ts_color_selector = pn.widgets.Select(
        name='Line color',
        options=CONFIG['style']['color_options'],
        value=CONFIG['defaults']['timeseries_color']
    )
    
    ts_linestyle_selector = pn.widgets.Select(
        name='Line style',
        options=CONFIG['style']['linestyle_options'],
        value=CONFIG['defaults']['timeseries_linestyle']
    )
    
    ts_linewidth_slider = pn.widgets.FloatSlider(
        name='Line width',
        start=CONFIG['linewidth']['min'],
        end=CONFIG['linewidth']['max'],
        step=CONFIG['linewidth']['step'],
        value=CONFIG['linewidth']['default']
    )
    
    ts_marker_selector = pn.widgets.Select(
        name='Marker',
        options=CONFIG['style']['marker_options'],
        value=CONFIG['defaults']['timeseries_marker']
    )
    
    ts_marker_size = pn.widgets.IntSlider(
        name='Marker size',
        start=CONFIG['markersize']['min'],
        end=CONFIG['markersize']['max'],
        step=CONFIG['markersize']['step'],
        value=CONFIG['markersize']['default']
    )
    
    ts_show_grid_checkbox = pn.widgets.Checkbox(
        name='Show grid',
        value=CONFIG['checkboxes']['show_grid']
    )
    
    # Return organized dictionary
    return {
        'simulation': {
            'variable': variable_selector,
            'time': time_player,
        },
        'contourf': {
            'cmap': cmap_selector,
            'scale': scale_selector,
            'levels': levels_selector,
            'independent_scale': independent_scale_checkbox,
            'show_crosssection': show_crosssection_checkbox,
        },
        'profile': {
            'angle': angle_slider,
            'x_inicio': x_inicio_slider,
            'y_inicio': y_inicio_slider,
            'npoints': npoints_slider,
            'scale': profile_scale_selector,
            'color': profile_color_selector,
            'linestyle': profile_linestyle_selector,
            'linewidth': profile_linewidth_slider,
            'marker': profile_marker_selector,
            'marker_size': profile_marker_size,
        },
        'timeseries': {
            'scale': ts_scale_selector,
            'color': ts_color_selector,
            'linestyle': ts_linestyle_selector,
            'linewidth': ts_linewidth_slider,
            'marker': ts_marker_selector,
            'marker_size': ts_marker_size,
            'show_grid': ts_show_grid_checkbox,
        },
    }
