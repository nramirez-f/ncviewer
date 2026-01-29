"""Command line interface for ncviewer

Main CLI entry point with lazy module imports.
Each subcommand imports only its required module to minimize startup time.
"""
import argparse
import sys
from . import __version__


# Command definitions (single source of truth)
COMMANDS = {
    "ncinfo": {
        "description": "Display NetCDF file information",
        "args": [("file", {"help": "Path to NetCDF file"})],
    },
    "ncdim": {
        "description": "Display dimensions and their sizes",
        "args": [("file", {"help": "Path to NetCDF file"})],
    },
    "ncvar": {
        "description": "List variables with descriptions",
        "args": [("file", {"help": "Path to NetCDF file"})],
    },
    "ncsum": {
        "description": "Show statistical summary of variable(s)",
        "args": [
            ("file", {"help": "Path to NetCDF file"}),
            ("var", {"nargs": "?", "help": "Variable name (optional, shows all if omitted)"}),
        ],
    },
    "ncsnap1d": {
        "description": "Generate 1D snapshot at specific time",
        "args": [
            ("file", {"help": "Path to NetCDF file"}),
            ("vars", {"nargs": "+", "help": "Variable name(s) or expression(s) to plot"}),
        ],
        "optional_args": [
            (["-t", "--time"], {"required": True, "help": "Time index (integer) or datetime string"}),
            (["-o", "--output"], {"help": "Output file path (PNG, PDF, etc.)"}),
            (["--hvplot"], {"action": "store_true", "help": "Use hvplot instead of matplotlib"}),
        ],
    },
    "ncerr": {
        "description": "Compute error between two NetCDF files",
        "args": [
            ("file1", {"help": "Path to NetCDF firstfile"}),
            ("file2", {"help": "Path to NetCDF second file"}),
        ],
        "optional_args": [
            (["-t", "--time"], {"type": int, "help": "Specific time index to compare (optional)"}),
        ],
    },
    "ncmov2d": {
        "description": "Create 2D animations from NetCDF files (MP4/GIF)",
        "args": [
            ("file", {"help": "Path to NetCDF file"}),
            ("variable", {"help": "Variable name to animate"}),
        ],
        "optional_args": [
            (["-o", "--output"], {"help": "Output file path (auto-generated if omitted)"}),
            (["-f", "--format"], {"choices": ["mp4", "gif"], "default": "mp4", "help": "Output format (default: mp4)"}),
            (["--time-dim"], {"default": "time", "help": "Name of time dimension (default: time)"}),
            (["--x-dim"], {"default": "x", "help": "Name of X spatial dimension (default: x)"}),
            (["--y-dim"], {"default": "y", "help": "Name of Y spatial dimension (default: y)"}),
            (["--time-start"], {"type": int, "default": 0, "help": "Start time index (default: 0)"}),
            (["--time-end"], {"type": int, "help": "End time index (default: all)"}),
            (["--time-step"], {"type": int, "default": 1, "help": "Time step (default: 1)"}),
            (["--fps"], {"type": int, "default": 10, "help": "Frames per second (default: 10)"}),
            (["--cmap"], {"default": "viridis", "help": "Matplotlib colormap (default: viridis)"}),
            (["--levels"], {"type": int, "default": 50, "help": "Number of contour levels (default: 50)"}),
            (["--vmin"], {"type": float, "help": "Minimum value for colorbar (auto if omitted)"}),
            (["--vmax"], {"type": float, "help": "Maximum value for colorbar (auto if omitted)"}),
            (["--fixed-scale"], {"action": "store_true", "help": "Use fixed colorbar scale across all frames"}),
            (["--no-auto-res"], {"action": "store_true", "help": "Disable automatic resolution adjustment"}),
            (["--figsize"], {"nargs": 2, "type": float, "metavar": ("WIDTH", "HEIGHT"), "help": "Figure size in inches (default: 10 8)"}),
            (["--dpi"], {"type": int, "default": 100, "help": "DPI for output (default: 100)"}),
            (["--title"], {"help": "Custom plot title (default: variable name)"}),
            (["--no-time"], {"action": "store_true", "help": "Don't show time in title"}),
            (["--no-colorbar"], {"action": "store_true", "help": "Don't show colorbar"}),
        ],
    },
    "ncplot2d": {
        "description": "Launch interactive 2D plotting server",
        "args": [
            ("file", {"help": "Path to NetCDF file"}),
        ],
        "optional_args": [
            (["--time-dim"], {"default": "time", "help": "Name of time dimension (default: time)"}),
            (["--x-dim"], {"default": "x", "help": "Name of X spatial dimension (default: x)"}),
            (["--y-dim"], {"default": "y", "help": "Name of Y spatial dimension (default: y)"}),
        ],
    },
    "ncplot1d": {
        "description": "Launch interactive 1D plotting server",
        "args": [
            ("file", {"help": "Path to NetCDF file"}),
        ],
        "optional_args": [
            (["--time-dim"], {"default": "time", "help": "Name of time dimension (default: time)"}),
            (["--x-dim"], {"default": "x", "help": "Name of X spatial dimension (default: x)"}),
            (["--y-dim"], {"default": "y", "help": "Name of Y spatial dimension (default: y)"}),
        ],
    },
}

def _create_parser(prog, config):
    """Create parser from command configuration"""
    parser = argparse.ArgumentParser(prog=prog, description=config["description"])
    
    # Add positional/required arguments
    for arg_name, arg_config in config["args"]:
        parser.add_argument(arg_name, **arg_config)
    
    # Add optional arguments if any
    for opt_names, opt_config in config.get("optional_args", []):
        parser.add_argument(*opt_names, **opt_config)
    
    return parser


def ncinfo():
    """Entry point for ncinfo command"""
    parser = _create_parser("ncinfo", COMMANDS["ncinfo"])
    args = parser.parse_args()
    
    try:
        from . import _inspect
        _inspect.print_info(args.file)
        return 0
    except FileNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return 1

def ncerr():
    """Entry point for ncerr command"""
    parser = _create_parser("ncerr", COMMANDS["ncerr"])
    args = parser.parse_args()
    
    try:
        from . import _inspect
        _inspect.error(args.file1, args.file2, time_index=args.time)
        return 0
    except FileNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return 1

def ncdim():
    """Entry point for ncdim command"""
    parser = _create_parser("ncdim", COMMANDS["ncdim"])
    args = parser.parse_args()
    
    try:
        from . import _inspect
        _inspect.dimensions(args.file)
        return 0
    except FileNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return 1


def ncvar():
    """Entry point for ncvar command"""
    parser = _create_parser("ncvar", COMMANDS["ncvar"])
    args = parser.parse_args()
    
    try:
        from . import _inspect
        _inspect.list_variables(args.file)
        return 0
    except FileNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return 1


def ncsum():
    """Entry point for ncsum command"""
    parser = _create_parser("ncsum", COMMANDS["ncsum"])
    args = parser.parse_args()
    
    try:
        from . import _inspect
        _inspect.summary(args.file, args.var)
        return 0
    except FileNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 2
    except KeyError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return 1


def ncsnap1d():
    """Entry point for ncsnap1d command"""
    parser = _create_parser("ncsnap1d", COMMANDS["ncsnap1d"])
    args = parser.parse_args()
    
    try:
        from . import _snap1d
        _snap1d.plot1d(args.file, args.vars, args.time, args.output, args.hvplot)
        return 0
    except FileNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return 1


def ncmov2d():
    """Entry point for ncmov2d command - Create 2D animations"""
    parser = _create_parser("ncmov2d", COMMANDS["ncmov2d"])
    args = parser.parse_args()
    
    try:
        from . import _mov2d
        
        # Handle figsize conversion
        figsize = tuple(args.figsize) if args.figsize else (10, 8)
        
        _mov2d.create_animation(
            input_file=args.file,
            variable=args.variable,
            output_file=args.output,
            output_format=args.format,
            time_dim=args.time_dim,
            x_dim=args.x_dim,
            y_dim=args.y_dim,
            time_start=args.time_start,
            time_end=args.time_end,
            time_step=args.time_step,
            fps=args.fps,
            cmap=args.cmap,
            levels=args.levels,
            vmin=args.vmin,
            vmax=args.vmax,
            time_dependent_scale=not args.fixed_scale,
            auto_resolution=not args.no_auto_res,
            figsize=figsize,
            dpi=args.dpi,
            custom_title=args.title,
            show_time=not args.no_time,
            show_colorbar=not args.no_colorbar,
        )
        return 0
    except FileNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return 1


def ncplot2d():
    """Entry point for ncplot2d command - Launch interactive 2D plotting server"""
    parser = _create_parser("ncplot2d", COMMANDS["ncplot2d"])
    args = parser.parse_args()
    
    try:
        from .plot2d import launch_server
        launch_server(
            input_file=args.file,
            time_dim=args.time_dim,
            x_dim=args.x_dim,
            y_dim=args.y_dim
        )
        return 0
    except FileNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return 1
    
def ncplot1d():
    """
    Entry point for ncplot1d command - Launch interactive 1D plotting server
    """
    parser = _create_parser("ncplot1d", COMMANDS["ncplot1d"])
    args = parser.parse_args()
    
    try:
        from .plot1d import launch_server
        launch_server(
            input_file=args.file,
            time_dim=args.time_dim,
            x_dim=args.x_dim
        )
        return 0
    except FileNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return 1


def main(argv=None):
    """Main entry point for ncviewer command"""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="ncviewer",
        description="NetCDF Viewer - Quick NetCDF file exploration tool"
    )
    sub = parser.add_subparsers(dest="cmd", required=False)

    sub.add_parser("commands", help="List all available commands")
    args = parser.parse_args(argv)

    if not args or not getattr(args, "cmd", None):
        print(80*"═")
        print(f"NetCDF Viewer (version {__version__})".center(80))
        print(80*"═")
        print()
        print("Quick NetCDF file exploration tool")
        print()
        print("Run 'ncviewer commands' to list all available commands.")
        return 0

    if args.cmd == "commands":
        print("Available commands:\n")
        for cmd in sorted(COMMANDS.keys()):
            desc = COMMANDS[cmd]["description"]
            print(f"  {cmd:<12} - {desc}")
        print()
        print("Run any command with --help for detailed usage")
        return 0

    # Should not reach here
    parser.print_help()
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
