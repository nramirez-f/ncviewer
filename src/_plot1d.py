import hvplot.pandas
import numpy as np
import pandas as pd
import panel as pn

def launch_panel_server(port=2700):
    """Launch a Panel web server for interactive 1D plotting.
    
    Args:
        port: Port number for the server (default: 2700)
    
    Returns:
        0 on success, 1 on error
    """
    
    
    PRIMARY_COLOR = "#0072B5"
    SECONDARY_COLOR = "#B54300"
    CSV_FILE = (
       "https://raw.githubusercontent.com/holoviz/panel/main/examples/assets/occupancy.csv"
    )
    
    pn.extension(design="material", sizing_mode="stretch_width")
    
    @pn.cache
    def get_data():
    return pd.read_csv(CSV_FILE, parse_dates=["date"], index_col="date")

    data = get_data()

    data.tail()

    # Crear una aplicación básica de Panel
    def create_app():
        return pn.Column(
            "# NCViewer - Interactive 1D Plotting",
            "Panel server running successfully!",
        )
    
    app = create_app()
    
    print(f"Launching Panel server on port {port}...")
    print(f"Open http://localhost:{port} in your browser")
    print("Press Ctrl+C to stop the server\n")
    
    try:
        # Servir la aplicación
        app.show(port=port, threaded=False)
        return 0
    except Exception as e:
        print(f"✗ Error starting server: {e}", file=sys.stderr)
        return 1