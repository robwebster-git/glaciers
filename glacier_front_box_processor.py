#!/usr/bin/env python
# coding: utf-8

from shapely.ops import split
from shapely.geometry import LineString, Polygon, shape, mapping
import os
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.dates import YearLocator
import fiona
import sys
from pprint import pprint
from datetime import datetime as dt
import glob
import click


def get_years(lines):
    all_years = []
    for line in lines:
        all_years.append(line['properties']['year'])

    return all_years


def box_process(boxfile, linesfile, outpath, w, invert):
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
            
            fn = current_glacier.lower().split(' glaci')[0]
            out_filepath = os.path.join(outpath, f'{fn}_boxresults.shp')
            
            # Dummy variable to be updated by search for earliest year
            sorted_years = sorted(get_years(lines))
            earliest_year = sorted_years[0]
            
            # Update the lines schema to include new attributes, ready for writing out new shapefile
            updated_schema = lines.schema
            updated_schema['properties']['measurement'] = 'int:10'
            updated_schema['properties']['rel_posn'] = 'int:10'
            
            # New outputs will include the same attributes as the lines, but now with polygons associated
            # so need to update the geometry type for the new layer to Polygon
            updated_schema['geometry'] = 'Polygon'
            
            # Open a connection to a new shapefile for writing the outputs
            with fiona.open(out_filepath,'w', driver='ESRI Shapefile', crs=box.crs,schema=updated_schema) as ouput:
                
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
                            
                            if invert:
                                correct_polygon = result[1]
                                avgm = correct_polygon.area/boxwidth
                            else:
                                correct_polygon = result[0]
                                avgm = correct_polygon.area/boxwidth
                            
                            # Update the attributes to include this new measurement
                            line['properties']['measurement'] = int(avgm)
                            
                            # Set the zero point for relative position calculations
                            if year == earliest_year:
                                zero_position = int(avgm)   
                            
                            # Update the various lists to hold results for this iteration
                            current_year.append(line['properties']['year'])
                            new_polygons.append(correct_polygon)
                            avgm_values.append(avgm)
                            new_lines.append(line)
                            
                        else:
                            print(f'Invalid result for year {year}, continuing...')
                            if year == earliest_year:
                                sorted_years.pop(0)
                                earliest_year = sorted_years[0]
                
                    except:
                        print('Unable to create Shapely geometry from line co-ordinates')


                for line, result in zip(new_lines, new_polygons):
                    try:
                        line['properties']['rel_posn'] = (line['properties']['measurement']) - zero_position
                        
                        # If 'w' flag is true, the shapefile will be written to disk
                        if w:
                            ouput.write({'geometry':mapping(correct_polygon),'properties': line['properties']})
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
        ax.plot(*poly.exterior.xy, alpha=0.3)

    plt.show()

def write_result_image(new_polygons, current_year, current_glacier, outpath):
    fig, ax = plt.subplots(figsize=(10, 10))

    total = zip(new_polygons, current_year)

    for poly, year in total:
        ax.plot(*poly.exterior.xy, alpha=0.4)

    ax.set_title(f'{current_glacier}')

    figure_file = os.path.join(outpath, 'images', f'{current_glacier}.png')
    plt.savefig(figure_file)
    plt.close()

def show_graph(new_polygons, new_lines):
    fig, ax = plt.subplots(figsize=(10, 6))

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

    x_startdate = dt(1930, 1, 1)
    x_enddate = dt(2030,1,1)

    plt.axis([x_startdate, x_enddate, -13000, 1000])

    yloc = YearLocator()
    ax.xaxis.set_minor_locator(yloc)
    ax.minorticks_on()
    ax.grid(True)

    ax.set_axisbelow(True)

    # Customize the major grid
    ax.grid(which='major', linestyle='-', linewidth='0.5', color='black')
    # Customize the minor grid
    ax.grid(which='minor', linestyle='dotted', linewidth='0.5', color='grey')

    ax.plot(df.loc[:])
    ax.scatter(df.index, df.iloc[:,0])

    plt.show()

def write_graph(new_polygons, new_lines, outpath, df):
    fig, ax = plt.subplots(figsize=(10, 6))
    glacier = new_lines[0]['properties']['gl_name']
 
    ax.set_xlabel('Year', fontsize=14)
    ax.set_ylabel('Frontal position change (metres)', fontsize=14)
    ax.set_title(f'Approximate frontal positions relative to earliest record\n({glacier})', fontsize=16)

    x_startdate = dt(1950, 1, 1)
    x_enddate = dt(2030,1,1)

    plt.axis([x_startdate, x_enddate, -13000, 1000])

    yloc = YearLocator()
    ax.xaxis.set_minor_locator(yloc)
    ax.minorticks_on()
    ax.grid(True)

    ax.set_axisbelow(True)

    # Customize the major grid
    ax.grid(which='major', linestyle='-', linewidth='0.5', color='black')
    # Customize the minor grid
    ax.grid(which='minor', linestyle='dotted', linewidth='0.5', color='grey')


    ax.plot(df.index, df.iloc[:,0])
    ax.scatter(df.index, df.iloc[:,0])

    graph_file = os.path.join(outpath, 'graphs', f'{glacier.lower().replace(" ", "_")}_frontal_change.png')
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
@click.option('--invert', is_flag=True, default=False, help='If set, the program thinks the other side of the split lines is the important polygon.  Sometimes needed for curvilinear boxes.  Rectinlinear boxes should not need it if the box has been drawn starting on the upstream part of the glacier')
def main(boxes_path, lines_path, outpath, w, show_result_images, show_graphs, write_result_images, write_graphs, write_csv, invert):

    all_boxfiles = glob.glob(os.path.join(boxes_path, '*.shp'))
    df_all = pd.DataFrame()

    for boxfile in all_boxfiles:
        glacier = os.path.basename(boxfile)
        linefile = os.path.join(lines_path, glacier)
        result_lines, result_polygons, years, current_glacier, df_latest = box_process(boxfile, linefile, outpath, w, invert)
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

