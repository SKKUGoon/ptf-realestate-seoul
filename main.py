import pandas as pd
import geopandas as gpd
from dao.dao import SimpleDatabaseAccess

dao = SimpleDatabaseAccess()

df = dao.select_geo_dataframe('CLEAN_PENSION')
