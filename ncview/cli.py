"""Command line interface for NcView

Main CLI entry point with lazy module imports.
Each subcommand imports only its required module to minimize startup time.
"""
import argparse
import sys


def build_parser():
    parser = argparse.ArgumentParser(
        prog="ncv",
        description="NetCDF Viewer"
    )
    sub = parser.add_subparsers(dest="cmd", required=False)

    # Data inspection commands (fast - only xarray)
    p_info = sub.add_parser("info", help="Display NetCDF file information")
    p_info.add_argument("file", help="Path to NetCDF file")

    p_dimensions = sub.add_parser("dimensions", help="Display dimensions and their sizes")
    p_dimensions.add_argument("file", help="Path to NetCDF file")

    p_variables = sub.add_parser("variables", help="List variables with descriptions")
    p_variables.add_argument("file", help="Path to NetCDF file")

    p_summary = sub.add_parser("summary", help="Show statistical summary of variable(s)")
    p_summary.add_argument("file", help="Path to NetCDF file")
    p_summary.add_argument("var", nargs="?", help="Variable name (optional, shows all if omitted)")

    # Plotting commands (slower - loads matplotlib/hvplot)
    p_plot1d = sub.add_parser("plot1d", help="Generate 1D plot at specific time")
    p_plot1d.add_argument("file", help="Path to NetCDF file")
    p_plot1d.add_argument("vars", nargs="+", help="Variable name(s) or expression(s) to plot")
    p_plot1d.add_argument("-t", "--time", required=True, help="Time index (integer) or datetime string")
    p_plot1d.add_argument("-o", "--output", help="Output file path (PNG, PDF, etc.)")
    p_plot1d.add_argument("--hvplot", action="store_true", help="Use hvplot instead of matplotlib")

    # Code checking commands
    p_check_order = sub.add_parser("check_order", help="Check code order from NetCDF input files")
    p_check_order.add_argument("-samples", nargs="+", required=True, help="Path(s) to sample NetCDF file(s) (last one is used as reference)")
    p_check_order.add_argument("-vars", nargs="+", required=True, help="Variable name(s) to check")

    return parser


def main(argv=None):
    argv = argv or sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args or not getattr(args, "cmd", None):
        parser.print_help()
        return 1

    try:
        if args.cmd in ("info", "dimensions", "variables", "summary"):
            from . import _inspect
            
            if args.cmd == "info":
                _inspect.print_info(args.file)
            elif args.cmd == "dimensions":
                _inspect.dimensions(args.file)
            elif args.cmd == "variables":
                _inspect.list_variables(args.file)
            elif args.cmd == "summary":
                _inspect.summary(args.file, args.var)
        
        elif args.cmd == "plot1d":
            from . import _plot1d
            
            _plot1d.plot1d(
                args.file,
                args.vars,
                args.time,
                args.output,
                args.hvplot
            )
        
        elif args.cmd == "check_order":
            from . import _check_order
            
            _check_order.check_order(args.samples, args.vars)
                
        else:
            parser.print_help()
            return 1
            
    except FileNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 2
    except KeyError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
