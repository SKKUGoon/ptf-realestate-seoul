import pandas as pd
import geopandas as gpd

from data_entity_nps import NPS
from loc_road import RoadMapper
from grid import Coordinate, Grid, trickle_down
from const_major_coordinate import GANGNAM_STN_LAT, GANGNAM_STN_LON
from const_major_coordinate import GangnamStnBoundary

print("1. Data")
nps = NPS()

location_mapper = RoadMapper()
location_mapper.mount_comparison(nps.data)
d = location_mapper.create_join_data()

print("2. Grid")
gangnam = Coordinate(GANGNAM_STN_LON, GANGNAM_STN_LAT)
g = Grid(gangnam, GangnamStnBoundary, 100)
grid_elements = g.n_by_m_gridelement()

print("3. Assigning a Grid")
cols = ['business', 'ppl', 'amount', 'ppp', 'lng', 'lat']
entities = d[cols]
entities_np = entities.to_numpy()

ett_grid = list()
for entity_info in entities_np:
    print(f"assigning grid for {entity_info[0]}", flush=True)
    entity_lon = entity_info[4]
    entity_lat = entity_info[5]

    for ge in grid_elements:
        if ge.has(entity_lon, entity_lat):
            ett_grid.append([ge.data_single['index'], *entity_info[0:4]])
            break

ett_grid = pd.DataFrame(ett_grid, columns=['grid_index', 'entity_name', 'people', 'total_pension', 'ppp'])

ett_name_dict = {v[0]: v[1] for v in ett_grid.to_numpy()}  # entity name
ett_people_dict = {v[0]: v[2] for v in ett_grid.to_numpy()}  # people
ett_pension_dict = {v[0]: v[3] for v in ett_grid.to_numpy()}  # total pension
ett_avg_pension_dict = {v[0]: v[4] for v in ett_grid.to_numpy()}  # ppp

print("4. Give Grid a Score")
# Add all the values per grdis
for k, v in g.grid_element_map.items():
    # Entity name
    if k in ett_name_dict.keys():
        v.set_data_value('name', f" {ett_name_dict[k]}")
    else:
        v.set_data_value('name', "")

    # People
    if k in ett_people_dict.keys():
        v.set_data_value('people', ett_people_dict[k])
    else:
        v.set_data_value('people', 0)

    # Total pension
    if k in ett_pension_dict.keys():
        v.set_data_value('pension', ett_pension_dict[k])
    else:
        v.set_data_value('pension', 0)

    # Average pension (PPP)
    if k in ett_avg_pension_dict.keys():
        v.set_data_value('ppp', ett_avg_pension_dict[k])
    else:
        v.set_data_value('ppp', 0)

print("5. Grid Trickle down effect")
trickle_down_targets = ['people', 'pension', 'ppp']

for tdt in trickle_down_targets:
    trickles = dict()
    for _, v in g.grid_element_map.items():
        if v.data_single[tdt] != 0:
            trickle = trickle_down(v, tdt, g.single_size, 500)  # Human walking distance 500

            for tk, tv in trickle.items():
                if tk in g.grid_element_map.keys():
                    if tk in trickles.keys():
                        trickles[tk] += tv
                    else:
                        trickles[tk] = tv

    result = list()
    for k, v in g.grid_element_map.items():
        if k in trickles.keys():
            add = trickles[k]
        else:
            add = 0
        result.append(
            [*v.center.coordinate, v.data_single[tdt] + add]
        )
    d = pd.DataFrame(result, columns=['lon', 'lat', tdt])
    d.to_csv(f'./generate/gangnam_test_{tdt}.csv')

