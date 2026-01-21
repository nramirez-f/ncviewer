"""Data inspection utilities for ncviewer.

This module handles read-only operations on NetCDF files.
Only imports xarray/netCDF4 (lightweight, fast startup).
"""
import sys
from pathlib import Path
from ._utils import open_dataset, validate_variable
from ._math import evaluate_expression


def print_info(path):
    """Display complete NetCDF dataset information.
    
    Shows dimensions, coordinates, variables, attributes, and metadata.
    
    Args:
        path: Path to NetCDF file
    """
    ds = open_dataset(path)
    print(f"\nInfo of {Path(path).name}")
    print("=" * 80)
    print(ds)
    print("=" * 80)


def dimensions(path):
    """Display dimensions of the NetCDF dataset.
    
    Shows dimension names, sizes, data types, memory usage, and value ranges.
    
    Args:
        path: Path to NetCDF file
    """
    ds = open_dataset(path)
    
    print(f"\nDimensions in {Path(path).name}")
    print("=" * 80)
    
    if not ds.sizes:
        print("No dimensions found in this NetCDF file.")
        return
    
    for dim_name, dim_size in ds.sizes.items():
        # Check if dimension is unlimited
        unlimited = ""
        if hasattr(ds, 'encoding') and 'unlimited_dims' in ds.encoding:
            if dim_name in ds.encoding['unlimited_dims']:
                unlimited = " (UNLIMITED)"
        
        print(f"\n{dim_name}:")
        print(f"  Size: {dim_size}{unlimited}")
        
        # Check if this dimension has coordinate values
        if dim_name in ds.coords:
            coord = ds[dim_name]
            dtype = str(coord.dtype)
            print(f"  Type: {dtype}")
            
            # Calculate memory size
            itemsize = coord.dtype.itemsize
            total_bytes = dim_size * itemsize
            
            # Format size in human-readable format
            if total_bytes < 1024:
                size_str = f"{total_bytes} B"
            elif total_bytes < 1024**2:
                size_str = f"{total_bytes/1024:.2f} KB"
            elif total_bytes < 1024**3:
                size_str = f"{total_bytes/1024**2:.2f} MB"
            else:
                size_str = f"{total_bytes/1024**3:.2f} GB"
            
            print(f"  Memory: {size_str}")
            
            # Try to compute min/max (skip if non-numeric)
            try:
                min_val = float(coord.min().values)
                max_val = float(coord.max().values)
                print(f"  Range: [{min_val:.4f}, {max_val:.4f}]")
            except (TypeError, ValueError):
                print(f"  Range: (Non-numeric)")
        else:
            print(f"  (No coordinate variable)")
    
    print("\n" + "=" * 80)
    print(f"Total: {len(ds.sizes)} dimension(s)")


def list_variables(path):
    """List all variables with key metadata and descriptions.
    
    Shows variable names, dimensions, shapes, types, and descriptions (if available).
    Suggests using 'summary' command for detailed statistics.
    
    Args:
        path: Path to NetCDF file
    """
    ds = open_dataset(path)
    
    print(f"Variables in {Path(path).name}")
    print("=" * 80)
    
    if not ds.data_vars:
        print("No data variables found in this NetCDF file.")
        return
    
    for name in ds.data_vars:
        var = ds[name]
        dims = ", ".join(var.dims) if var.dims else "scalar"
        shape = var.shape
        dtype = str(var.dtype)
        
        print(f"- {name}:")
        print(f"    Dims: ({dims})")
        print(f"    Shape: {shape}")
        print(f"    Type: {dtype:<12}")
        
        for attr_name, attr_val in var.attrs.items():
                print(f"    {attr_name}: {attr_val}")
    
    print("=" * 80)
    print(f"Total: {len(ds.data_vars)} variable(s)")
    print(f"Tip:    Use 'ncv summary {Path(path).name}' for detailed statistics")
    print(f"        Use 'ncv summary {Path(path).name} <var_name>' for a specific variable")

def summary(path, varname=None):
    """Display statistical summary of variable(s) or expressions.
    
    Args:
        path: Path to NetCDF file
        varname: Optional variable name or mathematical expression. 
                 If None, summarizes all variables.
                 Examples: 'h', 'h-H', 'temp*2', 'sqrt(u**2 + v**2)'
    """
    ds = open_dataset(path)
    
    if varname:
        # Check if it's an expression (contains operators or functions)
        is_expression = any(op in varname for op in ['+', '-', '*', '/', '**', '(', ')'])
        
        if is_expression:
            # Evaluate the expression
            try:
                var = evaluate_expression(ds, varname)
                variables = [(varname, var)]
            except (KeyError, SyntaxError) as e:
                print(f"✗ Error: {e}", file=sys.stderr)
                return
        else:
            # Single variable
            validate_variable(ds, varname)
            variables = [(varname, ds[varname])]
    else:
        # All variables
        variables = [(name, ds[name]) for name in ds.data_vars]
    
    print(f"Summary for {Path(path).name}:")
    print("=" * 80)
    
    for var_name, var in variables:
        print(f"\nVariable: {var_name}")
        print(f"  Dimensions: {var.dims}")
        print(f"  Shape: {var.shape}")
        print(f"  Type: {var.dtype}")
        
        # Try to compute statistics (skip if non-numeric)
        try:
            print(f"  Min: {float(var.min().values):.4f}")
            print(f"  Max: {float(var.max().values):.4f}")
            print(f"  Mean: {float(var.mean().values):.4f}")
            print(f"  Std: {float(var.std().values):.4f}")
        except (TypeError, ValueError):
            print("  (Non-numeric data, statistics not available)")
        
        # Print attributes if any (only for single variables, not expressions)
        if hasattr(var, 'attrs') and var.attrs and not any(op in var_name for op in ['+', '-', '*', '/', '**', '(', ')']):
            print("  Attributes:")
            for attr_name, attr_val in var.attrs.items():
                print(f"    {attr_name}: {attr_val}")
    
    print("=" * 80)
