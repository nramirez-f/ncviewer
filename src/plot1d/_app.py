import panel as pn

import sys
from src import _utils
from pathlib import Path
from ._widgets import *

def launch_server(input_file, time_dim='time', x_dim='x'):
    try:
        ds = _utils.open_dataset(input_file)
        x_coords = ds[x_dim].values
        # Get Widgets solo si el dataset se abrió correctamente
        widgets = create_widgets_1d(ds, time_dim, x_coords)
    except FileNotFoundError:
        print(f"✗ Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: Cannot open NetCDF file '{input_file}': {e}")
        sys.exit(1)
    # Initialize Panel and HoloViews
    pn.extension('plotly')
    
    # Load NetCDF data
    print(f"Loading NetCDF file {input_file}...")
    try:
        time_idx=widgets['simulation']['time_player'],
    except FileNotFoundError:
        print(f"✗ Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: Cannot open NetCDF file '{input_file}': {e}")
        sys.exit(1)

    x_coords = ds[x_dim].values

    # Get Widgets
    widgets = create_widgets_1d(ds, time_dim, x_coords)

    # ========== Bindings ==========
    from ._plotter import line_plot

    # Line Plot
    def parse_variables(var_string):
        """Parse comma-separated variable expressions into a list."""
        if isinstance(var_string, str):
            return [v.strip() for v in var_string.split(',') if v.strip()]
        return var_string

    line_plot_pane = pn.bind(
        line_plot,
        ds=ds,
        time_dim=time_dim,
        x_dim=x_dim,
        time_idx=widgets['simulation']['time_player'],
        x_coords=x_coords,
        vars_list=pn.bind(parse_variables, widgets['simulation']['variables_input'])
    )

    # ========== Layout ==========
    dashboard = pn.Column(
        pn.Row(widgets['simulation']['variables_input']),
        line_plot_pane,
        pn.Row(widgets['simulation']['time_player']),
        sizing_mode='stretch_both'
    )

    # NcFiles
    nc = pn.Column(
        pn.pane.Markdown(f'**path:** {str(Path(input_file).resolve())}'),
        pn.pane.Markdown(f'**dimensions:** {", ".join([f"{key}({size})" for key, size in dict(ds.sizes).items()])}'),
        pn.pane.Markdown(f'**variables:** {", ".join(ds.data_vars.keys())}'),
    )

    ncfiles = pn.Accordion(('nc', nc), active=[0])
       
    sidebar_content = [
        pn.pane.Markdown('# NetCDF Files'),
        ncfiles,
    ]

    template = pn.template.BootstrapTemplate(
        title='NcViewer - Plot 1D',
        sidebar=sidebar_content,
        main=[dashboard],
    )

    print(f'\nStarting Panel server...')
    print('Press Ctrl+C to stop\n')
    template.show()