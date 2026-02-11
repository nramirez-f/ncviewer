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
            "ncorder = src.cli:ncorder",
            "ncsnap1d = src.cli:ncsnap1d",
            "ncmov2d = src.cli:ncmov2d",
            "ncplot2d = src.cli:ncplot2d",
            "ncplot1d = src.cli:ncplot1d",
        ],
    },
    include_package_data=True,
    python_requires=">=3.8",
)
