from process.data_entity_nps import NPS
from process.loc_road import RoadMapper
from grid.grid import Coordinate, Grid, grid_matching_line
from grid.grid_major_coordinate import GANGNAM_STN_LAT, GANGNAM_STN_LON
from grid.grid_major_coordinate import GangnamStnBoundary

# ---- Data Layout ---- #
nps = NPS()
location = RoadMapper(mod='v2')
location.mount_comparison(nps.data)
locate_nps = location.create_join_data()

# ---- Grid Mapping ---- #
gangnam = Coordinate(GANGNAM_STN_LON, GANGNAM_STN_LAT)
g = Grid(gangnam, GangnamStnBoundary, 100, "GangnamNPS")

# ---- Grid Assigning ---- #

# 2) If Grid matching to line
matched_line = grid_matching_line(g, locate_nps, 'line_seg', True)
matched_np_line = matched_line.to_numpy()
