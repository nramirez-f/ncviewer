"""
Math Utilities for ncviewer
"""
import numpy as np

def evaluate_expression(ds, expression):
    """Evaluate a mathematical expression using dataset variables.
    
    Args:
        ds: xarray Dataset
        expression: String containing variable names and operations (e.g., 'h-H', 'temp*2+1', or just 'h')
        
    Returns:
        Computed xarray DataArray
        
    Raises:
        KeyError: If a variable in the expression doesn't exist
        SyntaxError: If the expression is invalid
    """
    import re
    
    # Strip whitespace
    expression = expression.strip()
    
    # Check if it's a simple variable name (no operators or functions)
    if expression in ds.data_vars or expression in ds.coords:
        return ds[expression]
    
    # Extract variable names from the expression (alphanumeric + underscore)
    var_pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
    potential_vars = re.findall(var_pattern, expression)
    
    # Create a safe namespace with dataset variables
    namespace = {}
    for var_name in potential_vars:
        if var_name in ds.data_vars or var_name in ds.coords:
            namespace[var_name] = ds[var_name]
    
    # Add common math functions and numpy
    import numpy as np
    namespace.update({
        'np': np,
        'abs': np.abs,
        'sqrt': np.sqrt,
        'sin': np.sin,
        'cos': np.cos,
        'tan': np.tan,
        'log': np.log,
        'log10': np.log10,
        'exp': np.exp,
        'pow': np.power,
    })
    
    try:
        result = eval(expression, {"__builtins__": {}}, namespace)
        return result
    except NameError as e:
        raise KeyError(f"Variable not found in expression '{expression}': {e}")
    except Exception as e:
        raise SyntaxError(f"Invalid expression '{expression}': {e}")

def compute_error(var_a, var_b, cell_volume, norm='2'):
    """
    Compute error between two variables using specified norm.
    
    Args:
        var_a: First variable (numpy array)
        var_b: Second variable (numpy array)
        cell_volume: Cell volume weights (numpy array)
        norm: Norm type ('1', '2', 'inf')
        
    Returns:
        Computed error (float)
    """
    diff = var_a - var_b
    if norm == '1':
        err = np.sum(np.abs(diff))*cell_volume
    elif norm == '2':
        err = np.sqrt(np.sum(diff**2)*cell_volume)
    elif norm == 'inf':
        err = np.max(np.abs(diff))
    else:
        raise ValueError(f"Unsupported norm type: {norm}")
    return err