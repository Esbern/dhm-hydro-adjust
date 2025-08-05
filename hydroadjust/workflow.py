"""
Notebook-friendly workflow functions for DHM hydro adjustments.
This module provides high-level functions that can be easily used in Jupyter notebooks.
"""

import os
from pathlib import Path
from typing import Union, Optional, List, Tuple
import logging

import numpy as np
import geopandas as gpd
from shapely.geometry import box
from osgeo import gdal, ogr
from tqdm import tqdm

from .sampling import BoundingBox, get_raster_window, get_raster_interpolator
from .burning import burn_lines

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

gdal.UseExceptions()
ogr.UseExceptions()


class HydroAdjustWorkflow:
    """
    A class to manage the complete hydro adjustment workflow.
    """
    
    def __init__(self, 
                 dtm_raster: Union[str, Path],
                 horseshoe_file: Union[str, Path],
                 line_file: Union[str, Path],
                 output_dir: Union[str, Path]):
        """
        Initialize the workflow with input files and output directory.
        
        Parameters:
        -----------
        dtm_raster : str or Path
            Path to the input DTM raster file
        horseshoe_file : str or Path
            Path to the horseshoe vector data file
        line_file : str or Path
            Path to the line vector data file
        output_dir : str or Path
            Directory where output files will be created
        """
        self.dtm_raster = Path(dtm_raster)
        self.horseshoe_file = Path(horseshoe_file)
        self.line_file = Path(line_file)
        self.output_dir = Path(output_dir)
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Define output file paths
        self.hs_filtered = self.output_dir / 'horseshoe_filtered.gpkg'
        self.lines_filtered = self.output_dir / 'lines_filtered.gpkg'
        self.hs_with_z = self.output_dir / 'horseshoe_with_z.gpkg'
        self.lines_with_z = self.output_dir / 'lines_with_z.gpkg'
        self.combined_lines = self.output_dir / 'combined_lines.gpkg'
        self.hydro_dtm = self.output_dir / 'hydro_adjusted_dtm.tif'
        
        logger.info(f"Workflow initialized with output directory: {self.output_dir}")
    
    def get_raster_bounds(self) -> Tuple[float, float, float, float]:
        """
        Get the bounding box of the DTM raster.
        
        Returns:
        --------
        tuple
            (min_x, min_y, max_x, max_y) bounding box coordinates
        """
        dataset = gdal.Open(str(self.dtm_raster))
        geotransform = dataset.GetGeoTransform()
        
        if geotransform[2] != 0.0 or geotransform[4] != 0.0:
            raise ValueError("Geotransforms with rotation are unsupported")
        
        cols = dataset.RasterXSize
        rows = dataset.RasterYSize
        
        upx = geotransform[0]
        upy = geotransform[3]
        xres = geotransform[1]
        yres = geotransform[5]
        
        # Calculate corners
        ulx = upx
        uly = upy
        lrx = upx + cols * xres
        lry = upy + rows * yres
        
        min_x = min(ulx, lrx)
        max_x = max(ulx, lrx)
        min_y = min(uly, lry)
        max_y = max(uly, lry)
        
        logger.info(f"Raster bounds: ({min_x}, {min_y}, {max_x}, {max_y})")
        return min_x, min_y, max_x, max_y
    
    def filter_vectors_by_bounds(self, 
                                horseshoe_layer: str = 'dhmhestesko',
                                line_layer: str = 'dhmlinje') -> None:
        """
        Filter vector data to only include features within the raster bounds.
        
        Parameters:
        -----------
        horseshoe_layer : str
            Layer name for horseshoe data
        line_layer : str
            Layer name for line data
        """
        min_x, min_y, max_x, max_y = self.get_raster_bounds()
        bbox_geom = box(min_x, min_y, max_x, max_y)
        
        # Filter horseshoe data
        logger.info("Filtering horseshoe data...")
        try:
            gdf_hs = gpd.read_file(self.horseshoe_file, layer=horseshoe_layer, bbox=bbox_geom)
            if not gdf_hs.empty:
                gdf_hs.to_file(self.hs_filtered, driver='GPKG')
                logger.info(f"Found {len(gdf_hs)} horseshoe features within bounds")
            else:
                logger.warning("No horseshoe features found within raster bounds")
        except Exception as e:
            logger.error(f"Error filtering horseshoe data: {e}")
        
        # Filter line data
        logger.info("Filtering line data...")
        try:
            gdf_lines = gpd.read_file(self.line_file, layer=line_layer, bbox=bbox_geom)
            if not gdf_lines.empty:
                gdf_lines.to_file(self.lines_filtered, driver='GPKG')
                logger.info(f"Found {len(gdf_lines)} line features within bounds")
            else:
                logger.warning("No line features found within raster bounds")
        except Exception as e:
            logger.error(f"Error filtering line data: {e}")
    
    def sample_line_z(self, input_lines: Union[str, Path], output_lines: Union[str, Path]) -> None:
        """
        Sample elevation from DTM for line endpoints and create 3D lines.
        
        Parameters:
        -----------
        input_lines : str or Path
            Path to input 2D line vector file
        output_lines : str or Path
            Path to output 3D line vector file
        """
        logger.info(f"Sampling elevation for lines: {input_lines}")
        
        input_raster_dataset = gdal.Open(str(self.dtm_raster))
        input_lines_datasrc = ogr.Open(str(input_lines))
        input_lines_layer = input_lines_datasrc.GetLayer()
        
        # Create output file
        output_lines_driver = ogr.GetDriverByName("GPKG")
        if os.path.exists(output_lines):
            output_lines_driver.DeleteDataSource(str(output_lines))
        
        output_lines_datasrc = output_lines_driver.CreateDataSource(str(output_lines))
        output_lines_datasrc.CreateLayer(
            "lines_with_z",
            srs=input_lines_layer.GetSpatialRef(),
            geom_type=ogr.wkbLineString25D,
        )
        output_lines_layer = output_lines_datasrc.GetLayer()
        
        valid_count = 0
        invalid_count = 0
        
        for input_line_feature in tqdm(input_lines_layer, desc="Processing lines"):
            input_line_geometry = input_line_feature.GetGeometryRef()
            
            if input_line_geometry.GetPointCount() == 2:
                # Get X,Y coordinates
                input_line_xy = np.array(input_line_geometry.GetPoints())[:,:2]
                
                input_line_bbox = BoundingBox(
                    x_min=np.min(input_line_xy[:,0]),
                    x_max=np.max(input_line_xy[:,0]),
                    y_min=np.min(input_line_xy[:,1]),
                    y_max=np.max(input_line_xy[:,1]),
                )
                
                # Get raster window for this line
                window_raster_dataset = get_raster_window(input_raster_dataset, input_line_bbox)
                window_raster_interpolator = get_raster_interpolator(window_raster_dataset)
                
                # Sample elevation at endpoints
                input_line_z = window_raster_interpolator((input_line_xy[:,0], input_line_xy[:,1]))
                
                # Create output feature if sampling is valid
                if np.all(np.isfinite(input_line_z)):
                    output_line_feature = ogr.Feature(output_lines_layer.GetLayerDefn())
                    output_line_geometry = ogr.Geometry(ogr.wkbLineString25D)
                    output_line_geometry.AddPoint(input_line_xy[0,0], input_line_xy[0,1], input_line_z[0])
                    output_line_geometry.AddPoint(input_line_xy[1,0], input_line_xy[1,1], input_line_z[1])
                    output_line_feature.SetGeometry(output_line_geometry)
                    output_lines_layer.CreateFeature(output_line_feature)
                    valid_count += 1
                else:
                    invalid_count += 1
        
        logger.info(f"Line sampling complete: {valid_count} valid, {invalid_count} invalid")
    
    def sample_horseshoe_z_lines(self, 
                                 input_horseshoes: Union[str, Path], 
                                 output_lines: Union[str, Path],
                                 max_sample_dist: Optional[float] = None) -> None:
        """
        Sample horseshoe profiles and render as 3D lines.
        
        Parameters:
        -----------
        input_horseshoes : str or Path
            Path to input horseshoe vector file
        output_lines : str or Path
            Path to output 3D line vector file
        max_sample_dist : float, optional
            Maximum sampling distance along profiles
        """
        logger.info(f"Sampling elevation for horseshoes: {input_horseshoes}")
        
        input_raster_dataset = gdal.Open(str(self.dtm_raster))
        input_raster_geotransform = input_raster_dataset.GetGeoTransform()
        
        if max_sample_dist is None:
            # Set to half the diagonal pixel size
            max_sample_dist = 0.5 * np.hypot(
                input_raster_geotransform[1],
                input_raster_geotransform[5],
            )
        
        input_horseshoes_datasrc = ogr.Open(str(input_horseshoes))
        input_horseshoes_layer = input_horseshoes_datasrc.GetLayer()
        
        # Create output file
        output_lines_driver = ogr.GetDriverByName("GPKG")
        if os.path.exists(output_lines):
            output_lines_driver.DeleteDataSource(str(output_lines))
        
        output_lines_datasrc = output_lines_driver.CreateDataSource(str(output_lines))
        output_lines_datasrc.CreateLayer(
            "horseshoe_lines_with_z",
            srs=input_horseshoes_layer.GetSpatialRef(),
            geom_type=ogr.wkbLineString25D,
        )
        output_lines_layer = output_lines_datasrc.GetLayer()
        
        valid_count = 0
        invalid_count = 0
        
        for horseshoe_feature in tqdm(input_horseshoes_layer, desc="Processing horseshoes"):
            horseshoe_geometry = horseshoe_feature.GetGeometryRef()
            
            if horseshoe_geometry.GetPointCount() == 4:
                # Get X,Y coordinates (ABCD pattern)
                horseshoe_xy = np.array(horseshoe_geometry.GetPoints())[:,:2]
                
                horseshoe_bbox = BoundingBox(
                    x_min=np.min(horseshoe_xy[:,0]),
                    x_max=np.max(horseshoe_xy[:,0]),
                    y_min=np.min(horseshoe_xy[:,1]),
                    y_max=np.max(horseshoe_xy[:,1]),
                )
                
                # Get raster window
                window_raster_dataset = get_raster_window(input_raster_dataset, horseshoe_bbox)
                window_raster_interpolator = get_raster_interpolator(window_raster_dataset)
                
                # Calculate profile lengths
                open_profile_length = np.hypot(
                    horseshoe_xy[3, 0] - horseshoe_xy[0, 0],
                    horseshoe_xy[3, 1] - horseshoe_xy[0, 1],
                )
                closed_profile_length = np.hypot(
                    horseshoe_xy[2, 0] - horseshoe_xy[1, 0],
                    horseshoe_xy[2, 1] - horseshoe_xy[1, 1],
                )
                
                # Determine sampling density
                longest_profile_length = max(open_profile_length, closed_profile_length)
                num_profile_samples = max(2, int(np.ceil(longest_profile_length / max_sample_dist)) + 1)
                
                # Sample along profiles
                profile_abscissa = np.linspace(0.0, 1.0, num_profile_samples, endpoint=True)
                
                # Open profile A->D, Closed profile B->C
                open_profile_xy = horseshoe_xy[0,:] + profile_abscissa[:,np.newaxis]*(horseshoe_xy[3,:] - horseshoe_xy[0,:])
                closed_profile_xy = horseshoe_xy[1,:] + profile_abscissa[:,np.newaxis]*(horseshoe_xy[2,:] - horseshoe_xy[1,:])
                
                # Sample elevations
                open_profile_z = window_raster_interpolator((open_profile_xy[:,0], open_profile_xy[:,1]))
                closed_profile_z = window_raster_interpolator((closed_profile_xy[:,0], closed_profile_xy[:,1]))
                
                # Create connecting lines if sampling is valid
                if np.all(np.isfinite(open_profile_z)) and np.all(np.isfinite(closed_profile_z)):
                    for i in range(num_profile_samples):
                        output_line_feature = ogr.Feature(output_lines_layer.GetLayerDefn())
                        output_line_geometry = ogr.Geometry(ogr.wkbLineString25D)
                        output_line_geometry.AddPoint(
                            open_profile_xy[i,0], open_profile_xy[i,1], open_profile_z[i]
                        )
                        output_line_geometry.AddPoint(
                            closed_profile_xy[i,0], closed_profile_xy[i,1], closed_profile_z[i]
                        )
                        output_line_feature.SetGeometry(output_line_geometry)
                        output_lines_layer.CreateFeature(output_line_feature)
                    valid_count += 1
                else:
                    invalid_count += 1
        
        logger.info(f"Horseshoe sampling complete: {valid_count} valid, {invalid_count} invalid")
    
    def merge_line_files(self, input_files: List[Union[str, Path]], output_file: Union[str, Path]) -> None:
        """
        Merge multiple line files into a single GeoPackage.
        
        Parameters:
        -----------
        input_files : list
            List of input file paths to merge
        output_file : str or Path
            Output merged file path
        """
        logger.info(f"Merging {len(input_files)} files into {output_file}")
        
        # Create output file
        output_driver = ogr.GetDriverByName("GPKG")
        if os.path.exists(output_file):
            output_driver.DeleteDataSource(str(output_file))
        
        output_datasrc = output_driver.CreateDataSource(str(output_file))
        
        for i, input_file in enumerate(input_files):
            if os.path.exists(input_file):
                input_datasrc = ogr.Open(str(input_file))
                for layer_idx in range(input_datasrc.GetLayerCount()):
                    input_layer = input_datasrc.GetLayerByIndex(layer_idx)
                    layer_name = f"layer_{i}_{input_layer.GetName()}"
                    output_layer = output_datasrc.CopyLayer(input_layer, layer_name)
                    if output_layer is None:
                        logger.warning(f"Failed to copy layer {input_layer.GetName()}")
        
        logger.info("File merging complete")
    
    def burn_lines_to_raster(self, lines_file: Union[str, Path], output_raster: Union[str, Path]) -> None:
        """
        Burn 3D lines into the DTM raster.
        
        Parameters:
        -----------
        lines_file : str or Path
            Path to 3D lines file
        output_raster : str or Path
            Path to output adjusted DTM
        """
        logger.info(f"Burning lines into DTM: {lines_file} -> {output_raster}")
        
        input_raster_dataset = gdal.Open(str(self.dtm_raster))
        lines_datasrc = ogr.Open(str(lines_file))
        
        # Create intermediate in-memory dataset
        intermediate_driver = gdal.GetDriverByName("MEM")
        intermediate_raster_dataset = intermediate_driver.CreateCopy("temp", input_raster_dataset)
        
        # Burn all layers
        for layer in lines_datasrc:
            burn_lines(intermediate_raster_dataset, layer)
            logger.info(f"Burned layer {layer.GetName()}")
        
        # Save to output file
        output_driver = gdal.GetDriverByName("GTiff")
        output_dataset = output_driver.CreateCopy(str(output_raster), intermediate_raster_dataset)
        
        logger.info("Line burning complete")
    
    def run_complete_workflow(self, 
                             horseshoe_layer: str = 'dhmhestesko',
                             line_layer: str = 'dhmlinje',
                             max_sample_dist: Optional[float] = None) -> Path:
        """
        Run the complete hydro adjustment workflow.
        
        Parameters:
        -----------
        horseshoe_layer : str
            Layer name for horseshoe data
        line_layer : str
            Layer name for line data
        max_sample_dist : float, optional
            Maximum sampling distance for horseshoe profiles
            
        Returns:
        --------
        Path
            Path to the final hydro-adjusted DTM
        """
        logger.info("Starting complete hydro adjustment workflow")
        
        try:
            # Step 1: Filter vectors by raster bounds
            self.filter_vectors_by_bounds(horseshoe_layer, line_layer)
            
            # Step 2: Sample elevations for lines (if filtered file exists)
            if os.path.exists(self.lines_filtered):
                self.sample_line_z(self.lines_filtered, self.lines_with_z)
            
            # Step 3: Sample elevations for horseshoes (if filtered file exists)
            if os.path.exists(self.hs_filtered):
                self.sample_horseshoe_z_lines(self.hs_filtered, self.hs_with_z, max_sample_dist)
            
            # Step 4: Merge line files
            input_files = []
            if os.path.exists(self.lines_with_z):
                input_files.append(self.lines_with_z)
            if os.path.exists(self.hs_with_z):
                input_files.append(self.hs_with_z)
            
            if input_files:
                self.merge_line_files(input_files, self.combined_lines)
                
                # Step 5: Burn lines into DTM
                self.burn_lines_to_raster(self.combined_lines, self.hydro_dtm)
                
                logger.info(f"Workflow complete! Output: {self.hydro_dtm}")
                return self.hydro_dtm
            else:
                logger.warning("No valid input data found within raster bounds")
                return None
                
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            raise


# Convenience functions for direct notebook use
def create_hydro_adjusted_dtm(dtm_raster: Union[str, Path],
                             horseshoe_file: Union[str, Path],
                             line_file: Union[str, Path],
                             output_dir: Union[str, Path],
                             horseshoe_layer: str = 'dhmhestesko',
                             line_layer: str = 'dhmlinje',
                             max_sample_dist: Optional[float] = None) -> Path:
    """
    Convenience function to run the complete workflow in one call.
    
    Parameters:
    -----------
    dtm_raster : str or Path
        Path to input DTM raster
    horseshoe_file : str or Path
        Path to horseshoe vector data
    line_file : str or Path
        Path to line vector data
    output_dir : str or Path
        Output directory for results
    horseshoe_layer : str
        Layer name for horseshoe data
    line_layer : str
        Layer name for line data
    max_sample_dist : float, optional
        Maximum sampling distance for horseshoe profiles
        
    Returns:
    --------
    Path
        Path to hydro-adjusted DTM
    """
    workflow = HydroAdjustWorkflow(dtm_raster, horseshoe_file, line_file, output_dir)
    return workflow.run_complete_workflow(horseshoe_layer, line_layer, max_sample_dist)
