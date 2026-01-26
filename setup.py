from setuptools import setup, find_packages

setup(
    name="ncviewer",
    version="0.1.0",
    description="CLI tool for quick NetCDF file exploration (inspired by pangeo/xarray)",
    author="nramirez-f",
    packages=find_packages(),
    install_requires=[
        "xarray",
        "netCDF4",
        "matplotlib",
        "hvplot",
        "bokeh",
        "holoviews",
        "panel",
    ],
    entry_points={
        "console_scripts": [
            "ncviewer = src.cli:main",
            "ncinfo = src.cli:ncinfo",
            "ncdim = src.cli:ncdim",
            "ncvar = src.cli:ncvar",
            "ncsum = src.cli:ncsum",
            "ncerr = src.cli:ncerr",
            "ncp1d = src.cli:ncp1d",
            "ncplot1d = src.cli:ncplot1d",
        ],
    },
    include_package_data=True,
    python_requires=">=3.8",
)
