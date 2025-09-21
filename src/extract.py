import os
import time
from dotenv import load_dotenv
import pathlib
import arcpy


def set_environment():
    """
    Set up the environment and workspace.
    """
    script_dir = pathlib.Path(__file__).parent.absolute()
    env_path = script_dir / '.env'
    load_dotenv(env_path)
    arcpy.env.overwriteOutput = True

# TODO: allow user to run outside of ArcGIS Pro
def generate_raster_tiles(fishnet_layer, output_folder, imagery_source, width=1920, height=1536, scale=1200, dpi=300):
    '''
    Generate raster tiles in tiff format from ArcGIS Pro project using fishnet layer.
    To be used in open ArcGIS Pro Project  - in current state, user must first click in map frame to get active view.
    (161 tiles generated in ~15 minutes)
    :param fishnet_layer - string: path to fishnet layer
    :param output_folder - string: path to output folder
    :param imagery_source - string: source of imagery in snake case e.g. "esri_world_imagery" or "nearmap"
    :param width - integer: width of output tiles in pixels (columns)
    :param height - integer: height of output tiles in pixels (rows)
    :param scale - integer: scale of output tiles
    :param dpi - integer: resolution of output tiles in dots per inch
    '''
    #arcpy.env.workspace = output_folder
    #arcpy.env.overwriteOutput = True

    start_time = time.time()
    print(f"Started raster tile generation at: {time.ctime(start_time)}")
    project = arcpy.mp.ArcGISProject("CURRENT")
    active_view = project.activeView

    if active_view:
        # Loop through each grid cell in the fishnet
        with arcpy.da.SearchCursor(fishnet_layer, ["SHAPE@", "OBJECTID"]) as cursor:
            for row in cursor:
                extent = row[0].extent  # Get extent of the current grid cell
                oid = row[1]  # Get unique ID for naming

                # Set map frame extent
                active_view.camera.setExtent(extent)
                # Uncomment the line below and adjust duration (seconds) if imagery does not load quickly enough as extent is changed)
                #time.sleep(3.5)  
                active_view.camera.scale = scale  # Adjust scale to match 1:1200

                # Define output raster path
                output_path = f"{output_folder}\{imagery_source}_tile_{oid}.tif"
                
                # Export map to TIFF
                active_view.exportToTIFF(output_path, width=width, height=height, resolution=dpi, world_file=True)
                
                print(f"Exported: {output_path}")
            print(f"Raster tile generation complete at: {(time.time() - start_time)/60} minutes")
    else:
        print("No active view found in project at this time.")


def generate_raster_tiles_via_layout(fishnet_layer, output_folder, imagery_source, scale=1200, dpi=300):
    '''
    Generate raster tiles in tiff format from ArcGIS Pro project using fishnet layer.
    To be used in open ArcGIS Pro Project  - in current state, user must first click in map frame to get active view.
    (161 tiles generated in ~15 minutes)
    :param fishnet_layer - string: path to fishnet layer
    :param output_folder - string: path to output folder
    :param imagery_source - string: source of imagery in snake case e.g. "esri_world_imagery" or "nearmap"
    :param scale - integer: scale of output tiles
    :param dpi - integer: resolution of output tiles in dots per inch
    '''
    #arcpy.env.workspace = output_folder
    #arcpy.env.overwriteOutput = True

    start_time = time.time()
    print(f"Started raster tile generation at: {time.ctime(start_time)}")
    project = arcpy.mp.ArcGISProject("CURRENT")
    # Assuming there's at least one layout
    layout = project.listLayouts()[0]
    active_view = layout.listElements("MAPFRAME_ELEMENT")[0]

    if active_view:
        # Loop through each grid cell in the fishnet
        with arcpy.da.SearchCursor(fishnet_layer, ["SHAPE@", "OBJECTID"]) as cursor:
            for row in cursor:
                extent = row[0].extent  # Get extent of the current grid cell
                oid = row[1]  # Get unique ID for naming

                # Set map frame extent
                active_view.camera.setExtent(extent)
                # Allow time for the map to refresh - duration may need to be adjusted
                #time.sleep(7)  
                active_view.camera.scale = scale  # Adjust scale to match 1:1200

                # Define output raster path
                output_path = f"{output_folder}\{imagery_source}_tile_{oid}.tif"
                
                # Export map to TIFF
                active_view.exportToTIFF(output_path, resolution=dpi, world_file=True)
                
                print(f"Exported: {output_path}")
            print(f"Raster tile generation complete at: {(time.time() - start_time)/60} minutes")
    else:
        print("No active view found in project at this time.")


def mosaic_rasters(working_dir, common_string, output_raster_name, spatial_ref_wkid=2276, mosaic_method="LAST", pixel_type="8_BIT_UNSIGNED", cell_size=None, number_of_bands=3):
    '''
    Mosaic input rasters to a new raster using specified method.
    :param working_dir - string: path to directory holding input rasters and output raster to be generated
    :param common_string - string: common string in input raster names
    :param output_raster_name - string: name of output raster
    :param spatial_ref_wkid - integer: well-known ID of spatial reference for input and output rasters
    :param mosaic_method - string: method to use for mosaicking
    :param pixel_type - string: pixel type of output raster
    :param cell_size - string: cell size of output raster
    :param number_of_bands - integer: number of bands in output raster
    '''
    start_time = time.time()
    set_environment()
    print(f"Started raster tile mosaic process at: {time.ctime(start_time)}")
    #working_dir_path = os.path.abspath(working_dir)
    input_raster_candidates = [os.path.join(working_dir, f) for f in os.listdir(working_dir) if common_string in f]
    input_rasters = [r for r in input_raster_candidates if '.tif' in r and 'xml' not in r]
    spatial_reference = arcpy.SpatialReference(spatial_ref_wkid)
    print(f"Attempting to mosaic {len(input_rasters)} rasters into a single raster...")
    arcpy.management.MosaicToNewRaster(input_rasters, working_dir, output_raster_name, spatial_reference, pixel_type, cell_size, number_of_bands, mosaic_method)
    print(f"Raster tile mosaic process complete in: {(time.time() - start_time)/60} minutes")    


def preserve_bands(input_raster, output_raster, band_list=[1, 2, 3]):
    '''
    Copy specified bands of input raster to a new raster. (Can be used but may not be necessary as number of bands can be specified for output of mosaic_rasters())
    :param input_raster - string: path to input raster
    :param output_raster - string: path to output raster
    :param band_list - list of integers: list of bands to preserve
    '''
    arcpy.management.CompositeBands([f"{input_raster}\\Band_{b}" for b in band_list], output_raster)


def extract_building_footprints(gdb, in_raster_path, out_prefix):
    '''
    Wrapper for arcpy.geoai.ExtractFeaturesUsingAIModels() function to extract building footprints from input raster.
    gdb - string: path to geodatabase
    in_raster_path - string: path to input raster
    out_prefix - string: prefix for output feature class
    '''
    start_time = time.time()
    print(f"Started building footprint extraction process at: {time.ctime(start_time)}")
    arcpy.geoai.ExtractFeaturesUsingAIModels(
        in_raster=in_raster_path,
        mode="Infer and Postprocess",
        out_location=gdb,
        out_prefix=out_prefix,
        area_of_interest=None,
        pretrained_models="'BUILDING FOOTPRINT EXTRACTION - USA'",
        additional_models=None,
        confidence_threshold=None,
        save_intermediate_output="FALSE",
        test_time_augmentation="FALSE",
        buffer_distance="15 Meters",
        extend_length="25 Meters",
        smoothing_tolerance="30 Meters",
        dangle_length="5 Meters",
        in_road_features=None,
        road_buffer_width="5 Meters",
        regularize_parcels="TRUE",
        post_processing_workflow="Polygon Regularization",
        out_features=None,
        parcel_tolerance="3 Meters",
        regularization_method="Right Angles",
        poly_tolerance="1 Meters",
        prompt="None",
        in_features=None,
        out_summary=None
    )
    print(f"Extraction of building footprints completed in: {(time.time() - start_time)/60} minutes")
