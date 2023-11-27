import pandas as pd

from loc_subway import SubwayMapper
from data_float_population import FloatPopulationSubwayTime

from grid import Coordinate, Grid, trickle_down
from const_major_coordinate import GANGNAM_STN_LAT, GANGNAM_STN_LON
from const_major_coordinate import GangnamStnBoundary

print("Assorting data")
fpt = FloatPopulationSubwayTime()

mapper = SubwayMapper()
mapper.mount_comparison(
    fpt.data,
    "지하철역",
    "호선명"
)

mrg = pd.merge(
    mapper.comparison,
    mapper.standard,
    on=['line_name', 'station_name'],
    how='left'
)

unassigned = mrg.loc[mrg['lat'].isnull()]
assigned = mrg.loc[mrg['lat'].notnull()]

# Draw a grid
print("Drawing a grid")

gangnam = Coordinate(GANGNAM_STN_LON, GANGNAM_STN_LAT)
g = Grid(gangnam, GangnamStnBoundary, 100)
grid_elements = g.n_by_m_gridelement()

# For every station, find a grid - n * p process (slow)
print("Assigning a grid")
stations = mapper.standard.copy(deep=True)
stn_np = stations.to_numpy()

stn_grid = list()
for stn_info in stn_np:
    print(f"assigning grid for {stn_info[1]}({stn_info[2]})", flush=True)
    stn_lon = stn_info[3]
    stn_lat = stn_info[4]

    for ge in grid_elements:
        if ge.has(stn_lon, stn_lat):
            stn_grid.append([ge.data_single['index'], *stn_info[1:3]])
            break

# Merge grid data with float population data
stn_grid = pd.DataFrame(stn_grid, columns=["grid_index", "station_name", "line_name"])
float_population_202310 = mapper.comparison.loc[mapper.comparison['사용월'] == 202310]
stn_population = pd.merge(stn_grid, float_population_202310, on=['station_name', 'line_name'], how='left')
stn_population = stn_population[stn_grid.columns.tolist() + ['08시-09시 하차인원']]

# Assign grid element a data. Key is 'float_pop'. If no float_pop give 0

# for search effectiveness turn this into a dictionary.
# key is grid element index and value is float_pop
# there were un-matched station. (station without coordinates) - drop them with dropna()
stn_population_dict = {v[0]: v[-1] for v in stn_population.dropna().to_numpy()}

for k, v in g.grid_element_map.items():
    if k in stn_population_dict.keys():
        # float_pop: population value
        v.set_data_value('float_pop', stn_population_dict[k])
    else:
        v.set_data_value('float_pop', 0)

trickles = dict()
for _, v in g.grid_element_map.items():
    if v.data_single['float_pop'] != 0:
        trickle = trickle_down(v, 'float_pop', g.single_size, 500)  # Human walking distance 500

        for tk, tv in trickle.items():
            if tk in g.grid_element_map.keys():
                if tk in trickles.keys():
                    trickles[tk] += tv
                else:
                    trickles[tk] = tv


# Create csv for kepler.gl
result = list()
for k, v in g.grid_element_map.items():
    if k in trickles.keys():
        add = trickles[k]
    else:
        add = 0
    result.append(
        [*v.center.coordinate, v.data_single['float_pop'] + add]
    )
d = pd.DataFrame(result, columns=['lon', 'lat', 'float_pop'])
d.to_csv('./generate/gangnam_test.csv')
