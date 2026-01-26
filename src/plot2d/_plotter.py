"""Plotting functions for ncplot2d"""

import numpy as np
import panel as pn
import holoviews as hv
from scipy.interpolate import RegularGridInterpolator
from .config import CONFIG


def calculate_cross_section(data_2d, x_coords, y_coords, angle_rad, x_inicio, y_inicio, npoints, domain_size):
    """
    Calculate a cross-section through 2D data.
    
    Parameters
    ----------
    data_2d : np.ndarray
        2D array of data values
    x_coords : np.ndarray
        X coordinate values
    y_coords : np.ndarray
        Y coordinate values
    angle_rad : float
        Angle in radians for the cross-section direction
    x_inicio : float
        Starting X position
    y_inicio : float
        Starting Y position
    npoints : int
        Number of interpolation points
    domain_size : float
        Size of the domain (diagonal length)
        
    Returns
    -------
    tuple
        (distances, values, x_line, y_line) arrays for the cross-section
    """
    x_min, x_max = float(x_coords.min()), float(x_coords.max())
    y_min, y_max = float(y_coords.min()), float(y_coords.max())
    
    # Direction vector of the line
    dx = np.cos(angle_rad)
    dy = np.sin(angle_rad)
    
    # Create points along the line extending in both directions from starting point
    # This ensures we cover the entire domain regardless of angle
    t = np.linspace(0, domain_size, npoints)
    x_line = x_inicio + t * dx
    y_line = y_inicio + t * dy
    
    # Filter points that are within the domain
    mask = (x_line >= x_min) & (x_line <= x_max) & (y_line >= y_min) & (y_line <= y_max)
    x_line = x_line[mask]
    y_line = y_line[mask]
    t = t[mask]
    
    if len(x_line) == 0:
        return np.array([]), np.array([]), np.array([]), np.array([])
    
    # Interpolate values
    interpolator = RegularGridInterpolator(
        (y_coords, x_coords),
        data_2d,
        method='linear',
        bounds_error=False,
        fill_value=np.nan
    )
    
    points = np.column_stack([y_line, x_line])
    values = interpolator(points)
    
    # Calculate distances along the cut
    distances = t - t[0]
    
    return distances, values, x_line, y_line


def extract_timeseries(ds, var, x_pos, y_pos, x_coords, y_coords):
    """
    Extract time series at a specific (x, y) point.
    
    Parameters
    ----------
    ds : xarray.Dataset
        The NetCDF dataset
    var : str
        Variable name
    x_pos : float
        X position
    y_pos : float
        Y position
    x_coords : np.ndarray
        X coordinate values
    y_coords : np.ndarray
        Y coordinate values
        
    Returns
    -------
    tuple
        (time_values, timeseries) arrays
    """
    # Find the closest index to the given coordinates
    x_idx = np.abs(x_coords - x_pos).argmin()
    y_idx = np.abs(y_coords - y_pos).argmin()
    
    # Extract time series at that point
    timeseries = ds[var][:, y_idx, x_idx].values
    time_values = ds.time.values
    
    return time_values, timeseries


def create_plot(ds, var, cmap, scale, levels, independent_scale, show_crosssection, 
                time_idx, angle, x_inicio, y_inicio, npoints_percent, profile_scale,
                x_coords, y_coords, domain_size,
                profile_color, profile_linestyle, profile_linewidth, 
                profile_marker, profile_marker_size):
    """
    Create the main contourf plot with optional cross-section line and profile.
    [DEPRECATED - Use create_contourf_only and create_profile_only instead]
    
    Returns
    -------
    pn.Column
        Panel column containing the contourf plot and optional profile
    """
    # This function is kept for backward compatibility but not used in the app
    pass


def create_contourf_only(ds, var, cmap, scale, levels, independent_scale,
                        time_idx, angle, x_inicio, y_inicio, npoints_percent,
                        x_coords, y_coords, domain_size, show_line=True):
    """
    Create only the contourf plot with optional cross-section line.
    
    Returns
    -------
    hv.Layout
        HoloViews plot object
    """
    nx = ds.sizes['x']
    ny = ds.sizes['y']
    aspect_ratio = ny / nx
    
    base_width = CONFIG['plot']['base_width']
    width = int(base_width * scale)
    height = int(width * aspect_ratio)
    
    # Get data for the selected time
    data_2d = ds[var].isel(time=time_idx).values
    
    # Build base kwargs for contourf
    plot_kwargs = {
        'x': 'x',
        'y': 'y',
        'cmap': cmap,
        'width': width,
        'height': height,
        'levels': levels,
    }
    
    # Configure clim based on checkbox
    if independent_scale:
        # Independent scale per time
        vmin = float(ds[var].isel(time=time_idx).min().values)
        vmax = float(ds[var].isel(time=time_idx).max().values)
        plot_kwargs['clim'] = (vmin, vmax)
    else:
        # Fixed scale across all times
        vmin = float(ds[var].min().values)
        vmax = float(ds[var].max().values)
        plot_kwargs['clim'] = (vmin, vmax)
    
    # Create contourf for selected time
    contour_plot = ds[var].isel(time=time_idx).hvplot.contourf(**plot_kwargs).opts(shared_axes=False)
    
    if not show_line:
        return contour_plot
    
    # Add cut line
    angle_rad = np.deg2rad(angle)
    min_dim = min(ds.sizes['x'], ds.sizes['y'])
    npoints = int(min_dim * npoints_percent / 100)
    
    # Calculate cross-section to get line coordinates
    distances, values, x_line, y_line = calculate_cross_section(
        data_2d, x_coords, y_coords, angle_rad, x_inicio, y_inicio, npoints, domain_size
    )
    
    if len(x_line) > 0:
        line_data = hv.Curve(
            (x_line, y_line),
            kdims=['x'],
            vdims=['y']
        ).opts(
            color=CONFIG['cutline']['color'],
            line_width=CONFIG['cutline']['width'],
            line_dash=CONFIG['cutline']['style'],
            alpha=CONFIG['cutline']['alpha'],
            shared_axes=False
        )
        return contour_plot * line_data
    else:
        return contour_plot


def create_profile_only(ds, var, time_idx, angle, x_inicio, y_inicio, npoints_percent,
                       profile_scale, x_coords, y_coords, domain_size,
                       profile_color, profile_linestyle, profile_linewidth,
                       profile_marker, profile_marker_size, show_profile=True):
    """
    Create only the profile plot.
    
    Returns
    -------
    hv.Curve or hv.Text
        HoloViews plot object
    """
    if not show_profile:
        return hv.Text(0, 0, '')
    
    # Get data for the selected time
    data_2d = ds[var].isel(time=time_idx).values
    
    # Convert angle and calculate cross-section
    angle_rad = np.deg2rad(angle)
    min_dim = min(ds.sizes['x'], ds.sizes['y'])
    npoints = int(min_dim * npoints_percent / 100)
    
    distances, values, x_line, y_line = calculate_cross_section(
        data_2d, x_coords, y_coords, angle_rad, x_inicio, y_inicio, npoints, domain_size
    )
    
    if len(distances) == 0 or len(values) == 0:
        return hv.Text(0, 0, 'Profile is outside domain')
    
    # Remove NaNs
    mask = ~np.isnan(values)
    distances_clean = distances[mask]
    values_clean = values[mask]
    
    if len(distances_clean) == 0:
        return hv.Text(0, 0, 'No valid data in this profile')
    
    # Calculate profile dimensions with scale
    base_width = CONFIG['plot']['base_width']
    profile_width = int(base_width * profile_scale)
    profile_height = CONFIG['plot']['profile_height']
    
    # Get current time from dataset
    time_value = ds.time.isel(time=time_idx).values
    
    # Create dynamic title for profile
    profile_title = f'Profile of {var} at time={time_value}, position=({x_inicio:.2f}, {y_inicio:.2f}), direction={angle}°'
    
    plot_opts = {
        'width': profile_width,
        'height': profile_height,
        'color': profile_color,
        'line_width': profile_linewidth,
        'line_dash': profile_linestyle,
        'alpha': 1.0,
        'title': profile_title,
        'xlabel': 'Distance along profile',
        'ylabel': var,
        'tools': ['hover'],
        'show_grid': True,
        'shared_axes': False
    }
    
    # Create base plot
    profile_plot = hv.Curve(
        (distances_clean, values_clean),
        kdims=['Distance'],
        vdims=[var]
    ).opts(**plot_opts)
    
    # Add markers if selected
    if profile_marker != 'none':
        marker_map = {
            'circle': 'o',
            'square': 's',
            'diamond': 'd',
            'triangle': '^',
            'cross': '+',
            'x': 'x'
        }
        scatter = hv.Scatter(
            (distances_clean, values_clean),
            kdims=['Distance'],
            vdims=[var]
        ).opts(
            marker=marker_map[profile_marker],
            size=profile_marker_size,
            color=profile_color,
            alpha=1.0
        )
        profile_plot = profile_plot * scatter
    
    return profile_plot


def create_plot_old(ds, var, cmap, scale, levels, independent_scale, show_crosssection, 
                time_idx, angle, x_inicio, y_inicio, npoints_percent, profile_scale,
                x_coords, y_coords, domain_size,
                profile_color, profile_linestyle, profile_linewidth, 
                profile_marker, profile_marker_size):
    """
    Create the main contourf plot with optional cross-section line and profile.
    
    Returns
    -------
    pn.Column
        Panel column containing the contourf plot and optional profile
    """
    nx = ds.sizes['x']
    ny = ds.sizes['y']
    aspect_ratio = ny / nx
    
    base_width = CONFIG['plot']['base_width']
    width = int(base_width * scale)
    height = int(width * aspect_ratio)
    
    # Get data for the selected time
    data_2d = ds[var].isel(time=time_idx).values
    
    # Build base kwargs for contourf
    plot_kwargs = {
        'x': 'x',
        'y': 'y',
        'cmap': cmap,
        'width': width,
        'height': height,
        'levels': levels,
    }
    
    # Configure clim based on checkbox
    if independent_scale:
        # Independent scale per time
        vmin = float(ds[var].isel(time=time_idx).min().values)
        vmax = float(ds[var].isel(time=time_idx).max().values)
        plot_kwargs['clim'] = (vmin, vmax)
    else:
        # Fixed scale across all times
        vmin = float(ds[var].min().values)
        vmax = float(ds[var].max().values)
        plot_kwargs['clim'] = (vmin, vmax)
    
    # Create contourf for selected time
    contour_plot = ds[var].isel(time=time_idx).hvplot.contourf(**plot_kwargs).opts(shared_axes=False)
    
    # ========== ADD PROFILE (CONDITIONAL) ==========
    
    if not show_crosssection:
        return pn.Column(
            pn.pane.HoloViews(contour_plot, sizing_mode='stretch_width')
        )
    
    # Convert angle from degrees to radians
    angle_rad = np.deg2rad(angle)
    
    # Calculate number of points based on percentage of minimum dimension
    min_dim = min(ds.sizes['x'], ds.sizes['y'])
    npoints = int(min_dim * npoints_percent / 100)
    
    # Calculate cross-section
    distances, values, x_line, y_line = calculate_cross_section(
        data_2d, x_coords, y_coords, angle_rad, x_inicio, y_inicio, npoints, domain_size
    )
    
    # Add cut line if there are valid points
    if len(x_line) > 0:
        line_data = hv.Curve(
            (x_line, y_line),
            kdims=['x'],
            vdims=['y']
        ).opts(
            color=CONFIG['cutline']['color'],
            line_width=CONFIG['cutline']['width'],
            line_dash=CONFIG['cutline']['style'],
            alpha=CONFIG['cutline']['alpha'],
            shared_axes=False
        )
        contour_with_line = contour_plot * line_data
    else:
        contour_with_line = contour_plot
    
    # ========== 1D PROFILE PLOT ==========
    
    # Create profile plot directly (no need for @pn.depends since create_plot is already reactive)
    def create_profile_plot():
        if len(distances) > 0 and len(values) > 0:
            # Remove NaNs
            mask = ~np.isnan(values)
            distances_clean = distances[mask]
            values_clean = values[mask]
            
            if len(distances_clean) > 0:
                # Calculate profile dimensions with scale
                profile_width = int(base_width * profile_scale)
                profile_height = CONFIG['plot']['profile_height']
                
                # Get current time from dataset
                time_value = ds.time.isel(time=time_idx).values
                
                # Create dynamic title for profile
                profile_title = f'Profile of {var} at time={time_value}, position=({x_inicio:.2f}, {y_inicio:.2f}), direction={angle}°'
                
                plot_opts = {
                    'width': profile_width,
                    'height': profile_height,
                    'color': profile_color,
                    'line_width': profile_linewidth,
                    'line_dash': profile_linestyle,
                    'alpha': 1.0,
                    'title': profile_title,
                    'xlabel': 'Distance along profile',
                    'ylabel': var,
                    'tools': ['hover'],
                    'show_grid': True,
                    'shared_axes': False
                }
                
                # Create base plot
                profile_plot = hv.Curve(
                    (distances_clean, values_clean),
                    kdims=['Distance'],
                    vdims=[var]
                ).opts(**plot_opts)
                
                # Add markers if selected
                if profile_marker != 'none':
                    marker_map = {
                        'circle': 'o',
                        'square': 's',
                        'diamond': 'd',
                        'triangle': '^',
                        'cross': '+',
                        'x': 'x'
                    }
                    scatter = hv.Scatter(
                        (distances_clean, values_clean),
                        kdims=['Distance'],
                        vdims=[var]
                    ).opts(
                        marker=marker_map[profile_marker],
                        size=profile_marker_size,
                        color=profile_color,
                        alpha=1.0
                    )
                    profile_plot = profile_plot * scatter
                    
                return profile_plot
            else:
                return hv.Text(0, 0, 'No valid data in this profile')
        else:
            return hv.Text(0, 0, 'Profile is outside domain')
    
    # Combine contour with line and profile
    return pn.Column(
        pn.pane.HoloViews(contour_with_line, sizing_mode='stretch_width'),
        pn.pane.Markdown('# Profile'),
        pn.pane.HoloViews(create_profile_plot(), sizing_mode='stretch_width')
    )


def create_timeseries_plot(ds, var, x_pos, y_pos, ts_scale, ts_color, ts_linestyle,
                          ts_linewidth, ts_marker, ts_marker_size, show_grid, x_coords, y_coords):
    """
    Create a time series plot for the selected (x, y) point.
    
    Returns
    -------
    hv.Curve or hv.Text
        HoloViews plot object
    """
    # Extract time series
    time_values, timeseries = extract_timeseries(ds, var, x_pos, y_pos, x_coords, y_coords)
    
    # Verify there is valid data
    if len(timeseries) == 0:
        return hv.Text(0, 0, 'No data available')
    
    # Calculate plot dimensions
    base_width = CONFIG['plot']['base_width']
    ts_width = int(base_width * ts_scale)
    ts_height = CONFIG['plot']['timeseries_height']
    
    # Create dynamic title
    ts_title = f'Time serie of {var} at point = ({x_pos:.2f}, {y_pos:.2f})'
    
    # Configure plot options
    plot_opts = {
        'width': ts_width,
        'height': ts_height,
        'color': ts_color,
        'line_width': ts_linewidth,
        'line_dash': ts_linestyle,
        'alpha': 1.0,
        'title': ts_title,
        'xlabel': 'time',
        'ylabel': var,
        'tools': ['hover'],
        'show_grid': show_grid,
        'shared_axes': False
    }
    
    # Create base plot
    ts_plot = hv.Curve(
        (time_values, timeseries),
        kdims=['time'],
        vdims=[var]
    ).opts(**plot_opts)
    
    # Add markers if selected
    if ts_marker != 'none':
        marker_map = {
            'circle': 'o',
            'square': 's',
            'diamond': 'd',
            'triangle': '^',
            'cross': '+',
            'x': 'x'
        }
        scatter = hv.Scatter(
            (time_values, timeseries),
            kdims=['time'],
            vdims=[var]
        ).opts(
            marker=marker_map[ts_marker],
            size=ts_marker_size,
            color=ts_color,
            alpha=1.0
        )
        ts_plot = ts_plot * scatter
    
    return ts_plot
