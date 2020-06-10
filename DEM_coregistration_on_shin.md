# Coregistering two DEMs on shin.geos.ed.ac.uk

There are two methods:  using `dem_coreg.sh` or using `dem_align.py`.

## Initial Setup

You will need to activate the conda environment before running the programs:

`conda activate demcoreg`

You will need to have the following paths to the programs and conda environment in your PATH variable:
*(I WILL CHANGE THIS WHEN I GET A CHANCE SO THEY'RE NOT IN MY HOME DIRECTORY)*

Conda Environment:
`/scratch/s0092179/miniconda/base/bin`

Paths to Scripts:
`/home/s0092179/src/demcoreg/demcoreg`
`/home/s0092179/src/imview/imview`
`/home/s0092179/src/pygeotools/pygeotools`

For `dem_coreg.sh` only:
`/home/s0092179/src/StereoPipeline-2.6.2-2019-06-17-x86_64-Linux/bin`

## dem_coreg.sh

### USAGE

`dem_coreg.sh source_dem ref_dem`

Source DEM and Reference DEM are geotiffs in AEA projection.

Before you can run this command, you need to identify reference surfaces by using `dem_mask.py`:

### Preparing using `dem_mask.py`

```bash
usage: dem_mask.py [-h] [--outdir OUTDIR] [--writeout] [--toa]
                   [--toa_thresh TOA_THRESH] [--snodas]
                   [--snodas_thresh SNODAS_THRESH] [--modscag]
                   [--modscag_thresh MODSCAG_THRESH] [--bareground]
                   [--bareground_thresh BAREGROUND_THRESH] [--glaciers]
                   [--nlcd]
                   [--nlcd_filter {rock,rock+ice,rock+ice+water,not_forest,not_forest+not_water,none}]
                   [--dilate DILATE]
                   dem_fn

Identify control surfaces for DEM co-registration

positional arguments:
  dem_fn                DEM filename

optional arguments:
  -h, --help            show this help message and exit
  --outdir OUTDIR       Directory for output products
  --writeout            Write out all intermediate products, instead of only
                        final tif
  --toa                 Use top-of-atmosphere reflectance values (requires
                        pregenerated "dem_fn_toa.tif")
  --toa_thresh TOA_THRESH
                        Top-of-atmosphere reflectance threshold (default: 0.4,
                        valid range 0.0-1.0), mask values greater than this
                        value
  --snodas              Use SNODAS snow depth products
  --snodas_thresh SNODAS_THRESH
                        SNODAS snow depth threshold (default: 0.2 m), mask
                        values greater than this value
  --modscag             Use MODSCAG fractional snow cover products
  --modscag_thresh MODSCAG_THRESH
                        MODSCAG fractional snow cover percent threshold
                        (default: 50%, valid range 0-100), mask greater than
                        this value
  --bareground          Enable bareground filter
  --bareground_thresh BAREGROUND_THRESH
                        Percent bareground threshold (default: 60%, valid
                        range 0-100), mask greater than this value (only
                        relevant for global bareground data)
  --glaciers            Mask glacier polygons
  --nlcd                Enable NLCD LULC filter (for CONUS)
  --nlcd_filter {rock,rock+ice,rock+ice+water,not_forest,not_forest+not_water,none}
                        Preserve these NLCD pixels (default: not_forest)
  --dilate DILATE       Dilate mask with this many iterations (default: None)
```

### Considerations for Glacier Masking

If you already have data such as glacier polygons to use for masking, then you need to specify the location using the environment variable DATADIR, before you run the script:

`export DATADIR=/path/to/directory/`

The program expects the glacier polygons to be in a file called `rgi60_merge.shp` under this DATADIR folder, in folders called `rgi60/regions`.

The relevant part of the code is `rgi_fn = os.path.join(datadir, 'rgi60/regions/rgi60_merge.shp')`

Then you can run the program.  Example usage:

`dem_mask.py --glaciers --outdir masked_dems source_dem.tif`
`dem_mask.py --glaciers --outdir masked_dems reference_dem.tif`

This produces some extra files in the specified directory (`source_dem_warp.tif`, `source_dem_ref.tif` and so on).  For some reason you have to specify an output directory, and then move the outputs back into the same directory as the DEMs you want to coregister.

Next, run `dem_coreg.sh` as follows:

`dem_coreg.sh source_dem ref_dem`

Note:  The source DEM is the one that is moved, the reference DEM stays where it is.

## dem_align.py

This program can be used in a single line, as follows (it calls `dem_mask.py` within the program, so you still need to have the environment variable `$DATADIR` set so it can find your RGI glacier shapefile otherwise it will try to download afresh):

`dem_align.py -mask_list 'glaciers' -tiltcorr -polyorder 2 -outdir output_directory reference_dem.tif source_dem.tif`

For full usage options, see:

```bash
usage: dem_align.py [-h] [-mode {ncc,sad,nuth,none}]
                    [-mask_list {toa,snodas,modscag,bareground,glaciers,nlcd,none} [{toa,snodas,modscag,bareground,glaciers,nlcd,none} ...]]
                    [-tiltcorr] [-polyorder POLYORDER] [-tol TOL]
                    [-max_offset MAX_OFFSET] [-max_dz MAX_DZ]
                    [-res {min,max,mean,common_scale_factor}]
                    [-slope_lim SLOPE_LIM SLOPE_LIM] [-max_iter MAX_ITER]
                    [-outdir OUTDIR]
                    ref_fn src_fn

Perform DEM co-registration using multiple algorithms

positional arguments:
  ref_fn                Reference DEM filename
  src_fn                Source DEM filename to be shifted

optional arguments:
  -h, --help            show this help message and exit
  -mode {ncc,sad,nuth,none}
                        Type of co-registration to use (default: nuth)
  -mask_list {toa,snodas,modscag,bareground,glaciers,nlcd,none} [{toa,snodas,modscag,bareground,glaciers,nlcd,none} ...]
                        Define masks to use to limit reference surfaces for
                        co-registration (default: [])
  -tiltcorr             After preliminary translation, fit polynomial to
                        residual elevation offsets and remove (default: False)
  -polyorder POLYORDER  Specify order of polynomial fit (default: 1)
  -tol TOL              When iterative translation magnitude is below this
                        tolerance (meters), break and write out corrected DEM
                        (default: 0.02)
  -max_offset MAX_OFFSET
                        Maximum expected horizontal offset in meters, used to
                        set search range for ncc and sad modes (default: 100)
  -max_dz MAX_DZ        Maximum expected vertical offset in meters, used to
                        filter outliers (default: 100)
  -res {min,max,mean,common_scale_factor}
                        Warp intputs to this resolution (default: mean)
  -slope_lim SLOPE_LIM SLOPE_LIM
                        Minimum and maximum surface slope limits to consider
                        (default: (0.1, 40))
  -max_iter MAX_ITER    Maximum number of iterations, if tol is not reached
                        (default: 30)
  -outdir OUTDIR        Output directory (default: None)
```
