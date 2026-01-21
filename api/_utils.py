"""Common utilities for ncviewer modules.

Shared functionality used by both _inspect.py and _plot.py.
Only imports lightweight dependencies (pathlib, xarray).
"""
from pathlib import Path
import xarray as xr


def open_dataset(path):
    """Open a NetCDF file and return xarray Dataset.
    
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


def validate_variable(ds, varname):
    """Check if variable exists in dataset.
    
    Args:
        ds: xarray.Dataset
        varname: Variable name to validate
        
    Raises:
        KeyError: If variable not found in dataset
    """
    if varname not in ds.data_vars:
        available = ", ".join(list(ds.data_vars)[:5])
        if len(ds.data_vars) > 5:
            available += f", ... ({len(ds.data_vars)} total)"
        raise KeyError(
            f"Variable '{varname}' not found. "
            f"Available variables: {available}"
        )
