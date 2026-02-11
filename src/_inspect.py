"""
Data inspection utilities for ncviewer.

This module handles read-only operations on NetCDF files.
Only imports xarray/netCDF4 (lightweight, fast startup).
"""

import sys
from pathlib import Path
from ._utils import open_dataset
from ._math import evaluate_expression, compute_error
import numpy as np
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *

def print_info(path):
    """
    Display complete NetCDF dataset information.
    
    Shows dimensions, coordinates, variables, attributes, and metadata.
    
    Args:
        path: Path to NetCDF file
    """
    ds = open_dataset(path)
    print(f"\nInfo of {str(Path(path).resolve())}")
    print(SEPARATOR_CHAR * SEPARATOR_LENGTH)
    print(ds)
    print(SEPARATOR_CHAR * SEPARATOR_LENGTH)
    ds.close()

def list_dimensions(path):
    """
    Display dimensions of the NetCDF dataset.
    
    Shows dimension names, sizes, data types, memory usage, and value ranges.
    
    Args:
        path: Path to NetCDF file
    """
    ds = open_dataset(path)

    print(f"\nDimensions in {str(Path(path).resolve())}")
    print(SEPARATOR_CHAR * SEPARATOR_LENGTH)

    if not ds.sizes:
        print("No dimensions found in this NetCDF file.")
        ds.close()
        return

    unlimited_dims = list(ds.encoding.get('unlimited_dims', []))
    limited_dims = [dim for dim in ds.dims if dim not in unlimited_dims]

    print(f"Total: {len(ds.sizes)} dimension(s)")
    print(f"Unlimited dimensions ({len(unlimited_dims)}): {unlimited_dims}")
    print(f"Limited dimensions ({len(limited_dims)}): {limited_dims}")

    for dim_name, dim_size in ds.sizes.items():
        # Details
        print(f"\n{dim_name}:")
        print(f"  Size: {dim_size}")

        coord = ds[dim_name]
        dtype = str(coord.dtype)
        print(f"  Type: {dtype}")

        # Calculate memory size
        itemsize = coord.dtype.itemsize
        total_bytes = dim_size * itemsize

        # Format size in human-readable format
        if total_bytes < KB_THRESHOLD:
            size_str = f"{total_bytes} B"
        elif total_bytes < MB_THRESHOLD:
            size_str = f"{total_bytes/1024:.2f} KB"
        elif total_bytes < GB_THRESHOLD:
            size_str = f"{total_bytes/1024**2:.2f} MB"
        else:
            size_str = f"{total_bytes/1024**3:.2f} GB"

        print(f"  Memory: {size_str}")

        
        min_val = float(coord.min().values)
        max_val = float(coord.max().values)
        print(f"  Range: [{min_val:.4f}, {max_val:.4f}]")
        
    print(SEPARATOR_CHAR * SEPARATOR_LENGTH)

    ds.close()


def list_variables(path):
    """
    List all variables with key metadata and descriptions.
    
    Shows variable names, dimensions, shapes, types, and descriptions (if available).
    Suggests using 'summary' command for detailed statistics.
    
    Args:
        path: Path to NetCDF file
    """
    ds = open_dataset(path)
    
    print(f"\nVariables in {str(Path(path).resolve())}")
    print(SEPARATOR_CHAR * SEPARATOR_LENGTH)
    
    if not ds.data_vars:
        print("No data variables found in this NetCDF file.")
        ds.close()
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
    
    print(SEPARATOR_CHAR * SEPARATOR_LENGTH)
    print(f"Total: {len(ds.data_vars)} variable(s)")
    ds.close()

def summary(path, varname=None):
    """
    Display statistical summary of variable(s) or expressions.
    
    Args:
        path: Path to NetCDF file
        varname: Optional variable name or mathematical expression. 
                 If None, summarizes all variables.
                 Examples: 'h', 'h-H', 'temp*2', 'sqrt(u**2 + v**2)'
    """
    ds = open_dataset(path)
    
    if varname:
        # Check if it's an expression (contains operators or functions)
        is_expression = any(op in varname for op in EXPRESSION_OPERATORS)
        
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
            if not varname in ds.data_vars:
                available = ", ".join(list(ds.data_vars)[:5])
                if len(ds.data_vars) > 5:
                    available += f", ... ({len(ds.data_vars)} total)"
                print(f"✗ Error: Variable '{varname}' not found. Available variables: {available}", file=sys.stderr)
                return
            variables = [(varname, ds[varname])]
    else:
        # All variables
        variables = [(name, ds[name]) for name in ds.data_vars]
    
    print(f"\nVariables summary for {str(Path(path).resolve())}:")
    print(SEPARATOR_CHAR * SEPARATOR_LENGTH)
    
    for var_name, var in variables:
        print(f"\nVariable: {var_name}")
        print(f"  Dimensions: {var.dims}")
        print(f"  Shape: {var.shape}")
        print(f"  Type: {var.dtype}")
        # Try to compute statistics (skip if non-numeric)
        try:
            print(f"  Min: {float(var.min().values):.{STAT_PRECISION}f}")
            print(f"  Max: {float(var.max().values):.{STAT_PRECISION}f}")
            print(f"  Mean: {float(var.mean().values):.{STAT_PRECISION}f}")
            print(f"  Std: {float(var.std().values):.{STAT_PRECISION}f}")
        except (TypeError, ValueError):
            print("  (Non-numeric data, statistics not available)")
        # Print attributes if any (only for single variables, not expressions)
        if hasattr(var, 'attrs') and var.attrs and not any(op in var_name for op in EXPRESSION_OPERATORS):
            print("  Attributes:")
            for attr_name, attr_val in var.attrs.items():
                print(f"    {attr_name}: {attr_val}")
    
    print(SEPARATOR_CHAR * SEPARATOR_LENGTH)
    ds.close()

def error(path1, path2, time_index=None, norm_error=DEFAULT_ERROR_NORM):
    """
    Error analysis between two NetCDF files.
    
    Args:
        path1: Path to first NetCDF file
        path2: Path to second NetCDF file
        time_index: Optional specific time index to compare
    """
    
    ds1 = open_dataset(path1)
    ds2 = open_dataset(path2)
    
    print(f"\nErrors between:\n{str(Path(path1).resolve())} and {str(Path(path2).resolve())}")
    print(SEPARATOR_CHAR * SEPARATOR_LENGTH)
    
    print("checking dimension names...")
    dims1 = set(ds1.sizes.keys())
    dims2 = set(ds2.sizes.keys())
    
    if dims1 != dims2:
        print(f"✗ Dimension names differ:")
        print(f"  Only in file1: {dims1 - dims2}")
        print(f"  Only in file2: {dims2 - dims1}")
        return
    else:
        print("✓ Dimension names match")
    
    print("checking dimension sizes...")
    dims_match = True
    for dim in dims1:
        if ds1.sizes[dim] != ds2.sizes[dim]:
            print(f"✗ Dimension '{dim}': size mismatch ({ds1.sizes[dim]} vs {ds2.sizes[dim]})")
            dims_match = False
    
    if not dims_match:
        print("\n✗ Cannot compare: dimension sizes do not match")
        return
    else:
        print("✓ All dimensions match")

    print("checking coordinate nodes...")
    
    for coord_name in ds1.coords:
        if coord_name in ds2.coords:
            coord1 = ds1[coord_name].values
            coord2 = ds2[coord_name].values
            if not np.allclose(coord1, coord2, rtol=COORDINATE_RTOL, atol=COORDINATE_ATOL):
                max_diff = np.max(np.abs(coord1 - coord2))
                print(f"✗ Coordinate '{coord_name}': values differ (max diff: {max_diff:.2e})")
                return
    
    print("✓ All coordinate nodes match")
    
    print("finding variables to compare...")
    vars1 = set(ds1.data_vars.keys())
    vars2 = set(ds2.data_vars.keys())
    common_vars = vars1 & vars2
    
    if vars1 != vars2:
        print(f"Variables in both files: {len(common_vars)}")
        if vars1 - vars2:
            print(f"Only in file1: {vars1 - vars2}")
        if vars2 - vars1:
            print(f"Only in file2: {vars2 - vars1}")
    else:
        print(f"✓ {len(common_vars)} variables match")
    
    if not common_vars:
        print("\n✗ No common variables to compare")
        return
    
    print(f"computing errors for variables {sorted(common_vars)} in norm {norm_error}...")
    print("\nError results:")
    print(SEPARATOR_CHAR * SEPARATOR_LENGTH)
    
    # Detect time dimension
    time_dim = None
    # First try to find unlimited dimension
    if hasattr(ds1, 'encoding') and 'unlimited_dims' in ds1.encoding:
        unlimited_dims = list(ds1.encoding['unlimited_dims'])
        if unlimited_dims:
            time_dim = unlimited_dims[0]  # Use first unlimited dimension
    
    # If no unlimited dimension found, fall back to common time dimension names
    if time_dim is None:
        for dim in TIME_DIMENSION_NAMES:
            if dim in ds1.dims:
                time_dim = dim
                break

    # Identify spatial dimensions (x and y)
    x_dim = None
    y_dim = None
    for dim in ds1.dims:
        if dim == time_dim:
            continue
        dim_lower = dim.lower()
        if dim_lower in X_DIMENSION_NAMES:
            x_dim = dim
        elif dim_lower in Y_DIMENSION_NAMES:
            y_dim = dim
    
    # Calculate cell_volume based on grid type
    if x_dim and not y_dim:
        # 1D case: (t, x)
        if x_dim in ds1.coords and len(ds1[x_dim].values) > 1:
            dx = np.abs(ds1[x_dim].values[1] - ds1[x_dim].values[0])
            cell_volume = dx
            print(f"Grid type: 1D (uniform spacing dx={dx:.6e})")
        else:
            cell_volume = DEFAULT_CELL_VOLUME
            print(f"Grid type: 1D (no spacing info, using cell_volume={DEFAULT_CELL_VOLUME})")
    elif x_dim and y_dim:
        # 2D case: (t, y, x)
        dx = 1.0
        dy = 1.0
        if x_dim in ds1.coords and len(ds1[x_dim].values) > 1:
            dx = np.abs(ds1[x_dim].values[1] - ds1[x_dim].values[0])
        if y_dim in ds1.coords and len(ds1[y_dim].values) > 1:
            dy = np.abs(ds1[y_dim].values[1] - ds1[y_dim].values[0])
        cell_volume = dx * dy
        print(f"Grid type: 2D (uniform spacing dx={dx:.6e}, dy={dy:.6e})")
    else:
        # Fallback: no spatial dimensions detected
        cell_volume = DEFAULT_CELL_VOLUME
        print(f"Grid type: Unknown (using cell_volume={DEFAULT_CELL_VOLUME})")
    
    for var_name in sorted(common_vars):
        var1 = ds1[var_name]
        var2 = ds2[var_name]
        
        # Check if shapes match
        if var1.shape != var2.shape:
            print(f"\n{var_name}: ✗ Shape mismatch ({var1.shape} vs {var2.shape})")
            continue
        
        print(f"\n{var_name}:")
        print(f"  Dimensions: {var1.dims}")
        print(f"  Shape: {var1.shape}")
        
        # Check if variable has time dimension
        has_time = time_dim and time_dim in var1.dims
        
        if has_time and time_index is None:
            # Compare all time steps
            time_size = var1.sizes[time_dim]
            errors = []
            
            for t in range(time_size):
                v1_t = var1.isel({time_dim: t}).values
                v2_t = var2.isel({time_dim: t}).values
                err = compute_error(v1_t, v2_t, cell_volume, norm=norm_error)
                errors.append(err)
            
            errors = np.array(errors)
            total_error = np.sum(errors)
            mean_error = np.mean(errors)
            max_idx = np.argmax(errors)
            min_idx = np.argmin(errors)
            
            print(f"  Total error ({time_dim} summation) = {total_error:.6e}")
            print(f"  Mean error = {mean_error:.6e}")
            print(f"  Max error = {errors[max_idx]:.6e} at time={ds1[time_dim].values[max_idx]:.3e}")
            print(f"  Min error = {errors[min_idx]:.6e} at time={ds1[time_dim].values[min_idx]:.3e}")
            
        elif has_time and time_index is not None:
            if time_index >= var1.sizes[time_dim]:
                print(f"  ✗ Time index {time_index} out of range (max: {var1.sizes[time_dim]-1})")
                continue
            
            v1_t = var1.isel({time_dim: time_index}).values
            v2_t = var2.isel({time_dim: time_index}).values
            err = compute_error(v1_t, v2_t, cell_volume, norm=norm_error)
            
            print(f"  Error = {err:.6e} at {time_dim}={ds1[time_dim].values[time_index]:.3e}")
            
        else:
            # No time dimension, compare directly
            v1 = var1.values
            v2 = var2.values
            err = compute_error(v1, v2, cell_volume, norm=norm_error)
            
            print(f"  Error: {err:.6e}")
    
    print("\n" + SEPARATOR_CHAR * SEPARATOR_LENGTH)
    ds1.close()
    ds2.close()
