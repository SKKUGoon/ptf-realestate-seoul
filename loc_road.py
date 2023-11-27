import geopandas as gpd
import pandas as pd
from pyproj import CRS

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
        self.data = gpd.read_file(
            loader.data_filename_roadshape_lite_location(),
            encoding='cp949'
        )

        # Replace 'central_meridian_longitude' with the longitude of your central meridian
        grs80_crs = CRS("+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +units=m +no_defs")
        self.data = self.data.to_crs(grs80_crs)
        self.data = self.data.to_crs(epsg=4326)

        # Clean data - pick essential column
        essential_cols = [
            'ENG_RN', 'RN', 'RN_CD',  # 영어 이름, 국문 이름, 도로명 코드
            'ROAD_BT', 'ROAD_LT',  # 도로 폭, 도로 길이
            'ROA_CLS_SE', 'SIG_CD',  # 도로위계기능구분 코드, 시군구 코드
            'WDR_RD_CD', 'geometry'  # 광역도로구분코드, 도형(LINESTRING)
        ]
        self.data = self.data[essential_cols]

        # Assign location to each road - version 1 center point
        self.v1_assign_coorinate()

    def mount_comparison(self, nps: pd.DataFrame, road_name_col: str):
        ...

    def v1_assign_coorinate(self):
        # In version 1, assign middle point of the road
        self.data['location'] = self.data['geometry'].apply(
            lambda x: x.interpolate(0.5, normalized=True)
        )


if __name__ == "__main__":
    roads = RoadMapper()
