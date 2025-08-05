"""
DHM Hydro Adjust - Tools to make hydrological adjustments to DEM rasters.

This package provides tools to burn hydrological adjustment objects into DEM rasters,
ensuring that water can flow uninterrupted through culverts, under bridges, etc.
"""

from .workflow import HydroAdjustWorkflow, create_hydro_adjusted_dtm
from .burning import burn_lines
from .sampling import BoundingBox, get_raster_window, get_raster_interpolator

__version__ = "1.0.0"
__author__ = "Danish Agency for Data Supply and Efficiency (SDFE)"

__all__ = [
    "HydroAdjustWorkflow",
    "create_hydro_adjusted_dtm", 
    "burn_lines",
    "BoundingBox",
    "get_raster_window",
    "get_raster_interpolator"
]