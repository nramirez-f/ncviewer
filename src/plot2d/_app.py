"""Panel app layout and server logic for ncplot2d"""

import sys
import random
import numpy as np
import panel as pn
import hvplot.xarray
import holoviews as hv
from .. import _utils
from ._widgets import create_widgets_2d
from ._plotter import create_timeseries_plot


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
        if not dim in ds.dims:
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
    
    # Domain Properties
    x_min, x_max = float(x_coords.min()), float(x_coords.max())
    y_min, y_max = float(y_coords.min()), float(y_coords.max())
    domain_size = np.sqrt((x_max - x_min)**2 + (y_max - y_min)**2)
    
    # Create widgets
    widgets = create_widgets_2d(ds, time_dim, x_coords, y_coords)
        
    # ========== CREATE REACTIVE PLOTS ==========
    
    # Main contourf plot (without profile to avoid recreation)
    from ._plotter import contourf, create_profile_only
    
    contourf_pane = pn.panel(
        pn.bind(
            contourf,
            ds=ds,
            x_dim=x_dim,
            y_dim=y_dim,
            var=widgets['simulation']['variable'].param.value,
            cmap=widgets['contourf']['cmap'].param.value,
            scale=widgets['contourf']['scale'].param.value_throttled,
            levels=widgets['contourf']['levels'].param.value_throttled,
            independent_scale=widgets['contourf']['independent_scale'].param.value,
            time_idx=widgets['simulation']['time'].param.value_throttled,
            angle=widgets['profile']['angle'].param.value_throttled,
            x_inicio=widgets['profile']['x_inicio'].param.value_throttled,
            y_inicio=widgets['profile']['y_inicio'].param.value_throttled,
            npoints_percent=widgets['profile']['npoints'].param.value_throttled,
            x_coords=x_coords,
            y_coords=y_coords,
            domain_size=domain_size,
            show_line=widgets['contourf']['show_crosssection'].param.value
        ),
        #sizing_mode='stretch_width'
    )
    
    # Separate profile pane
    profile_pane = pn.panel(
        pn.bind(
            create_profile_only,
            ds=ds,
            var=widgets['simulation']['variable'].param.value,
            time_idx=widgets['simulation']['time'].param.value_throttled,
            angle=widgets['profile']['angle'].param.value_throttled,
            x_inicio=widgets['profile']['x_inicio'].param.value_throttled,
            y_inicio=widgets['profile']['y_inicio'].param.value_throttled,
            npoints_percent=widgets['profile']['npoints'].param.value_throttled,
            profile_scale=widgets['profile']['scale'].param.value_throttled,
            x_coords=x_coords,
            y_coords=y_coords,
            domain_size=domain_size,
            profile_color=widgets['profile']['color'].param.value,
            profile_linestyle=widgets['profile']['linestyle'].param.value,
            profile_linewidth=widgets['profile']['linewidth'].param.value_throttled,
            profile_marker=widgets['profile']['marker'].param.value,
            profile_marker_size=widgets['profile']['marker_size'].param.value_throttled,
            show_profile=widgets['contourf']['show_crosssection'].param.value
        ),
        sizing_mode='stretch_width'
    )
    
    # Time series plot
    timeseries_pane = pn.panel(
        pn.bind(
            create_timeseries_plot,
            ds=ds,
            var=widgets['simulation']['variable'].param.value,
            x_pos=widgets['profile']['x_inicio'].param.value_throttled,
            y_pos=widgets['profile']['y_inicio'].param.value_throttled,
            ts_scale=widgets['timeseries']['scale'].param.value_throttled,
            ts_color=widgets['timeseries']['color'].param.value,
            ts_linestyle=widgets['timeseries']['linestyle'].param.value,
            ts_linewidth=widgets['timeseries']['linewidth'].param.value_throttled,
            ts_marker=widgets['timeseries']['marker'].param.value,
            ts_marker_size=widgets['timeseries']['marker_size'].param.value_throttled,
            show_grid=widgets['timeseries']['show_grid'].param.value,
            x_coords=x_coords,
            y_coords=y_coords
        ),
        sizing_mode='stretch_width'
    )
    
    # ========== SIDEBAR LAYOUT ==========
    
    netcdf_controls = pn.Column(
        widgets['simulation']['variable'],
        widgets['simulation']['time'],
        pn.pane.Markdown('---'),
        pn.pane.Markdown('### Exploration point'),
        widgets['profile']['x_inicio'],
        widgets['profile']['y_inicio'],
        sizing_mode='stretch_width'
    )

    contourf_controls = pn.Column(
        widgets['contourf']['cmap'],
        widgets['contourf']['scale'],
        widgets['contourf']['levels'],
        widgets['contourf']['independent_scale'],
        widgets['contourf']['show_crosssection'],
        sizing_mode='stretch_width'
    )

    crosssection_controls = pn.Column(
        pn.pane.Markdown('### Cut parameters'),
        widgets['profile']['angle'],
        widgets['profile']['npoints'],
        pn.pane.Markdown('---'),
        pn.pane.Markdown('### Profile style'),
        widgets['profile']['scale'],
        widgets['profile']['color'],
        widgets['profile']['linestyle'],
        widgets['profile']['linewidth'],
        widgets['profile']['marker'],
        widgets['profile']['marker_size'],
        sizing_mode='stretch_width'
    )

    timeserie_controls = pn.Column(
        pn.pane.Markdown('### Plot style'),
        widgets['timeseries']['scale'],
        widgets['timeseries']['color'],
        widgets['timeseries']['linestyle'],
        widgets['timeseries']['linewidth'],
        widgets['timeseries']['marker'],
        widgets['timeseries']['marker_size'],
        widgets['timeseries']['show_grid'],
        sizing_mode='stretch_width'
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
            active=[0],  # Only first active
            sizing_mode='stretch_width'
        ),
    ]

    # ========== MAIN LAYOUT ==========

    main_layout = pn.Column(
        pn.pane.Markdown('# Contourf'),
        contourf_pane,
        pn.pane.Markdown('# Profile'),
        profile_pane,
        pn.pane.Markdown('# Time Serie'),
        timeseries_pane,
        sizing_mode='stretch_width'
    )
    
    # ========== CREATE TEMPLATE ==========
    
    template = pn.template.BootstrapTemplate(
        title='NcViewer - Plot 2D',
        sidebar=sidebar_content,
        main=[main_layout],
    )
    
    print(f'\nStarting Panel server...')
    print('Press Ctrl+C to stop\n')
    template.show()
