"""
Numerical scheme order checking utilities for ncviewer.

This module handles numerical scheme order verification from NetCDF sample files.
"""
import sys
from pathlib import Path
from ._utils import open_dataset
from ._math import evaluate_expression, compute_error
import numpy as np
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *

def compute_table(sample_files, ref_file, variables=None, time_index=None, norm_error=DEFAULT_ERROR_NORM):
    """
    Compute convergence order table for multiple NetCDF files.
    
    Compares sample files (coarse grids) against a reference file (fine grid)
    by projecting the fine grid onto each coarse grid and computing errors.
    
    Args:
        sample_files: List of paths to sample NetCDF files (coarse grids)
        ref_file: Path to reference NetCDF file (finest grid)
        variables: Optional list of variable names or expressions to analyze.
                   If None, uses all common variables.
        time_index: Optional time index to analyze (default: last time step)
        norm_error: Error norm to use ('1', '2', 'inf')
    """
    from ._utils import coarsen_grid
    
    # Open reference file
    ds_ref = open_dataset(ref_file)
    
    print(f"\nConvergence order analysis")
    print(SEPARATOR_CHAR * SEPARATOR_LENGTH)
    print(f"Reference file: {str(Path(ref_file).resolve())}")
    print(f"Sample files: {len(sample_files)}")
    for i, f in enumerate(sample_files, 1):
        print(f"  [{i}] {str(Path(f).resolve())}")
    print(SEPARATOR_CHAR * SEPARATOR_LENGTH)
    
    # Detect time dimension
    time_dim = None
    if hasattr(ds_ref, 'encoding') and 'unlimited_dims' in ds_ref.encoding:
        unlimited_dims = list(ds_ref.encoding['unlimited_dims'])
        if unlimited_dims:
            time_dim = unlimited_dims[0]
    
    if time_dim is None:
        for dim in TIME_DIMENSION_NAMES:
            if dim in ds_ref.dims:
                time_dim = dim
                break
    
    # Identify spatial dimensions
    x_dim = None
    y_dim = None
    for dim in ds_ref.dims:
        if dim == time_dim:
            continue
        if dim in X_DIMENSION_NAMES or dim.lower() in [x.lower() for x in X_DIMENSION_NAMES]:
            x_dim = dim
        elif dim in Y_DIMENSION_NAMES or dim.lower() in [y.lower() for y in Y_DIMENSION_NAMES]:
            y_dim = dim
    
    # Determine grid type
    if x_dim and not y_dim:
        grid_type = '1D'
        spatial_dims = [x_dim]
        print(f"Grid type: 1D (spatial dimension: {x_dim})")
    elif x_dim and y_dim:
        grid_type = '2D'
        spatial_dims = [y_dim, x_dim]  # Order matters: (y, x)
        print(f"Grid type: 2D (spatial dimensions: {y_dim}, {x_dim})")
    else:
        print("✗ Error: Could not detect spatial dimensions")
        ds_ref.close()
        return
    
    # Get reference grid sizes
    if grid_type == '1D':
        n_ref = ds_ref.sizes[x_dim]
        print(f"Reference grid size: {x_dim}={n_ref}")
    else:  # 2D
        ny_ref = ds_ref.sizes[y_dim]
        nx_ref = ds_ref.sizes[x_dim]
        print(f"Reference grid size: {y_dim}={ny_ref}, {x_dim}={nx_ref}")
    
    # Determine time index (default: last)
    if time_dim:
        if time_index is None:
            time_index = ds_ref.sizes[time_dim] - 1
            print(f"Time index: {time_index} (last, {time_dim}={ds_ref[time_dim].values[time_index]:.3e})")
        else:
            if time_index >= ds_ref.sizes[time_dim] or time_index < 0:
                print(f"✗ Error: Time index {time_index} out of range [0, {ds_ref.sizes[time_dim]-1}]")
                ds_ref.close()
                return
            print(f"Time index: {time_index} ({time_dim}={ds_ref[time_dim].values[time_index]:.3e})")
    else:
        time_index = None
        print("No time dimension detected")
    
    # Determine variables to analyze
    if variables is None:
        variables = list(ds_ref.data_vars.keys())
        print(f"Variables: all ({len(variables)} found)")
    else:
        print(f"Variables: {variables}")
    
    print(f"Norm: {norm_error}")
    print(SEPARATOR_CHAR * SEPARATOR_LENGTH)
    
    # Validate sample files and collect grid info
    sample_info = []
    print("Validating sample files...")
    
    for i, sample_file in enumerate(sample_files, 1):
        ds_sample = open_dataset(sample_file)
        
        # Check spatial dimensions exist
        for dim in spatial_dims:
            if dim not in ds_sample.dims:
                print(f"✗ Error: Sample file {i} missing dimension '{dim}'")
                ds_sample.close()
                ds_ref.close()
                return
        
        # Get grid sizes
        if grid_type == '1D':
            n_sample = ds_sample.sizes[x_dim]
            
            # Validate: reference must be finer (more points)
            if n_ref <= n_sample:
                print(f"✗ Error: Sample [{i}] '{Path(sample_file).name}' ({x_dim}={n_sample}) is not coarser than reference ({x_dim}={n_ref})")
                ds_sample.close()
                ds_ref.close()
                return
            
            # Validate: reference must be exact multiple
            if n_ref % n_sample != 0:
                print(f"✗ Error: Sample [{i}] '{Path(sample_file).name}' ({x_dim}={n_sample}) is not compatible with reference ({x_dim}={n_ref})")
                print(f"  Reason: {n_ref} is not divisible by {n_sample}")
                ds_sample.close()
                ds_ref.close()
                return
            
            refinement = n_ref // n_sample
            sample_info.append({
                'file': sample_file,
                'ds': ds_sample,
                'n': n_sample,
                'refinement': (refinement,),
                'dx': np.abs(ds_sample[x_dim].values[1] - ds_sample[x_dim].values[0]) if len(ds_sample[x_dim].values) > 1 else 1.0
            })
            print(f"  [{i}] {Path(sample_file).name}: {x_dim}={n_sample}, refinement={refinement}x")
            
        else:  # 2D
            ny_sample = ds_sample.sizes[y_dim]
            nx_sample = ds_sample.sizes[x_dim]
            
            # Validate: reference must be finer
            if ny_ref <= ny_sample or nx_ref <= nx_sample:
                print(f"✗ Error: Sample [{i}] '{Path(sample_file).name}' ({y_dim}={ny_sample}, {x_dim}={nx_sample}) is not coarser than reference ({y_dim}={ny_ref}, {x_dim}={nx_ref})")
                ds_sample.close()
                ds_ref.close()
                return
            
            # Validate: reference must be exact multiple
            if ny_ref % ny_sample != 0 or nx_ref % nx_sample != 0:
                print(f"✗ Error: Sample [{i}] '{Path(sample_file).name}' ({y_dim}={ny_sample}, {x_dim}={nx_sample}) is not compatible with reference ({y_dim}={ny_ref}, {x_dim}={nx_ref})")
                print(f"  Reason: ({ny_ref}, {nx_ref}) is not divisible by ({ny_sample}, {nx_sample})")
                ds_sample.close()
                ds_ref.close()
                return
            
            ry = ny_ref // ny_sample
            rx = nx_ref // nx_sample
            dx = np.abs(ds_sample[x_dim].values[1] - ds_sample[x_dim].values[0]) if len(ds_sample[x_dim].values) > 1 else 1.0
            dy = np.abs(ds_sample[y_dim].values[1] - ds_sample[y_dim].values[0]) if len(ds_sample[y_dim].values) > 1 else 1.0
            
            sample_info.append({
                'file': sample_file,
                'ds': ds_sample,
                'ny': ny_sample,
                'nx': nx_sample,
                'refinement': (ry, rx),
                'dx': dx,
                'dy': dy
            })
            print(f"  [{i}] {Path(sample_file).name}: {y_dim}={ny_sample}, {x_dim}={nx_sample}, refinement=({ry}y, {rx}x)")
    
    print("✓ All sample files validated")
    print(SEPARATOR_CHAR * SEPARATOR_LENGTH)
    
    # Load reference data for each variable
    print("Loading reference data...")
    ref_data = {}
    
    for var_expr in variables:
        # Check if it's an expression
        is_expression = any(op in var_expr for op in EXPRESSION_OPERATORS)
        
        try:
            if is_expression:
                var = evaluate_expression(ds_ref, var_expr)
            else:
                if var_expr not in ds_ref.data_vars:
                    print(f"✗ Warning: Variable '{var_expr}' not found in reference file, skipping")
                    continue
                var = ds_ref[var_expr]
            
            # Extract data at time index
            if time_dim and time_dim in var.dims:
                var_data = var.isel({time_dim: time_index}).values
            else:
                var_data = var.values
            
            ref_data[var_expr] = var_data
            print(f"  ✓ {var_expr}: shape={var_data.shape}")
            
        except Exception as e:
            print(f"✗ Warning: Could not load '{var_expr}': {e}, skipping")
            continue
    
    if not ref_data:
        print("\n✗ Error: No valid variables to analyze")
        for info in sample_info:
            info['ds'].close()
        ds_ref.close()
        return
    
    print(SEPARATOR_CHAR * SEPARATOR_LENGTH)
    
    # Compute errors for each sample and variable
    print("Computing errors...")
    errors = {var: [] for var in ref_data.keys()}
    
    for i, info in enumerate(sample_info, 1):
        ds_sample = info['ds']
        print(f"  Processing sample [{i}]...")
        
        for var_expr in ref_data.keys():
            try:
                # Load sample data
                is_expression = any(op in var_expr for op in EXPRESSION_OPERATORS)
                
                if is_expression:
                    var_sample = evaluate_expression(ds_sample, var_expr)
                else:
                    if var_expr not in ds_sample.data_vars:
                        print(f"    ✗ Variable '{var_expr}' not in sample, skipping")
                        errors[var_expr].append(np.nan)
                        continue
                    var_sample = ds_sample[var_expr]
                
                # Extract data at time index
                if time_dim and time_dim in var_sample.dims:
                    var_sample_data = var_sample.isel({time_dim: time_index}).values
                else:
                    var_sample_data = var_sample.values
                
                # Project reference onto sample grid
                var_ref_projected = coarsen_grid(ref_data[var_expr], info['refinement'])
                
                # Compute cell volume
                if grid_type == '1D':
                    cell_volume = info['dx']
                else:
                    cell_volume = info['dx'] * info['dy']
                
                # Compute error
                err = compute_error(var_sample_data, var_ref_projected, cell_volume, norm=norm_error)
                errors[var_expr].append(err)
                
            except Exception as e:
                print(f"    ✗ Error computing '{var_expr}': {e}")
                errors[var_expr].append(np.nan)
    
    print("✓ Errors computed")
    print(SEPARATOR_CHAR * SEPARATOR_LENGTH)
    
    # Compute orders
    orders = {var: [] for var in ref_data.keys()}
    
    for var in ref_data.keys():
        for i in range(1, len(sample_info)):
            if np.isnan(errors[var][i-1]) or np.isnan(errors[var][i]):
                orders[var].append("")
            else:
                # Compute h_ratio based on grid type
                if grid_type == '1D':
                    h_ratio = sample_info[i]['n'] / sample_info[i-1]['n']
                else:
                    # Use average of x and y ratios
                    h_ratio_x = sample_info[i]['nx'] / sample_info[i-1]['nx']
                    h_ratio_y = sample_info[i]['ny'] / sample_info[i-1]['ny']
                    h_ratio = (h_ratio_x + h_ratio_y) / 2.0
                
                if errors[var][i] > 0 and errors[var][i-1] > 0:
                    p = np.log(errors[var][i-1] / errors[var][i]) / np.log(h_ratio)
                    orders[var].append(f"{p:.3f}")
                else:
                    orders[var].append("")
        # First row has no order
        orders[var].insert(0, "")
    
    # Print results table
    print(f"\nOrder table in norm {norm_error} at {time_dim}={ds_ref[time_dim].values[time_index]:.3e}:")
    print(SEPARATOR_CHAR * SEPARATOR_LENGTH)
    
    # Build header
    if grid_type == '1D':
        header = f"{'cells x':>8}"
    else:
        header = f"{'cells y':>8} {'cells x':>8}"
    
    for var in ref_data.keys():
        var_short = var[:10] if len(var) <= 10 else var[:9] + "…"
        header += f" {'error '+var_short+'':>15} {'order '+var_short+'':>8}"
    
    print(header)
    print("-" * len(header))
    
    # Print data rows
    for i, info in enumerate(sample_info):
        if grid_type == '1D':
            row = f"{info['n']:8d}"
        else:
            row = f"{info['ny']:8d} {info['nx']:8d}"
        
        for var in ref_data.keys():
            if np.isnan(errors[var][i]):
                row += f" {'N/A':>15} {orders[var][i]:>8}"
            else:
                row += f" {errors[var][i]:15.6e} {orders[var][i]:>8}"
        
        print(row)
    
    print(SEPARATOR_CHAR * SEPARATOR_LENGTH)
    
    # Cleanup
    for info in sample_info:
        info['ds'].close()
    ds_ref.close()

