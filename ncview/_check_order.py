"""Code order checking utilities for NcView.

This module handles code order verification from NetCDF input files.
"""
import sys
from pathlib import Path
import netCDF4 as nc
import numpy as np
import math

def compute_err(u_refp, u, x, norm):
    """Calcula el error entre la solución numérica u y la referencia
    """

    dx = x[1] - x[0]
    diff = u_refp - u
    nu = norm.upper()
    if nu == 'L1':
        return np.sum(np.abs(diff)) * dx
    elif nu == 'L2':
        return math.sqrt(np.sum(diff**2) * dx)
    elif nu in ('LINF', 'L_INF', 'INF'):
        return float(np.max(np.abs(diff)))
    else:
        raise ValueError(f"Norma desconocida: {norm}")

def check_order(input_files):
    """Check code order from NetCDF input files.
    
    Args:
        input_files: List of paths to NetCDF input files (relative to execution directory)
    """
    # Convert to Path objects and verify they exist
    file_paths = []
    for f in input_files:
        p = Path(f)
        if not p.exists():
            print(f"✗ Warning: File not found: {f}", file=sys.stderr)
        else:
            file_paths.append(p)
    
    if not file_paths:
        print("✗ Error: No valid input files found", file=sys.stderr)
        return
    
    print("=== Scheme Order ===")
    print(f"Checking scheme order from {len(file_paths)} input file(s):")
    for p in file_paths:
        print(f"  - {p}")

    vars_ = ['h', 'q']

    # Norma: 'L1', 'L2' o 'Linf'
    NORM = 'L1'

    # Nombres en NetCDF
    XNAME = 'x'
    TNAME = 'time'

    # referencia geométrica (x_ref) y tamaño fino
    with nc.Dataset(file_paths[-1]) as ds_ref0:
        x_ref = np.asarray(ds_ref0.variables[XNAME][:], float).squeeze()
    n_f = len(x_ref)

    # Para cada variable, cargar referencia fina al último tiempo
    uref_by_var = {}
    for varname in vars_:
        with nc.Dataset(file_paths[-1]) as ds_ref:
            vref = ds_ref.variables[varname]
            if vref.dimensions[0] == TNAME:   # (time, x)
                u_ref_full = vref[-1, :]
            else:                              # (x, time)
                u_ref_full = vref[:, -1]
        uref_by_var[varname] = np.asarray(u_ref_full, float).squeeze()

    # Recorremos una vez las mallas gruesas y acumulamos errores por variable
    coarse_files = file_paths[:-1]
    npx_list = []
    errs = {v: [] for v in vars_}

    for f in coarse_files:
        with nc.Dataset(f) as ds:
            x = np.asarray(ds.variables[XNAME][:], float).squeeze()
        n_c = len(x)
        assert n_f % n_c == 0, f"nf={n_f} no es múltiplo de nc={n_c}"
        r = n_f // n_c
        if not npx_list:
            npx_list = []
        npx_list.append(n_c)

        for varname in vars_:
            with nc.Dataset(f) as ds:
                v = ds.variables[varname]
                if v.dimensions[0] == TNAME:
                    u = v[-1, :]
                else:
                    u = v[:, -1]
            u = np.asarray(u, float).squeeze()

            u_refp = uref_by_var[varname].reshape(-1, r).mean(axis=1)
            err = compute_err(u_refp, u, x, NORM)
            errs[varname].append(err)

    # Calcular p par-a-par por variable (p en fila i compara fila i-1 con i)
    ps = {v: ["" for _ in range(len(npx_list))] for v in vars_}
    for v in vars_:
        for i in range(1, len(npx_list)):
            h_ratio = (1.0 / npx_list[i-1]) / (1.0 / npx_list[i])  # = npx[i]/npx[i-1]
            p_val = math.log(errs[v][i-1] / errs[v][i]) / math.log(h_ratio)
            ps[v][i] = f"{p_val:.3f}"

    # Imprimir tabla conjunta
    header = f"{'ncx':>8}"
    for v in vars_:
        header += f" | {'Error(' + v + ')':>13} | {'Order(' + v + ')':>8}"
    
    print(f"\nError table using {NORM} norm: \n")
    print(header)
    print("-" * len(header))
    
    # Print data rows
    for i, npx in enumerate(npx_list):
        row = f"{npx:8d}"
        for v in vars_:
            row += f" | {errs[v][i]:13.6e} | {ps[v][i]:>8}"
        print(row)
