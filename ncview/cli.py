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
