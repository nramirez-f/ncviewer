"""Common utilities for ncviewer modules.

Shared functionality used by both _inspect.py and _plot.py.
Only imports lightweight dependencies (pathlib, xarray).
"""
from pathlib import Path
import xarray as xr


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

def count_spatial_dimensions(path):
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

def count_temporal_dimensions(path):
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
