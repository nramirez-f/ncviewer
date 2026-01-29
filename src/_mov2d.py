"""
Create 2D animations from NetCDF files.
Exports to GIF or MP4 format.
"""

import sys
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from pathlib import Path
import shutil
from tqdm import tqdm
from . import _utils


def create_animation(
    input_file,
    variable,
    output_file=None,
    output_format='mp4',
    time_dim='time',
    x_dim='x',
    y_dim='y',
    time_start=0,
    time_end=None,
    time_step=1,
    fps=10,
    cmap='viridis',
    levels=50,
    vmin=None,
    vmax=None,
    time_dependent_scale=True,
    auto_resolution=True,
    figsize=(10, 8),
    dpi=100,
    custom_title=None,
    show_time=True,
    show_colorbar=True,
):
    """
    Create animation from NetCDF dataset.
    
    Parameters
    ----------
    input_file : str
        Path to input NetCDF file
    variable : str
        Variable name to animate
    output_file : str, optional
        Output file path. If None, auto-generates name as '<variable>_<filename>.<format>'
    output_format : str, default 'mp4'
        Output format ('mp4' or 'gif'), used only if output_file is None
    time_dim : str, default 'time'
        Name of time dimension
    x_dim : str, default 'x'
        Name of X spatial dimension
    y_dim : str, default 'y'
        Name of Y spatial dimension
    time_start : int, default 0
        Start time index
    time_end : int, optional
        End time index. If None, uses all available times
    time_step : int, default 1
        Step between time frames
    fps : int, default 10
        Frames per second
    cmap : str, default 'viridis'
        Matplotlib colormap name
    levels : int, default 50
        Number of contour levels
    vmin : float, optional
        Minimum value for colorbar. If None, computed from data
    vmax : float, optional
        Maximum value for colorbar. If None, computed from data
    time_dependent_scale : bool, default True
        If True, colorbar scale changes with time
    auto_resolution : bool, default True
        If True, automatically adjusts figure size to match NetCDF grid
    figsize : tuple, default (10, 8)
        Figure size in inches (width, height), used if auto_resolution=False
    dpi : int, default 100
        DPI for figure, used if auto_resolution=False
    custom_title : str, optional
        Custom title for plots. If None, uses variable name
    show_time : bool, default True
        Show time value in title
    show_colorbar : bool, default True
        Show colorbar
    """
    
    # Load NetCDF data
    print(f"Loading NetCDF file: {input_file}")
    try:
        ds = _utils.open_dataset(input_file)
    except FileNotFoundError:
        print(f"✗ Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: Cannot open NetCDF file '{input_file}': {e}")
        sys.exit(1)
    
    # Validate variable exists
    if not variable in ds.data_vars:
        available = ", ".join(list(ds.data_vars)[:5])
        if len(ds.data_vars) > 5:
            available += f", ... ({len(ds.data_vars)} total)"
        print(f"✗ Error: Variable '{variable}' not found. Available variables: {available}")
        ds.close()
        sys.exit(1)
    
    data = ds[variable]
    
    # Display dataset info
    print(f"\nDataset info:")
    print(f"  Variables: {', '.join(ds.data_vars.keys())}")
    print(f"  Dimensions: {dict(ds.sizes)}")
    print(f"  Selected variable: {variable}")
    
    # Validate dimensions exist
    for dim in [time_dim, x_dim, y_dim]:
        if not dim in ds.dims:
            available = ", ".join(list(ds.dims)[:5])
            if len(ds.dims) > 5:
                available += f", ... ({len(ds.dims)} total)"
            print(f"✗ Error: Dimension '{dim}' not found. Available dimensions: {available}")
            ds.close()
            sys.exit(1)
    
    # Validate variable has required dimensions
    if time_dim not in data.dims:
        print(f"✗ Error: Variable '{variable}' does not have '{time_dim}' dimension.")
        print(f"Variable dimensions: {list(data.dims)}")
        ds.close()
        sys.exit(1)
    
    if len(data.dims) != 3:
        print(f"✗ Error: Variable '{variable}' must be 3D ({time_dim}, {y_dim}, {x_dim}).")
        print(f"Current dimensions: {data.dims}")
        ds.close()
        sys.exit(1)
    
    # Validate variable contains the spatial dimensions
    if x_dim not in data.dims:
        print(f"✗ Error: Variable '{variable}' does not have '{x_dim}' dimension.")
        print(f"Variable dimensions: {list(data.dims)}")
        ds.close()
        sys.exit(1)
    
    if y_dim not in data.dims:
        print(f"✗ Error: Variable '{variable}' does not have '{y_dim}' dimension.")
        print(f"Variable dimensions: {list(data.dims)}")
        ds.close()
        sys.exit(1)
    
    # Time range
    time_end_idx = time_end if time_end is not None else len(data[time_dim])
    time_indices = range(time_start, time_end_idx, time_step)
    
    if len(time_indices) == 0:
        print("✗ Error: No time steps to animate with given range.")
        ds.close()
        sys.exit(1)
    
    print(f"\nCreating animation with {len(time_indices)} frames...")
    print(f"Time range: {time_start} to {time_end_idx-1} (step: {time_step})")
    
    # Get coordinate arrays
    x_coords = ds[x_dim].values
    y_coords = ds[y_dim].values
    
    # Calculate optimal figure size and DPI
    if auto_resolution:
        nx = len(x_coords)
        ny = len(y_coords)
        
        # Calculate aspect ratio
        aspect_ratio = ny / nx
        
        # Strategy: Scale up small grids to minimum resolution, keep 1:1 for large grids
        MIN_PIXELS = 800   # Minimum pixels per dimension for good text rendering
        MAX_PIXELS = 2000  # Maximum pixels per dimension
        
        # Start with 1:1 mapping
        target_width_px = nx
        target_height_px = ny
        
        # Scale up if too small (this fixes the text size issue)
        if target_width_px < MIN_PIXELS and target_height_px < MIN_PIXELS:
            if target_width_px > target_height_px:
                target_width_px = MIN_PIXELS
                target_height_px = int(MIN_PIXELS * aspect_ratio)
            else:
                target_height_px = MIN_PIXELS
                target_width_px = int(MIN_PIXELS / aspect_ratio)
        
        # Scale down if too large
        if target_width_px > MAX_PIXELS or target_height_px > MAX_PIXELS:
            if target_width_px > target_height_px:
                target_width_px = MAX_PIXELS
                target_height_px = int(MAX_PIXELS * aspect_ratio)
            else:
                target_height_px = MAX_PIXELS
                target_width_px = int(MAX_PIXELS / aspect_ratio)
        
        # Use reasonable DPI
        dpi_calc = 100
        
        # Calculate figure size in inches
        figsize_calc = (target_width_px / dpi_calc, target_height_px / dpi_calc)
        
        print(f"\nAuto-resolution enabled:")
        print(f"  Grid size: {nx} x {ny}")
        print(f"  Aspect ratio: {aspect_ratio:.2f}")
        print(f"  Figure size: {figsize_calc[0]:.2f} x {figsize_calc[1]:.2f} inches")
        print(f"  DPI: {dpi_calc}")
        print(f"  Output resolution: {target_width_px} x {target_height_px} pixels")
        if nx < MIN_PIXELS or ny < MIN_PIXELS:
            print(f"  (scaled up from {nx} x {ny} to meet {MIN_PIXELS}px minimum)")
        elif nx > MAX_PIXELS or ny > MAX_PIXELS:
            print(f"  (scaled down from {nx} x {ny} to stay within {MAX_PIXELS}px limit)")
    else:
        figsize_calc = figsize
        dpi_calc = dpi
    
    # Calculate global vmin/vmax if not time-dependent
    if not time_dependent_scale:
        if vmin is not None:
            vmin_val = vmin
        else:
            data_subset = data.isel({time_dim: slice(time_start, time_end_idx, time_step)})
            vmin_val = float(np.nanmin(data_subset.values))
        
        if vmax is not None:
            vmax_val = vmax
        else:
            data_subset = data.isel({time_dim: slice(time_start, time_end_idx, time_step)})
            vmax_val = float(np.nanmax(data_subset.values))
        
        # Validate that vmin < vmax
        if np.isnan(vmin_val) or np.isnan(vmax_val):
            print("Warning: Data contains only NaN values. Using default range [0, 1]")
            vmin_val, vmax_val = 0.0, 1.0
        elif vmin_val == vmax_val:
            print(f"Warning: All data values are constant ({vmin_val}). Adding epsilon for visualization.")
            epsilon = abs(vmin_val) * 0.01 if vmin_val != 0 else 1.0
            vmin_val -= epsilon
            vmax_val += epsilon
        elif vmax_val - vmin_val < 1e-10:
            print(f"Warning: Data range very small ({vmin_val} to {vmax_val}). Expanding range.")
            epsilon = 1e-8
            vmin_val -= epsilon
            vmax_val += epsilon
    
    # Setup figure
    fig, ax = plt.subplots(figsize=figsize_calc, dpi=dpi_calc)
    
    # Initialize plot elements
    contourf = None
    cbar = None
    pbar = None
    
    def init():
        """Initialize animation."""
        ax.clear()
        return []
    
    def animate(frame_idx):
        """Update animation frame."""
        nonlocal contourf, cbar, pbar
        
        time_idx = time_indices[frame_idx]
        data_2d = data.isel({time_dim: time_idx}).values
        
        # Clear previous contourf
        ax.clear()
        
        # Calculate vmin/vmax for this frame if time-dependent
        if time_dependent_scale:
            if vmin is not None:
                frame_vmin = vmin
            else:
                frame_vmin = float(np.nanmin(data_2d))
            
            if vmax is not None:
                frame_vmax = vmax
            else:
                frame_vmax = float(np.nanmax(data_2d))
            
            # Validate that frame_vmin < frame_vmax
            if np.isnan(frame_vmin) or np.isnan(frame_vmax):
                print(f"Warning: Frame {frame_idx} contains only NaN. Using [0, 1]")
                frame_vmin, frame_vmax = 0.0, 1.0
            elif frame_vmin == frame_vmax:
                epsilon = abs(frame_vmin) * 0.01 if frame_vmin != 0 else 1.0
                frame_vmin -= epsilon
                frame_vmax += epsilon
            elif frame_vmax - frame_vmin < 1e-10:
                epsilon = 1e-8
                frame_vmin -= epsilon
                frame_vmax += epsilon
        else:
            frame_vmin = vmin_val
            frame_vmax = vmax_val
        
        # Create contourf
        contour_levels = np.linspace(frame_vmin, frame_vmax, levels)
        contourf = ax.contourf(x_coords, y_coords, data_2d,
                               levels=contour_levels,
                               cmap=cmap,
                               extend='both')
        
        # Add colorbar (only once)
        if show_colorbar and frame_idx == 0:
            cbar = plt.colorbar(contourf, ax=ax)
        
        # Set labels
        ax.set_xlabel(x_dim)
        ax.set_ylabel(y_dim)
        
        # Title
        if custom_title:
            title = custom_title
        else:
            title = f'{variable}'
        
        if show_time:
            time_value = data[time_dim].isel({time_dim: time_idx}).values
            title += f' (time={time_value:.3f})'
        
        ax.set_title(title)
        
        # Update progress bar
        if pbar is not None:
            pbar.update(1)
        
        return [contourf]
    
    # Create progress bar
    print(f"\nGenerating {len(time_indices)} frames...")
    pbar = tqdm(total=len(time_indices), desc="Rendering", unit="frame", ncols=80)
    
    # Create animation
    anim = animation.FuncAnimation(
        fig, animate, init_func=init,
        frames=len(time_indices),
        interval=1000/fps,
        blit=False
    )
    
    # Generate automatic filename if not specified
    if output_file is None:
        input_basename = Path(input_file).stem
        output_filename = f"{variable}_{input_basename}.{output_format}"
        output_path = Path(output_filename)
    else:
        output_path = Path(output_file)
    
    output_ext = output_path.suffix.lower()
    
    # Check FFmpeg if exporting to MP4
    if output_ext == '.mp4':
        if not shutil.which('ffmpeg'):
            print("\n" + "="*60)
            print("✗ ERROR: FFmpeg not found!")
            print("="*60)
            print("MP4 export requires FFmpeg to be installed.")
            print("\nTo install FFmpeg:")
            print("  • Ubuntu/Debian: sudo apt install ffmpeg")
            print("  • macOS:         brew install ffmpeg")
            print("  • Windows:       Download from https://ffmpeg.org/download.html")
            print("\nAlternatively, use --format gif")
            print("="*60 + "\n")
            pbar.close()
            plt.close(fig)
            ds.close()
            sys.exit(1)
    
    print(f"\nSaving animation to '{output_path}'...")
    
    try:
        if output_ext == '.gif':
            writer = animation.PillowWriter(fps=fps, metadata=dict(artist='ncviewer'))
            anim.save(str(output_path), writer=writer)
        elif output_ext == '.mp4':
            writer = animation.FFMpegWriter(fps=fps, metadata=dict(artist='ncviewer'),
                                           bitrate=1800)
            anim.save(str(output_path), writer=writer)
        else:
            print(f"✗ Error: Unsupported output format '{output_ext}'")
            print("Supported formats: .gif, .mp4")
            pbar.close()
            plt.close(fig)
            ds.close()
            sys.exit(1)
    except Exception as e:
        pbar.close()
        plt.close(fig)
        ds.close()
        print(f"✗ Error saving animation: {e}")
        print("\nNote: For MP4 export, FFmpeg must be installed.")
        sys.exit(1)
    
    pbar.close()
    plt.close(fig)
    ds.close()
    
    print(f"\n✓ Animation saved successfully!")
    print(f"  Output file: {output_path}")
    print(f"  Frames: {len(time_indices)}")
    print(f"  FPS: {fps}")
    print(f"  Duration: {len(time_indices)/fps:.1f} seconds")
    print(f"  File size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
