import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine
from geoalchemy2 import WKTElement
from dotenv import load_dotenv

import os
from typing import Literal


class SimpleDatabaseAccess:
    def __init__(self):
        load_dotenv()
        username = os.getenv('USER')
        password = os.getenv('PASSWORD')
        host = os.getenv('HOST')
        port = os.getenv('PORT')
        name = os.getenv('NAME')

        # Create an engine
        self.engine_str = f'postgresql://{username}:{password}@{host}:{port}/{name}'

    @staticmethod
    def _retrieve_table_name(value: str):
        table = os.getenv(value)
        if table == "" or table is None:
            raise KeyError(f"no {value} was found in env")

        if '.' in table:
            # It contains a schema
            return table.split('.')
        else:
            return None, table

    def insert_dataframe(self,
                         data: pd.DataFrame,
                         target_table: str,
                         column_type: dict,
                         if_exists: Literal['append', 'replace'],
                         verbose: bool = True):
        schema, table = self._retrieve_table_name(target_table)

        engine = create_engine(self.engine_str)
        if column_type is None:
            data.to_sql(
                table,
                engine,
                schema=schema,
                if_exists=if_exists,
                index=False
            )
        else:
            data.to_sql(
                table,
                engine,
                schema=schema,
                if_exists=if_exists,
                index=False,
                dtype=column_type,
            )
        if verbose:
            print(f"Inserted {len(data)} rows into {table}")
        engine.dispose()

    def insert_geo_dataframe(self,
                             data: gpd.GeoDataFrame,
                             target_table: str,
                             column_type: dict,
                             geometry_column: str = 'geometry',
                             epsg: int = 4326,
                             verbose: bool = True):
        # Data column type check
        assert geometry_column in column_type.keys()
        schema, table = self._retrieve_table_name(target_table)

        # Before using `to_sql`, convert the geometry column in your DataFrame to WKT(Well-Known Text)
        # using element (WKTElement). This is necessary because geoalchemy2 expects geometries in WKT format
        # Should be single geometry column.
        df = data.copy(deep=True)
        df[geometry_column] = df[geometry_column].apply(
            lambda x: WKTElement(x.wkt, srid=epsg)
        )

        engine = create_engine(self.engine_str)
        df.to_sql(table, con=engine, schema=schema, if_exists='replace', index=False, dtype=column_type)
        if verbose:
            print(f"Inserted {len(data)} rows into {table}")
        engine.dispose()

    def select_dataframe(self, target_table: str, verbose: bool = True):
        schema, table = self._retrieve_table_name(target_table)

        query = f"SELECT * FROM {schema}.{table}"
        engine = create_engine(self.engine_str)

        if verbose:
            print(f"Sending query {query}")
        df = pd.read_sql(query, engine)
        engine.dispose()
        return df

    def select_geo_dataframe(self, target_table: str, geometry_column: str = 'geometry', verbose: bool = True):
        schema, table = self._retrieve_table_name(target_table)

        query = f"SELECT * FROM {schema}.{table}"
        engine = create_engine(self.engine_str)

        if verbose:
            print(f"Sending geo query {query}")
        gdf = gpd.read_postgis(query, engine, geom_col=geometry_column)
        engine.dispose()
        return gdf

