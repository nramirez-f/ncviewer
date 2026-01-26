"""Panel app layout and server logic for ncplot2d"""

import sys
import random
import numpy as np
import panel as pn
import hvplot.xarray
import holoviews as hv
from .. import _utils
from .config import CONFIG
from ._widgets import create_widgets
from ._plotter import create_plot, create_timeseries_plot


def launch_server(input_file, time_dim='time', x_dim='x', y_dim='y'):
    """
    Launch Panel server for interactive 2D plotting.
    
    Parameters
    ----------
    input_file : str
        Path to NetCDF file
    time_dim : str, default 'time'
        Name of time dimension
    x_dim : str, default 'x'
        Name of X spatial dimension
    y_dim : str, default 'y'
        Name of Y spatial dimension
    """
    
    # Initialize Panel and HoloViews
    pn.extension()
    hv.extension('bokeh')
    
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
    
    # Validate required dimensions exist
    for dim in [time_dim, x_dim, y_dim]:
        if not _utils.check_dimension(ds, dim):
            available = ", ".join(list(ds.dims)[:5])
            if len(ds.dims) > 5:
                available += f", ... ({len(ds.dims)} total)"
            print(f"✗ Error: Dimension '{dim}' not found. Available dimensions: {available}")
            ds.close()
            sys.exit(1)
    
    # Chunk the dataset for performance
    ds = ds.chunk({time_dim: 1, y_dim: ds.sizes[y_dim], x_dim: ds.sizes[x_dim]})
    
    # Get coordinate arrays
    x_coords = ds[x_dim].values
    y_coords = ds[y_dim].values
    
    # Calculate domain properties
    x_min, x_max = float(x_coords.min()), float(x_coords.max())
    y_min, y_max = float(y_coords.min()), float(y_coords.max())
    x_center = (x_min + x_max) / 2
    y_center = (y_min + y_max) / 2
    domain_size = np.sqrt((x_max - x_min)**2 + (y_max - y_min)**2)
    
    # Create widgets
    widgets = create_widgets(ds, x_coords, y_coords)
    
    # Unpack widgets for easier access
    w_global = widgets['global']
    w_profile = widgets['profile']
    w_ts = widgets['timeseries']
    
    # ========== CREATE REACTIVE PLOTS ==========
    
    # Main contourf plot (without profile to avoid recreation)
    from ._plotter import create_contourf_only, create_profile_only
    
    contourf_pane = pn.panel(
        pn.bind(
            create_contourf_only,
            ds=ds,
            var=w_global['variable'].param.value,
            cmap=w_global['cmap'].param.value,
            scale=w_global['scale'].param.value_throttled,
            levels=w_global['levels'].param.value_throttled,
            independent_scale=w_global['independent_scale'].param.value,
            time_idx=w_global['time'].param.value_throttled,
            angle=w_profile['angle'].param.value_throttled,
            x_inicio=w_profile['x_inicio'].param.value_throttled,
            y_inicio=w_profile['y_inicio'].param.value_throttled,
            npoints_percent=w_profile['npoints'].param.value_throttled,
            x_coords=x_coords,
            y_coords=y_coords,
            domain_size=domain_size,
            show_line=w_global['show_crosssection'].param.value
        ),
        sizing_mode='stretch_width'
    )
    
    # Separate profile pane
    profile_pane = pn.panel(
        pn.bind(
            create_profile_only,
            ds=ds,
            var=w_global['variable'].param.value,
            time_idx=w_global['time'].param.value_throttled,
            angle=w_profile['angle'].param.value_throttled,
            x_inicio=w_profile['x_inicio'].param.value_throttled,
            y_inicio=w_profile['y_inicio'].param.value_throttled,
            npoints_percent=w_profile['npoints'].param.value_throttled,
            profile_scale=w_profile['scale'].param.value_throttled,
            x_coords=x_coords,
            y_coords=y_coords,
            domain_size=domain_size,
            profile_color=w_profile['color'].param.value,
            profile_linestyle=w_profile['linestyle'].param.value,
            profile_linewidth=w_profile['linewidth'].param.value_throttled,
            profile_marker=w_profile['marker'].param.value,
            profile_marker_size=w_profile['marker_size'].param.value_throttled,
            show_profile=w_global['show_crosssection'].param.value
        ),
        sizing_mode='stretch_width'
    )
    
    # Time series plot
    timeseries_pane = pn.panel(
        pn.bind(
            create_timeseries_plot,
            ds=ds,
            var=w_global['variable'].param.value,
            x_pos=w_profile['x_inicio'].param.value_throttled,
            y_pos=w_profile['y_inicio'].param.value_throttled,
            ts_scale=w_ts['scale'].param.value_throttled,
            ts_color=w_ts['color'].param.value,
            ts_linestyle=w_ts['linestyle'].param.value,
            ts_linewidth=w_ts['linewidth'].param.value_throttled,
            ts_marker=w_ts['marker'].param.value,
            ts_marker_size=w_ts['marker_size'].param.value_throttled,
            show_grid=w_ts['show_grid'].param.value,
            x_coords=x_coords,
            y_coords=y_coords
        ),
        sizing_mode='stretch_width'
    )
    
    # ========== SIDEBAR LAYOUT ==========
    
    netcdf_controls = pn.Column(
        w_global['variable'],
        w_global['time'],
        pn.pane.Markdown('---'),
        pn.pane.Markdown('### Exploration point'),
        w_profile['x_inicio'],
        w_profile['y_inicio'],
    )
    
    contourf_controls = pn.Column(
        w_global['cmap'],
        w_global['scale'],
        w_global['levels'],
        w_global['independent_scale'],
        w_global['show_crosssection'],
    )
    
    crosssection_controls = pn.Column(
        pn.pane.Markdown('### Cut parameters'),
        w_profile['angle'],
        w_profile['npoints'],
        pn.pane.Markdown('---'),
        pn.pane.Markdown('### Profile style'),
        w_profile['scale'],
        w_profile['color'],
        w_profile['linestyle'],
        w_profile['linewidth'],
        w_profile['marker'],
        w_profile['marker_size']
    )
    
    timeserie_controls = pn.Column(
        pn.pane.Markdown('### Plot style'),
        w_ts['scale'],
        w_ts['color'],
        w_ts['linestyle'],
        w_ts['linewidth'],
        w_ts['marker'],
        w_ts['marker_size'],
        w_ts['show_grid'],
    )
    
    sidebar_content = [
        pn.pane.Markdown('## Dataset Info'),
        pn.pane.Markdown(f'**File:** {input_file}'),
        pn.pane.Markdown(f'**Variables:** {", ".join(ds.data_vars.keys())}'),
        pn.pane.Markdown(f'**Dimensions:** {dict(ds.sizes)}'),
        pn.layout.Divider(),
        pn.pane.Markdown('## Controls'),
        pn.Accordion(
            ('Simulation', netcdf_controls),
            ('Contourf', contourf_controls),
            ('Profile', crosssection_controls),
            ('Time-Serie', timeserie_controls),
            active=[0]  # Only first active
        ),
    ]
    
    # ========== MAIN LAYOUT ==========
    
    main_layout = pn.Column(
        pn.pane.Markdown('# Contourf'),
        contourf_pane,
        pn.pane.Markdown('# Profile'),
        profile_pane,
        pn.pane.Markdown('# Time Serie'),
        timeseries_pane
    )
    
    # ========== CREATE TEMPLATE ==========
    
    template = pn.template.BootstrapTemplate(
        title='NcViewer - Plot 2D',
        sidebar=sidebar_content,
        main=[main_layout],
    )
    
    # Random port between configured min/max
    port = random.randint(CONFIG['server']['port_min'], CONFIG['server']['port_max'])
    
    print(f'\n✓ Starting Panel server at http://localhost:{port}')
    print('Press Ctrl+C to stop\n')
    
    # Show the template
    template.show(port=port)
