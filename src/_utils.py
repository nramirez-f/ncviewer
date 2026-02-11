"""Common utilities for ncviewer modules.

Shared functionality used by both _inspect.py and _plot.py.
Only imports lightweight dependencies (pathlib, xarray).
"""
from pathlib import Path
import xarray as xr
import numpy as np


def open_dataset(path):
    """
    Open a NetCDF file and return xarray Dataset.
    
    Centralized file opening with validation.
    
    Args:
        path: Path to NetCDF file (str or Path)
        
    Returns:
        xarray.Dataset
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return xr.open_dataset(p)

def count_unlimited_dimensions(path):
    """
    Check how many spatial (non-unlimited) dimensions a NetCDF file has.

    Args:
        path: Path to NetCDF file (str or Path)

    Returns:
        int: Number of spatial dimensions (1, 2, or 3)
    """
    ds = open_dataset(path)
    spatial_dims = [
        dim for dim in ds.dims
        if not ds.encoding.get('unlimited_dims', []) or dim not in ds.encoding['unlimited_dims']
    ]
    # If unlimited_dims is not set, fallback to _is_unlimited_dim attribute
    if not ds.encoding.get('unlimited_dims', []):
        spatial_dims = [
            dim for dim in ds.dims
            if not getattr(ds.dims[dim], '_is_unlimited_dim', False)
        ]
    return len(spatial_dims)

def count_limited_dimensions(path):
    """
    Check how many temporal (unlimited) dimensions a NetCDF file has.

    Args:
        path: Path to NetCDF file (str or Path)

    Returns:
        int: Number of temporal (unlimited) dimensions
    """
    ds = open_dataset(path)
    unlimited_dims = ds.encoding.get('unlimited_dims', [])
    # If unlimited_dims is not set, fallback to _is_unlimited_dim attribute
    if not unlimited_dims:
        unlimited_dims = [
            dim for dim in ds.dims
            if getattr(ds.dims[dim], '_is_unlimited_dim', False)
        ]
    return len(unlimited_dims)

def coarsen_grid(var_fine, refinement_ratios):
    """
    Project fine grid variable onto coarse grid using conservative averaging.
    
    For each coarse cell, computes the mean of all fine cells within it.
    Supports 1D and 2D spatial grids.
    
    Args:
        var_fine: numpy array of fine grid values
                  Shape: (nx_fine,) for 1D or (ny_fine, nx_fine) for 2D
        refinement_ratios: tuple of refinement ratios (rx,) for 1D or (ry, rx) for 2D
                           rx = nx_fine / nx_coarse (must be integer)
                           ry = ny_fine / ny_coarse (must be integer)
    
    Returns:
        numpy array of coarse grid values
        Shape: (nx_coarse,) for 1D or (ny_coarse, nx_coarse) for 2D
        
    Raises:
        ValueError: If refinement ratios are not integers or dimensions incompatible
    """
    if len(var_fine.shape) == 1:
        # 1D case
        nx_f = var_fine.shape[0]
        rx = refinement_ratios[0]
        
        if not np.isclose(rx, round(rx)):
            raise ValueError(f"Refinement ratio rx={rx} is not an integer")
        rx = int(round(rx))
        
        if nx_f % rx != 0:
            raise ValueError(f"Fine grid size {nx_f} not divisible by refinement ratio {rx}")
        
        nx_c = nx_f // rx
        var_coarse = np.zeros(nx_c)
        
        for i in range(nx_c):
            var_coarse[i] = np.mean(var_fine[i*rx:(i+1)*rx])
        
        return var_coarse
        
    elif len(var_fine.shape) == 2:
        # 2D case
        ny_f, nx_f = var_fine.shape
        ry, rx = refinement_ratios
        
        if not np.isclose(rx, round(rx)) or not np.isclose(ry, round(ry)):
            raise ValueError(f"Refinement ratios rx={rx}, ry={ry} are not integers")
        rx = int(round(rx))
        ry = int(round(ry))
        
        if ny_f % ry != 0 or nx_f % rx != 0:
            raise ValueError(f"Fine grid size ({ny_f}, {nx_f}) not divisible by refinement ratios ({ry}, {rx})")
        
        ny_c = ny_f // ry
        nx_c = nx_f // rx
        var_coarse = np.zeros((ny_c, nx_c))
        
        for j in range(ny_c):
            for i in range(nx_c):
                block = var_fine[j*ry:(j+1)*ry, i*rx:(i+1)*rx]
                var_coarse[j, i] = np.mean(block)
        
        return var_coarse
    else:
        raise ValueError(f"Unsupported variable shape: {var_fine.shape}. Only 1D and 2D supported.")
