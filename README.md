# NetCDF Viewer

CLI for quick NetCDF file exploration, inspired by the pangeo ecosystem (xarray, hvplot).

## Main Commands

The CLI is invoked with `ncv` (git-style subcommands):

**Data Inspection (fast - only loads xarray):**
- `ncv info <file>`: display complete NetCDF dataset information
- `ncv dimensions <file>`: display dimensions and their sizes
- `ncv variables <file>`: list variables with descriptions and metadata
- `ncv summary <file> [variable|expression]`: show statistical summary (min/max/mean/std)
  - Examples: 
    - `ncv summary file.nc h` - summary of variable 'h'
    - `ncv summary file.nc "h-H"` - summary of the difference between h and H
    - `ncv summary file.nc "temp*2"` - summary of temperature multiplied by 2
    - `ncv summary file.nc "sqrt(u**2 + v**2)"` - summary of velocity magnitude
---

## Installation & Workflow

### 📦 Dependencies

This project uses the pangeo stack:
- `xarray`: NetCDF data reading and manipulation
- `netCDF4`: NetCDF file backend
- `hvplot`: interactive plotting
- `bokeh`: visualization backend

### 🔧 For DEVELOPMENT

If you're going to modify the CLI code, use a virtual environment:

```bash
# 1. Navigate to the project
cd /path/to/ncview

# 2. Create virtual environment
python3 -m venv .venv

# 3. Activate the environment
source .venv/bin/activate

# 4. Upgrade pip
pip install --upgrade pip

# 5. Install in editable mode (code changes reflect immediately)
pip install -e .

# 6. Now you can use ncv (inside the venv)
ncv --help
ncv info myfile.nc

# 7. To exit the environment
deactivate
```

**When to use development mode:**
- ✅ You're modifying code, adding features, debugging
- ✅ You can install dev tools (pytest, black, flake8, ipython)
- ✅ Completely isolated from system Python

**Every time you open a new terminal:**
```bash
cd /path/to/ncview
source .venv/bin/activate
# now ncv is available
```

**⚠️ Important for editable mode:** If changes don't reflect immediately:
```bash
# Option 1: Restart the Python process
# Just run ncv again in a fresh terminal or after deactivate/activate

# Option 2: Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# Option 3: Reinstall (rarely needed)
pip install -e . --force-reinstall --no-deps
```

### 🚀 For USAGE (end-user)

If you just want to use the tool without modifying code:

#### Option A: pipx (global isolated installation) - RECOMMENDED

**⚠️ Common issue on Debian/Ubuntu:** If you get `externally-managed-environment` error:

```bash
# Install pipx using system package manager
sudo apt update
sudo apt install pipx

# Configure PATH (first time only)
pipx ensurepath

# Close and reopen terminal, then install NcView
cd /path/to/ncview
pipx install .

# Now ncv is globally available
ncv --help
```

**Benefits of pipx:**
- ✅ `ncv` available from any directory
- ✅ Doesn't pollute global Python
- ✅ No need to activate/deactivate environments
- ✅ Pipx creates and manages virtual environment automatically

#### Option B: User virtual environment (without pipx)

If you can't install pipx and want global access:

```bash
# 1. Create virtual environment in your home
python3 -m venv ~/.venvs/ncview

# 2. Install NcView in that environment
~/.venvs/ncview/bin/pip install /path/to/ncview

# 3. Create permanent alias in ~/.bashrc to invoke ncv globally
echo 'alias ncv="~/.venvs/ncview/bin/ncv"' >> ~/.bashrc
source ~/.bashrc

# Now ncv works from any directory
ncv --help
```

---

## 📖 Quick Usage

```bash
# View dataset information
ncv info data/ocean_temperature.nc

# List variables with descriptions
ncv variables data/ocean_temperature.nc

# Show statistics for all variables
ncv summary data/ocean_temperature.nc

# Show statistics for specific variable
ncv summary data/ocean_temperature.nc temperature
```

---
## 🤝 Contributing

Open issues and PRs in the repository. For development, use the virtual environment workflow.
