#!/usr/bin/env python3
"""
Quick test script to verify the DHM Hydro Adjust package installation.
"""

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing package imports...")
    
    try:
        from hydroadjust import HydroAdjustWorkflow, create_hydro_adjusted_dtm
        print("✅ Main workflow functions imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import main functions: {e}")
        return False
    
    try:
        from hydroadjust import burn_lines, get_raster_window, BoundingBox
        print("✅ Core functions imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import core functions: {e}")
        return False
    
    try:
        from osgeo import gdal, ogr
        print("✅ GDAL/OGR imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import GDAL/OGR: {e}")
        print("   Try: conda install -c conda-forge gdal")
        return False
    
    try:
        import numpy as np
        import scipy
        import tqdm
        import geopandas as gpd
        import shapely
        print("✅ Scientific libraries imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import scientific libraries: {e}")
        return False
    
    return True


def test_workflow_init():
    """Test that the workflow class can be instantiated."""
    print("\nTesting workflow initialization...")
    
    try:
        from hydroadjust import HydroAdjustWorkflow
        from pathlib import Path
        
        # Create dummy paths (files don't need to exist for this test)
        workflow = HydroAdjustWorkflow(
            dtm_raster="dummy.tif",
            horseshoe_file="dummy_hs.gpkg",
            line_file="dummy_lines.gpkg", 
            output_dir="dummy_output"
        )
        
        print("✅ Workflow class instantiated successfully")
        print(f"   Output directory: {workflow.output_dir}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to instantiate workflow: {e}")
        return False


def test_cli_availability():
    """Test if CLI commands are available."""
    print("\nTesting CLI command availability...")
    
    import subprocess
    
    commands = ['sample_line_z', 'sample_horseshoe_z_lines', 'burn_line_z']
    
    for cmd in commands:
        try:
            result = subprocess.run([cmd, '--help'], 
                                   capture_output=True, 
                                   text=True, 
                                   timeout=5)
            if result.returncode == 0:
                print(f"✅ {cmd} command available")
            else:
                print(f"⚠️ {cmd} command found but returned error")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print(f"❌ {cmd} command not found")
            print("   Install package with: pip install -e .")


def main():
    """Run all tests."""
    print("DHM Hydro Adjust - Installation Test")
    print("=" * 40)
    
    # Test imports
    imports_ok = test_imports()
    
    if imports_ok:
        # Test workflow initialization
        workflow_ok = test_workflow_init()
        
        # Test CLI availability
        test_cli_availability()
        
        print("\n" + "=" * 40)
        if imports_ok and workflow_ok:
            print("🎉 Installation test PASSED!")
            print("\nNext steps:")
            print("1. Open 'hydro_workflow_notebook.ipynb' in Jupyter")
            print("2. Configure your data paths in the notebook")
            print("3. Run the workflow!")
        else:
            print("⚠️ Installation test had some issues")
            print("Check the error messages above for guidance")
    else:
        print("\n" + "=" * 40)
        print("❌ Installation test FAILED!")
        print("Install missing dependencies and try again")


if __name__ == "__main__":
    main()
