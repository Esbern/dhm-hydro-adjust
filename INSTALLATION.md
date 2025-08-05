# DHM Hydro Adjust - Installation and Usage Guide

## Quick Setup

### 1. Install the Package
From the project root directory, run:
```bash
pip install -e .
```

This will install the package in development mode with all dependencies.

### 2. Alternative: Install Dependencies Only
If you prefer not to install the package, install the required dependencies:
```bash
pip install gdal numpy scipy tqdm geopandas shapely
```

### 3. Open the Workflow Notebook
Open `hydro_workflow_notebook.ipynb` in Jupyter Lab or VS Code and follow the step-by-step workflow.

## Package Structure

```
dhm-hydro-adjust/
├── hydroadjust/
│   ├── __init__.py          # Package exports
│   ├── workflow.py          # Main workflow class and functions
│   ├── burning.py           # Raster burning functionality
│   ├── sampling.py          # Elevation sampling functionality
│   └── cli/                 # Original CLI scripts (still available)
│       ├── burn_line_z.py
│       ├── sample_line_z.py
│       └── sample_horseshoe_z_lines.py
├── hydro_workflow_notebook.ipynb  # Main workflow notebook
├── create hydro_dtm.ipynb   # Original notebook (for reference)
├── setup.py                 # Package configuration
├── environment.yml          # Conda environment
└── README.md               # Documentation
```

## Key Features

### 1. Simple One-Line Workflow
```python
from hydroadjust import create_hydro_adjusted_dtm

result = create_hydro_adjusted_dtm(
    dtm_raster="path/to/dtm.tif",
    horseshoe_file="path/to/horseshoes.gpkg", 
    line_file="path/to/lines.gpkg",
    output_dir="path/to/output"
)
```

### 2. Step-by-Step Control
```python
from hydroadjust import HydroAdjustWorkflow

workflow = HydroAdjustWorkflow(dtm_raster, horseshoe_file, line_file, output_dir)
workflow.filter_vectors_by_bounds()
workflow.sample_line_z(...)
workflow.sample_horseshoe_z_lines(...)
workflow.merge_line_files(...)
workflow.burn_lines_to_raster(...)
```

### 3. Progress Tracking
- Built-in logging shows progress for each step
- Progress bars for processing large datasets
- Clear error messages and warnings

### 4. Flexible Input/Output
- Supports various raster and vector formats via GDAL/OGR
- Automatic output directory creation
- Configurable sampling parameters

## Usage Examples

### Basic Usage
```python
import logging
from pathlib import Path
from hydroadjust import create_hydro_adjusted_dtm

# Enable progress logging
logging.basicConfig(level=logging.INFO)

# Define paths
dtm_raster = Path("data/dtm.tif")
horseshoe_file = Path("data/horseshoes.gpkg") 
line_file = Path("data/lines.gpkg")
output_dir = Path("output")

# Run workflow
result = create_hydro_adjusted_dtm(
    dtm_raster=dtm_raster,
    horseshoe_file=horseshoe_file,
    line_file=line_file,
    output_dir=output_dir,
    horseshoe_layer='dhmhestesko',
    line_layer='dhmlinje'
)

print(f"Hydro-adjusted DTM created: {result}")
```

### Advanced Usage with Custom Sampling
```python
from hydroadjust import HydroAdjustWorkflow

workflow = HydroAdjustWorkflow(dtm_raster, horseshoe_file, line_file, output_dir)

# Custom sampling distance (0.1 meter resolution)
workflow.sample_horseshoe_z_lines(
    input_horseshoes=workflow.hs_filtered,
    output_lines=workflow.hs_with_z,
    max_sample_dist=0.1  # 0.1 meter sampling
)
```

## CLI Commands (Still Available)

The original command-line interface is still available:

```bash
# Sample line elevations
sample_line_z input_raster.tif input_lines.gpkg output_lines.gpkg

# Sample horseshoe elevations  
sample_horseshoe_z_lines input_raster.tif input_horseshoes.gpkg output_lines.gpkg

# Burn lines into raster
burn_line_z lines.gpkg input_raster.tif output_raster.tif
```

## Troubleshooting

### GDAL Installation Issues
If you encounter GDAL installation problems:
1. Use conda: `conda install -c conda-forge gdal`
2. On Windows, consider using OSGeo4W or conda
3. Ensure GDAL Python bindings match your GDAL installation

### Memory Issues with Large Rasters
- The workflow processes data in chunks automatically
- For very large datasets, consider tiling your input raster
- Monitor memory usage during processing

### No Features Found
If the workflow reports no features within bounds:
1. Check that your vector data overlaps with the raster extent
2. Verify the coordinate reference systems match
3. Use a GIS to visualize the data extent

## Migration from Original Workflow

If you're upgrading from the original workflow:

1. **Replace subprocess calls** with direct function calls
2. **Update import statements** to use the new `hydroadjust` package
3. **Use the new notebook** as a template for your workflow
4. **Keep your existing file paths** - the new workflow is compatible

### Before (Original):
```python
import subprocess
subprocess.run(['python', 'cli/sample_line_z.py', raster, lines, output])
```

### After (Refactored):
```python
from hydroadjust import HydroAdjustWorkflow
workflow = HydroAdjustWorkflow(raster, horseshoes, lines, output_dir)
workflow.sample_line_z(lines, output)
```
