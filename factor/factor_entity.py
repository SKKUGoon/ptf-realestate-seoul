from process.data_entity_nps import NPS
from process.loc_road import RoadMapper
from grid.grid import Coordinate, Grid, grid_matching_point
from grid.grid_major_coordinate import GANGNAM_STN_LAT, GANGNAM_STN_LON
from grid.grid_major_coordinate import GangnamStnBoundary

# ---- Data Layout ---- #
nps = NPS()
location = RoadMapper()
location.mount_comparison(nps.data)
locate_nps = location.create_join_data()

# ---- Grid Mapping ---- #
gangnam = Coordinate(GANGNAM_STN_LON, GANGNAM_STN_LAT)
g = Grid(gangnam, GangnamStnBoundary, 100, "GangnamNPS")

# ---- Grid Assigning ---- #
matched = grid_matching_point(g, locate_nps, ('lng', 'lat'), True)
matched_np = matched.to_numpy()

g.push_data_to_grids({v[0]: v[1] for v in matched_np}, 'name', 'string', True)  # entity name
g.push_data_to_grids({v[0]: v[9] for v in matched_np}, 'people', 'number')  # people
g.push_data_to_grids({v[0]: v[10] for v in matched_np}, 'pension', 'number')  # total pension
g.push_data_to_grids({v[0]: v[11] for v in matched_np}, 'avg', 'number')  # ppp

# ---- Grid Spillover ---- #
g.trickle_down(
    [g.grid_element_map[v[0]] for v in matched_np],
    1000 // g.single_size,
    'avg',
    '*0.8'
)

g.trickle_down(
    [g.grid_element_map[v[0]] for v in matched_np],
    1000 // g.single_size,
    'people',
    '*0.6'
)

# ---- Data Display ---- #
df = g.grid_dataframe('avg')
dfn = g.grid_dataframe('name')
dfk = g.kepler_dataframe(['avg', 'people'])
