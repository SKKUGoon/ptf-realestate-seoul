from data_float_population import FloatPopulationSubwayTime
from loc_subway import SubwayMapper
from grid import Coordinate, Grid, grid_matching
from grid_major_coordinate import GANGNAM_STN_LAT, GANGNAM_STN_LON
from grid_major_coordinate import GangnamStnBoundary

# ---- Data Layout ---- #
fpt = FloatPopulationSubwayTime(202310)
location = SubwayMapper()
location.mount_comparison(fpt.data, '지하철역', '호선명')
locate_fpt = location.create_join_data()

# ---- Grid Mapping ---- #
gangnam = Coordinate(GANGNAM_STN_LON, GANGNAM_STN_LAT)
g = Grid(gangnam, GangnamStnBoundary, 100, "GangnamSubway")

# ---- Grid Assigning ---- #
matched = grid_matching(g, locate_fpt, ('lon', 'lat'), True)
matched_np = matched.to_numpy()

g.push_data_to_grids({v[0]: v[13] for v in matched_np}, 'arrive0809', 'number', True)  # 08-09 하차인원

# ---- Grid Spillover ---- #
g.trickle_down(
    [g.grid_element_map[v[0]] for v in matched_np],
    1000 // g.single_size,
    'arrive0809',
    '*0.8'
)

# ---- Data Display ---- #
dfn = g.grid_dataframe('arrive0809')
dfk = g.kepler_dataframe(['arrive0809'])
