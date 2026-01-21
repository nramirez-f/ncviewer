"""Math Utilities for ncviewer

"""

def evaluate_expression(ds, expression):
    """Evaluate a mathematical expression using dataset variables.
    
    Args:
        ds: xarray Dataset
        expression: String containing variable names and operations (e.g., 'h-H', 'temp*2+1')
        
    Returns:
        Computed xarray DataArray
        
    Raises:
        KeyError: If a variable in the expression doesn't exist
        SyntaxError: If the expression is invalid
    """
    import re
    
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
