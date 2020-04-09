from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from datetime import date
import geopandas as gpd
import os

s1dir = '~/Sync/msc_course/dissertation/data/sentinel-1/'
s2dir = '~/Sync/msc_course/dissertation/data/sentinel-2/'
l8dir = '~/Sync/msc_course/dissertation/data/landsat-8/'
aoidir = '/Users/robwebster/Sync/msc_course/dissertation/data/aoi/'

aoi_json = os.path.join(aoidir, 'sg_aoi.geojson')
print(aoi_json)

# connect to the API
api = SentinelAPI(None, None)

# search by polygon, time, and SciHub query keywords
footprint = geojson_to_wkt(read_geojson(aoi_json))
products = api.query(footprint, date=('20200101', 'NOW'), platformname='Sentinel-1', producttype='SLC', sensoroperationalmode='IW')

# GeoPandas GeoDataFrame with the metadata of the scenes and the footprints as geometries
df = api.to_dataframe(products)
geodf = api.to_geodataframe(products)

#print(df['title'])
#print(geodf['title'])

for id in df['uuid']:
    print(api.get_product_odata(id)['Online'])