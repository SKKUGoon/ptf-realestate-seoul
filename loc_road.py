import geopandas as gpd
import pandas as pd
from pyproj import CRS
from shapely.geometry import Point, MultiPoint

from loader import Loader


class RoadMapper:
    """
    Match
        Road (in Seoul) data with LINESTRING(2 coordinatefrom end to end) (standard)
        NPS Entity data. NPS data only gives upper stage of roadname address (comparison)
    """
    def __init__(self):
        loader = Loader()
        loader.set_path("./asset/location/road_shape_lite")
        self.standard = gpd.read_file(
            loader.data_filename_roadshape_lite_location(),
            encoding='cp949'
        )

        # Replace 'central_meridian_longitude' with the longitude of your central meridian
        grs80_crs = CRS("+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +units=m +no_defs")
        self.standard = self.standard.to_crs(grs80_crs)
        self.standard = self.standard.to_crs(epsg=4326)
        print(self.standard.crs)

        # Clean data - pick essential column
        essential_cols = [
            'ENG_RN', 'RN', 'RN_CD',  # 영어 이름, 국문 이름, 도로명 코드
            'ROAD_BT', 'ROAD_LT',  # 도로 폭, 도로 길이
            'ROA_CLS_SE', 'SIG_CD',  # 도로위계기능구분 코드, 시군구 코드
            'WDR_RD_CD', 'geometry'  # 광역도로구분코드, 도형(LINESTRING)
        ]
        self.standard = self.standard[essential_cols]

        # Assign location to each road - version 1 center point
        self.v1_assign_coorinate()

        self.comparison = pd.DataFrame()

    def mount_comparison(self, nps: pd.DataFrame):
        self.comparison = nps

    def create_join_data(self, verbose: bool = False):
        merge_key = ['RN', 'SIG_CD']
        for key in merge_key:
            assert key in self.comparison.columns, f"make sure {key} in comparison data"
            assert key in self.standard.columns, f"make sure {key} in standard data"

        d = pd.merge(self.comparison, self.standard, on=merge_key, how='left')
        d = d.dropna()

        def _calculate_centroid(group: pd.DataFrame):
            if verbose:
                print(group, flush=True)
            # Calculate the centroid for each group
            multipoint = MultiPoint(group['location'].tolist())
            return multipoint.centroid

        # Group by the duplicate key
        dup_key = ['business']
        centroid_df = d.groupby(dup_key).apply(_calculate_centroid).reset_index(name='centroid')

        # Merge the centroid back to the original dataframe
        d = d.drop_duplicates(subset=dup_key).drop(columns='geometry')
        d = d.merge(centroid_df, on=dup_key)

        d['geometry'] = d['centroid']
        d = d.drop(columns='centroid')
        d['lng'] = d['geometry'].apply(lambda x: x.coords[0][0])
        d['lat'] = d['geometry'].apply(lambda x: x.coords[0][1])
        return d

    def v1_assign_coorinate(self):
        # In version 1, assign middle point of the road
        self.standard['location'] = self.standard['geometry'].apply(
            lambda x: x.interpolate(0.5, normalized=True)
        )


if __name__ == "__main__":
    roads = RoadMapper()
