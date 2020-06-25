#!/usr/bin/env python
# coding: utf-8

import shapely
from shapely.ops import split
from shapely.geometry import LineString, Polygon, shape, mapping
import os
import pandas as pd
from matplotlib import pyplot as plt
import fiona
import geopandas as gpd
import sys
from pprint import pprint
from datetime import datetime as dt
import glob
import click

#basepath = os.path.join('/Users','robwebster','Sync','msc_course','dissertation', 'data', 'new_glacier_fronts')
#boxfile = os.path.join(basepath, 'boxes_by_glacier_name_curve', glacier_name)
#boxes_path = os.path.join(basepath, 'boxes_by_glacier_name_curve')
##lines_path = os.path.join(basepath, 'fronts_by_glacier_name_curve')
#linesfile = os.path.join(basepath, 'fronts_by_glacier_name_curve', glacier_name)
#outpath = os.path.join(basepath, 'box_method_files', 'tests')


def get_earliest_year(lines):
    #  Loops through a line layer and returns the earliest year
    early = 2030
    for line in lines:
        if line['properties']['year'] < early:
            early = line['properties']['year']
    return early


def get_years(lines):
    all_years = []
    for line in lines:
        all_years.append(line['properties']['year'])

    return all_years


def box_process(boxfile, linesfile, outpath, w):
    new_polygons = []
    new_lines = []
    avgm_values = []
    rel_retreat_values = []
    current_year = []

    with fiona.open(boxfile) as box:
        boxwidth = box[0]['properties']['width']
        sbox = shape(box[0]['geometry'])
        with fiona.open(linesfile) as lines:
            
            current_glacier = lines[0]['properties']['gl_name']

            print('Processing : ', current_glacier)
            
            fn = current_glacier.lower().split(' glaci')[0].lower()
            out_filepath = os.path.join(outpath, f'{fn}_boxresults.shp')
            
            # Dummy variable to be updated by search for earliest year
            sorted_years = sorted(get_years(lines))
            earliest_year = sorted_years[0]

            #print("Earliest record for this glacier is from", earliest_year, '\n')
            
            # Update the lines schema to include new attributes, ready for writing out new shapefile
            updated_schema = lines.schema
            updated_schema['properties']['measurement'] = 'int:10'
            updated_schema['properties']['rel_posn'] = 'int:10'
            
            # New outputs will include the same attributes as the lines, but now with polygons associated
            # so need to update the geometry type for the new layer to Polygon
            updated_schema['geometry'] = 'Polygon'
            
            # Display details of the schema
            #pprint(updated_schema)
            
            # Open a connection to a new shapefile for writing the outputs
            with fiona.open(out_filepath,'w', driver='ESRI Shapefile', crs=box.crs,schema=updated_schema) as ouput:
                
                #print("Box CRS - ", box.crs['init'])
                #print("Lines CRS - ", lines.crs['init'], '\n')
                
                if not box.crs['init'] == lines.crs['init']:
                    print('CRS of input layers do not match!')
                    sys.exit()
                
                for line in lines:
                    year = int(line['properties']['year'])
                    result = None
                    try:
                        shapely_line = shape(line['geometry'])
                        shapely_line.is_valid
                        #pprint(line['geometry'])
                        
                        # This is the line that actually splits the box with the line,
                        result = split(sbox, shapely_line)
                    
                        # Only valid splits will have more than one feature
                        if len(result) > 1:
                            
                            # Calculate the average front position measurement by dividing resulting polygon
                            # area by the width of the rectilinear box
                            
                            avgm = result[0].area/boxwidth
                            
                            # Update the attributes to include this new measurement
                            line['properties']['measurement'] = int(avgm)
                            
                            # Set the zero point for relative position calculations
                            if year == earliest_year:
                                zero_position = int(avgm)   
                            
                            # Update the various lists to hold results for this iteration
                            current_year.append(line['properties']['year'])
                            new_polygons.append(result)
                            avgm_values.append(avgm)
                            new_lines.append(line)
                            
                        else:
                            print(f'Invalid result for year {year}, continuing...')
                            if year == earliest_year:
                                sorted_years.pop(0)
                                earliest_year = sorted_years[0]
                                #print(f'There was a problem with the earliest record.  New earliest record set to {earliest_year}')
                
                    except:
                        print('Unable to create Shapely geometry from line co-ordinates')


                for line, result in zip(new_lines, new_polygons):
                    try:
                        line['properties']['rel_posn'] = (line['properties']['measurement']) - zero_position
                        
                        # Toggle This For Troubleshooting New Glaciers
                        #pprint(line['properties'])
                        
                        # If 'w' flag is true, the shapefile will be written to disk
                        if w:
                            ouput.write({'geometry':mapping(result[0]),'properties': line['properties']})
                    except:
                        print(f'Error processing {current_glacier}')
                
                print(f"Finished processing {current_glacier}\n")

            # Prepare some frontal change data in a DataFrame for later export and for plotting
            x = []
            y = []

            for poly, line in zip(new_polygons, new_lines):

                x.append(dt.strptime(line['properties']['date'], '%Y%m%d'))
                y.append(line['properties']['rel_posn'])

                glacier = new_lines[0]['properties']['gl_name']
            
                df = pd.DataFrame(y, x)
                df.index = df.index.normalize()
                df = df.sort_index()
                df.rename(columns={df.columns[0] : 'rel_posn'}, inplace=True)
                df['glacier'] = current_glacier

    return new_lines, new_polygons, current_year, current_glacier, df



def show_result_image(new_polygons, current_year):
    fig, ax = plt.subplots(figsize=(10, 10))

    total = zip(new_polygons, current_year)

    #ax.plot(*sbox.exterior.xy)
    #ax.plot(*shapely_test_line.xy)

    for poly, year in total:
        ax.plot(*poly[1].exterior.xy, alpha=0.3)

    plt.show()

def write_result_image(new_polygons, current_year, current_glacier, outpath):
    fig, ax = plt.subplots(figsize=(10, 10))

    total = zip(new_polygons, current_year)

    for poly, year in total:
        ax.plot(*poly[0].exterior.xy, alpha=0.3)

    ax.set_title(f'{current_glacier}')

    figure_file = os.path.join(outpath, 'images', f'{current_glacier}.png')
    plt.savefig(figure_file)
    plt.close()

def show_graph(new_polygons, new_lines):
    fig, ax = plt.subplots(figsize=(20, 10))

    x = []
    y = []

    for poly, line in zip(new_polygons, new_lines):
        x.append(dt.strptime(line['properties']['date'], '%Y%m%d'))
        y.append(line['properties']['rel_posn'])

    glacier = new_lines[0]['properties']['gl_name']
        
        
    df = pd.DataFrame(y, x)
    df.index = df.index.normalize()
    df = df.sort_index()

    ax.set_xlabel('Year', fontsize=20)
    ax.set_ylabel('Frontal position change (metres)', fontsize=20)
    ax.set_title(f'Approximate frontal positions relative to earliest record\n({glacier})', fontsize=20)

    ax.grid()

    ax.plot(df.loc[:])
    ax.scatter(df.index, df.iloc[:,0])

    plt.show()

def write_graph(new_polygons, new_lines, outpath, df):
    fig, ax = plt.subplots(figsize=(20, 10))
    glacier = new_lines[0]['properties']['gl_name']
 
    ax.set_xlabel('Year', fontsize=20)
    ax.set_ylabel('Frontal position change (metres)', fontsize=20)
    ax.set_title(f'Approximate frontal positions relative to earliest record\n({glacier})', fontsize=20)

    ax.grid()

    ax.plot(df.index, df.iloc[:,0])
    ax.scatter(df.index, df.iloc[:,0])

    graph_file = os.path.join(outpath, 'graphs', f'{glacier}_frontal_change.png')
    plt.savefig(graph_file)
    plt.close(fig)

@click.command()
@click.argument('boxes_path', type=click.Path(exists=True))
@click.argument('lines_path', type=click.Path(exists=True))
@click.argument('outpath', type=click.Path(exists=True))
@click.option('--w', is_flag=True, default=False, help='If set, writes output shapefiles')
@click.option('--show_result_images', is_flag=True, default=False, help='If set, plots the resulting polygons and fronts')
@click.option('--show_graphs', is_flag=True, default=False, help='If set, graphs the frontal change')
@click.option('--write_result_images', is_flag=True, default=False, help='If set, writes images of the resulting polygons and fronts')
@click.option('--write_graphs', is_flag=True, default=False, help='If set, saves .png of frontal change graphs')
@click.option('--write_csv', is_flag=True, default=False, help='If set, writes certain data from all glaciers to csv')
def main(boxes_path, lines_path, outpath, w, show_result_images, show_graphs, write_result_images, write_graphs, write_csv):
    
    if not (w==True):
            print('You will not write out the shapefiles')
            #sys.exit()

    all_boxfiles = glob.glob(os.path.join(boxes_path, '*.shp'))
    df_all = pd.DataFrame()

    for boxfile in all_boxfiles:
        glacier = os.path.basename(boxfile)
        linefile = os.path.join(lines_path, glacier)
        result_lines, result_polygons, years, current_glacier, df_latest = box_process(boxfile, linefile, outpath, w)
        if show_result_images:
            show_result_image(result_polygons, result_lines)
        if write_result_images:
            write_result_image(result_polygons, years, current_glacier, outpath)
        if show_graphs:
            show_graph(result_polygons, result_lines)
        if write_graphs:
            write_graph(result_polygons, result_lines, outpath, df_latest)
        if write_csv:
            df_all = pd.concat([df_all, df_latest])
    if write_csv:
        print('writing csv...')
        csv_file = os.path.join(outpath, 'csv', f'glacier_frontal_changes.csv')
        df_all.to_csv(csv_file)

if __name__ == "__main__":
    main()

