"""Default configuration for ncplot2d interactive 2D plotting"""

# Configuration dictionary with all default values
CONFIG = {
    # Server configuration
    'server': {
        'port_min': 5000,
        'port_max': 9999,
    },
    
    # Dimension names (can be overridden by CLI args)
    'dimensions': {
        'time_dim': 'time',
        'x_dim': 'x',
        'y_dim': 'y',
    },
    
    # Base plot dimensions
    'plot': {
        'base_width': 600,
        'profile_height': 300,
        'timeseries_height': 400,
    },
    
    # Widget ranges and defaults - Scale
    'scale': {
        'min': 0.5,
        'max': 2.0,
        'step': 0.1,
        'default': 1.0,
    },
    
    # Widget ranges and defaults - Levels
    'levels': {
        'min': 10,
        'step': 10,
        'default': 200,
    },
    
    # Widget ranges and defaults - Angle
    'angle': {
        'min': 0,
        'max': 360,
        'step': 1,
        'default': 90,
    },
    
    # Widget ranges and defaults - Interpolation points (%)
    'interpolation': {
        'min': 10,
        'max': 100,
        'step': 5,
        'default': 25,
    },
    
    # Widget ranges and defaults - Line width
    'linewidth': {
        'min': 0.5,
        'max': 5.0,
        'step': 0.5,
        'default': 2.0,
    },
    
    # Widget ranges and defaults - Marker size
    'markersize': {
        'min': 2,
        'max': 15,
        'step': 1,
        'default': 5,
    },
    
    # Style options
    'style': {
        'color_options': ['blue', 'red', 'green', 'black', 'orange', 'purple', 'brown', 'pink', 'gray', 'cyan'],
        'linestyle_options': ['solid', 'dashed', 'dotted', 'dashdot'],
        'marker_options': ['none', 'circle', 'square', 'diamond', 'triangle', 'cross', 'x'],
    },
    
    # Default style values
    'defaults': {
        'colormap': 'viridis',
        'profile_color': 'black',
        'profile_linestyle': 'dashed',
        'timeseries_color': 'blue',
        'timeseries_linestyle': 'solid',
        'profile_marker': 'none',
        'timeseries_marker': 'circle',
    },
    
    # Cut line visualization in contourf
    'cutline': {
        'color': 'black',
        'width': 2,
        'style': 'dashed',
        'alpha': 0.5,
    },
    
    # Default checkbox values
    'checkboxes': {
        'time_dependent_colorbar': False,
        'show_profile': True,
        'show_grid': True,
    },
}
