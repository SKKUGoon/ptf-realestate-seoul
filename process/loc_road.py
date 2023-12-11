import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPoint

from process.loader import Loader


class RoadMapper:
    """
    Match
        Road (in Seoul) process with LINESTRING(2 coordinatefrom end to end) (standard)
        NPS Entity process. NPS process only gives upper stage of roadname address (comparison)
    """
    def __init__(self, mod: str = 'v1'):
        loader = Loader()
        loader.set_path("./asset/location/road_shape_lite")
        self.standard = gpd.read_file(
            loader.data_filename_roadshape_lite_location(),
            encoding='cp949'
        )

        # Replace 'central_meridian_longitude' with the longitude of your central meridian
        self.standard = self.standard.to_crs(epsg=5186)
        self.standard = self.standard.to_crs(epsg=4326)

        # Clean process - pick essential column
        essential_cols = [
            'ENG_RN', 'RN', 'RN_CD',  # 영어 이름, 국문 이름, 도로명 코드
            'ROAD_BT', 'ROAD_LT',  # 도로 폭, 도로 길이
            'ROA_CLS_SE', 'SIG_CD',  # 도로위계기능구분 코드, 시군구 코드
            'WDR_RD_CD', 'geometry'  # 광역도로구분코드, 도형(LINESTRING)
        ]
        self.standard = self.standard[essential_cols]

        # Assign location to each road - version 1 center point
        self.mod = mod
        if self.mod == 'v1':
            # middle point of the line
            self._v1_assign_coordinate()
        elif self.mod == 'v2':
            # line coordinate
            self._v2_assign_line()

        self.comparison = pd.DataFrame()

    def mount_comparison(self, nps: pd.DataFrame):
        self.comparison = nps

    def create_join_data(self, verbose: bool = False):
        if self.mod == 'v1':
            return self._v1_create_join_data(verbose)
        elif self.mod == 'v2':
            return self._v2_create_join_data(verbose)
        else:
            raise NotImplementedError

    def _v1_create_join_data(self, verbose: bool = False):
        merge_key = ['RN', 'SIG_CD']
        for key in merge_key:
            assert key in self.comparison.columns, f"make sure {key} in comparison process"
            assert key in self.standard.columns, f"make sure {key} in standard process"

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

    def _v1_assign_coordinate(self):
        # In version 1, assign middle point of the road
        self.standard['location'] = self.standard['geometry'].apply(
            lambda x: x.interpolate(0.5, normalized=True)
        )

    def _v2_create_join_data(self, verbose: bool = False):
        merge_key = ['RN', 'SIG_CD']
        for key in merge_key:
            assert key in self.comparison.columns, f"make sure {key} in comparison process"
            assert key in self.standard.columns, f"make sure {key} in standard process"

        d = pd.merge(self.comparison, self.standard, on=merge_key, how='left')
        d = d.dropna()

        def _calculate_line(group: pd.DataFrame):
            if verbose:
                print(group, flush=True)
            # Add All the line for each group
            multiline = group['geometry'].tolist()
            return multiline

        # Group by the duplicate key
        dup_key = ['business']
        lines = d.groupby(dup_key).apply(_calculate_line).reset_index(name='line_seg')

        d = d.drop_duplicates(subset=dup_key).drop(columns='geometry')
        d = d.merge(lines, on=dup_key)

        return d

    def _v2_assign_line(self):
        pass


if __name__ == "__main__":
    roads = RoadMapper()
