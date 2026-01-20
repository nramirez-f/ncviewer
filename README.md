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

**Plotting (loads matplotlib/hvplot):**
- `ncv plot1d <file> <var1> [var2 ...] -t <time> [options]`: generate 1D plot at specific time
  - Required: `-t/--time`: time index (integer) or datetime string
  - Optional: `-o/--output`: save to file (PNG, PDF, etc.)
  - Optional: `--hvplot`: use hvplot instead of matplotlib
  - Examples:
    - `ncv plot1d file.nc h -t 0` - plot variable 'h' at time index 0
    - `ncv plot1d file.nc h H -t "2020-01-01"` - plot h and H at specific date
    - `ncv plot1d file.nc "h-H" -t 10 -o output.png` - plot difference, save to PNG
    - `ncv plot1d file.nc "sqrt(u**2+v**2)" -t 0 --hvplot` - plot with hvplot
---

## Installation & Workflow

### 📦 Dependencies

This project uses the pangeo stack and visualization libraries:
- `xarray`: NetCDF data reading and manipulation
- `netCDF4`: NetCDF file backend
- `matplotlib`: Static plotting (1D plots)
- `hvplot`: Interactive plotting
- `bokeh` & `holoviews`: Visualization backends

**All dependencies are installed automatically** when you install ncviewer with `pip install -e .` or `pipx install .`

### 🔧 For DEVELOPMENT

If you're going to modify the CLI code, use a virtual environment:

```bash
# 1. Clone the repository
git clone git@github.com:nramirez-f/ncviewer.git

# 2. Navigate to the project
cd /path/to/ncviewer

# 3. Create virtual environment
python3 -m venv .venv

# 4. Activate the environment
source .venv/bin/activate

# 5. Install in editable mode
pip install -e .

# 6. Now you can use ncv (inside the venv)
ncv --help
ncv info myfile.nc

# 7. To exit the environment
deactivate

# 8. (Optional) Add path in bashrc to invoke in any folder
export PATH="/path/to/ncviewer/.venv/bin:$PATH"
```
### 🚀 For USAGE (end-user)

If you just want to use the tool without modifying code:

#### Option A: pipx (global isolated installation) - RECOMMENDED

```bash
# Install pipx using system package manager
sudo apt update
sudo apt install pipx

# Configure PATH (first time only)
pipx ensurepath

# Close and reopen terminal, then install ncviewer
cd /path/to/ncviewer
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

If you can't install pipx and want global access, use development installation without editable mode.
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
