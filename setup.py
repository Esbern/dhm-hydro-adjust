from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dhm-hydro-adjust",
    version="1.0.0",
    description="Tools to make hydrological adjustments to DEM rasters",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    author="Danish Agency for Data Supply and Efficiency (SDFE)",
    author_email="sdfe@sdfe.dk",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "gdal",
        "numpy",
        "scipy",
        "tqdm",
        "geopandas",
        "shapely",
    ],
    extras_require={
        "dev": ["pytest"],
    },
    entry_points={
        "console_scripts": [
            "sample_line_z = hydroadjust.cli.sample_line_z:main",
            "sample_horseshoe_z_lines = hydroadjust.cli.sample_horseshoe_z_lines:main",
            "burn_line_z = hydroadjust.cli.burn_line_z:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: GIS",
    ],
)
