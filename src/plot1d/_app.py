import panel as pn

import sys
from src import _utils
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

    # Bindings
    from ._plotter import line_plot

    line_plot_pane = pn.bind(
        line_plot,
        ds=ds,
        time_dim=time_dim,
        time_idx=widgets['simulation']['time_player'],
        x_coords=x_coords,
        var=widgets['simulation']['variable']
    )

    # Layout
    simulation_controls = pn.Column(
        widgets['simulation']['time_player'],
        widgets['simulation']['variable'],
        sizing_mode='stretch_width'
    )

    dashboard = pn.Row(
        pn.pane.Markdown('# Line Plot'),
        line_plot_pane,
        align='center',
        sizing_mode='scale_both'
    )
       
    sidebar_content = [
        pn.pane.Markdown('## Dataset Info'),
        pn.pane.Markdown(f'**File:** {input_file}'),
        pn.pane.Markdown(f'**Variables:** {", ".join(ds.data_vars.keys())}'),
        pn.pane.Markdown(f'**Dimensions:**'),
        *[pn.pane.Markdown(f'- {key}: {size}') for key, size in dict(ds.sizes).items()],
        pn.layout.Divider(),
        pn.pane.Markdown('## Controls'),
        pn.Accordion(
            ('Simulation', simulation_controls),
            active=[0]
        ),
    ]

    template = pn.template.BootstrapTemplate(
        title='NcViewer - Plot 1D',
        sidebar=sidebar_content,
        main=[dashboard],
    )

    print(f'\nStarting Panel server...')
    print('Press Ctrl+C to stop\n')
    template.show()