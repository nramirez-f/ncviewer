"""1D plotting utilities for ncviewer.

This module handles 1D plotting operations using matplotlib and hvplot.
Allows plotting variables or expressions at specific time steps.
"""
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import xarray as xr
from ._utils import open_dataset
from ._math import evaluate_expression


def _parse_time_index(ds, time_spec):
    """Parse time specification and return the corresponding index.
    
    Args:
        ds: xarray Dataset
        time_spec: Time specification (integer index or string datetime)
        
    Returns:
        Integer index in the time dimension
        
    Raises:
        ValueError: If time specification is invalid
    """
    if 'time' not in ds.dims:
        raise ValueError("Dataset does not have a 'time' dimension")
    
    # If it's already an integer, use it as index
    try:
        idx = int(time_spec)
        if idx < 0 or idx >= len(ds.time):
            raise ValueError(f"Time index {idx} out of range [0, {len(ds.time)-1}]")
        return idx
    except ValueError:
        pass
    
    # Try to parse as datetime string
    try:
        import pandas as pd
        time_value = pd.to_datetime(time_spec)
        # Find nearest time
        idx = abs(ds.time - time_value).argmin().item()
        return idx
    except Exception as e:
        raise ValueError(f"Invalid time specification '{time_spec}': {e}")


def _prepare_data(ds, expressions, time_idx):
    """Prepare data for plotting by evaluating expressions at given time.
    
    Args:
        ds: xarray Dataset
        expressions: List of variable names or expressions
        time_idx: Time index to extract
        
    Returns:
        List of tuples (label, data_array)
    """
    results = []
    
    for expr in expressions:
        # Check if it's an expression or simple variable
        is_expression = any(op in expr for op in ['+', '-', '*', '/', '**', '(', ')'])
        
        if is_expression:
            # Evaluate expression
            try:
                data = evaluate_expression(ds, expr)
                label = expr
            except (KeyError, SyntaxError) as e:
                print(f"✗ Error evaluating '{expr}': {e}", file=sys.stderr)
                continue
        else:
            # Simple variable
            if expr not in ds.data_vars and expr not in ds.coords:
                print(f"✗ Error: Variable '{expr}' not found", file=sys.stderr)
                continue
            data = ds[expr]
            label = expr
        
        # Extract time slice if time dimension exists
        if 'time' in data.dims:
            data = data.isel(time=time_idx)
        
        results.append((label, data))
    
    return results


def plot1d(path, expressions, time_spec, output=None, use_hvplot=False):
    """Generate 1D plot of variable(s) or expression(s) at specific time.
    
    Args:
        path: Path to NetCDF file
        expressions: List of variable names or expressions to plot
        time_spec: Time specification (index or datetime string)
        output: Output file path (optional, shows interactive if None)
        use_hvplot: If True, use hvplot; if False, use matplotlib
    """
    ds = open_dataset(path)
    
    # Parse time
    try:
        time_idx = _parse_time_index(ds, time_spec)
    except ValueError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return
    
    # Get actual time value for title
    time_value = ds.time.isel(time=time_idx).values
    
    # Prepare data
    data_list = _prepare_data(ds, expressions, time_idx)
    
    if not data_list:
        print("✗ Error: No valid data to plot", file=sys.stderr)
        return
    
    print(f"\n📊 Plotting {len(data_list)} variable(s) at time index {time_idx} ({time_value})")
    
    if use_hvplot:
        _plot_with_hvplot(data_list, time_value, Path(path).name, output)
    else:
        _plot_with_matplotlib(data_list, time_value, Path(path).name, output)


def _plot_with_matplotlib(data_list, time_value, filename, output):
    """Create 1D plot using matplotlib.
    
    Args:
        data_list: List of (label, data_array) tuples
        time_value: Time value for title
        filename: NetCDF filename for title
        output: Output file path or None
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for label, data in data_list:
        # Determine which dimension to use for x-axis
        # Try common spatial dimensions
        x_dim = None
        for dim in ['x', 'lon', 'longitude', 'lat', 'latitude', 'depth', 'z', 'level']:
            if dim in data.dims:
                x_dim = dim
                break
        
        if x_dim is None and len(data.dims) > 0:
            # Use first available dimension
            x_dim = data.dims[0]
        
        if x_dim:
            # Get coordinate values
            if x_dim in data.coords:
                x_vals = data[x_dim].values
            else:
                x_vals = range(len(data[x_dim]))
            
            ax.plot(x_vals, data.values, label=label, marker='o', markersize=3)
            ax.set_xlabel(x_dim)
        else:
            # Scalar or no dimensions
            ax.plot([0], [data.values], 'o', label=label)
            ax.set_xlabel('Index')
    
    ax.set_ylabel('Value')
    ax.set_title(f'{filename} - Time: {time_value}')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output:
        plt.savefig(output, dpi=150, bbox_inches='tight')
        print(f"✓ Plot saved to: {output}")
    else:
        plt.show()
        print("✓ Plot displayed")


def _plot_with_hvplot(data_list, time_value, filename, output):
    """Create 1D plot using hvplot.
    
    Args:
        data_list: List of (label, data_array) tuples
        time_value: Time value for title
        filename: NetCDF filename for title
        output: Output file path or None
    """
    import hvplot.xarray  # noqa
    import holoviews as hv
    
    plots = []
    
    for label, data in data_list:
        # Determine which dimension to use for x-axis
        x_dim = None
        for dim in ['x', 'lon', 'longitude', 'lat', 'latitude', 'depth', 'z', 'level']:
            if dim in data.dims:
                x_dim = dim
                break
        
        if x_dim is None and len(data.dims) > 0:
            x_dim = data.dims[0]
        
        if x_dim:
            plot = data.hvplot.line(
                x=x_dim,
                label=label,
                width=800,
                height=400,
                grid=True
            )
            plots.append(plot)
    
    if not plots:
        print("✗ Error: No plottable data", file=sys.stderr)
        return
    
    # Overlay all plots
    combined = hv.Overlay(plots).opts(
        title=f'{filename} - Time: {time_value}',
        legend_position='right'
    )
    
    if output:
        hv.save(combined, output)
        print(f"✓ Plot saved to: {output}")
    else:
        # Display in browser
        hv.show(combined)
        print("✓ Plot displayed in browser")
