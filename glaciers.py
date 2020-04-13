from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from datetime import date
import geopandas as gpd
import os

s1dir = '/Users/robwebster/Sync/msc_course/dissertation/data/sentinel-1/'
s2dir = '/Users/robwebster/Sync/msc_course/dissertation/data/sentinel-2/'
l8dir = '/Users/robwebster/Sync/msc_course/dissertation/data/landsat-8/'
aoidir = '/Users/robwebster/Sync/msc_course/dissertation/data/aoi/'

aoi_json = os.path.join(aoidir, 'sg_aoi.geojson')
#print(aoi_json)

# connect to the API
api = SentinelAPI(None, None)

# search by polygon, time, and SciHub query keywords
aoi = geojson_to_wkt(read_geojson(aoi_json))
from_date = '20200401'
to_date = 'NOW'


def s1(aoi, from_date, to_date, download):
    '''
    Finds online Sentinel-1 imagery
    '''
    products = api.query(aoi, date=(from_date, to_date), platformname='Sentinel-1', producttype='GRD', sensoroperationalmode='IW')

    # Creates Pandas dataframe from results of api query
    df = api.to_dataframe(products)

    # Creates GeoPandas GeoDataFrame with the metadata of the scenes and the footprints as geometries
    geodf = api.to_geodataframe(products)

    #print(df.columns)
    #print(geodf.columns)

    #print(geodf['producttype'])
    #print(geodf['title'])

    print(f'\nSentinel-1 Images from {from_date} to {to_date}:\n')
    
    if not geodf.empty:
        for id in geodf['uuid']:
            print(f"    Product: {api.get_product_odata(id)['title']}  (Online: {api.get_product_odata(id)['Online']})")

    else:
        print('     No valid data in this time period\n')

    if download:
        api.download_all(products, s1dir)

    return geodf

def s2(aoi, from_date, to_date, download):
    '''
    Finds online Sentinel-2 imagery
    '''
    products = api.query(aoi, date=(from_date, to_date), platformname='Sentinel-2', cloudcoverpercentage=(0, 10), producttype='S2MSI2A')

    # Creates Pandas dataframe from results of api query
    df = api.to_dataframe(products)

    # Creates GeoPandas GeoDataFrame with the metadata of the scenes and the footprints as geometries
    geodf = api.to_geodataframe(products)

    #print(df.columns)
    #print(geodf.columns)

    #print(geodf['producttype'])
    #print(geodf['title'])

    print(f'\nSentinel-2 Images from {from_date} to {to_date}:\n')
    
    if not geodf.empty:
        for id in geodf['uuid']:
            print(f"    Product: {api.get_product_odata(id)['title']}  (Online: {api.get_product_odata(id)['Online']})")

    else:
        print('    No valid data in this time period\n')


    if download:
        api.download_all(products, s2dir)   

    return geodf


download = True
s1(aoi, from_date, to_date, download)
s2(aoi, from_date, to_date, download)