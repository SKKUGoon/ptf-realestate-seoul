from sqlalchemy.dialects.postgresql import INTEGER, VARCHAR, FLOAT, BIGINT
from geoalchemy2 import Geometry

nps_column = {
    'business': VARCHAR,
    'business_reg_stat': INTEGER,
    'j_addr': VARCHAR,
    'r_addr': VARCHAR,
    'bjd': VARCHAR,
    'hjd': VARCHAR,
    'business_own': INTEGER,
    'business_type_nm': VARCHAR,
    'ppl': INTEGER,
    'amount': BIGINT,
    'ppp': FLOAT,
}

road_column = {
    'ENG_RN': VARCHAR,
    'RN': VARCHAR,
    'RN_CD': VARCHAR,
    'ROAD_BT': FLOAT,
    'ROAD_LT': FLOAT,
    'ROA_CLS_SE': VARCHAR,
    'SIG_CD': VARCHAR,
    'WDR_RD_CD': VARCHAR,
    'geometry': Geometry('LineString', srid=4326)
}

road_column_multiline = {
    'ENG_RN': VARCHAR,
    'RN': VARCHAR,
    'RN_CD': VARCHAR,
    'ROAD_BT': FLOAT,
    'ROAD_LT': FLOAT,
    'ROA_CLS_SE': VARCHAR,
    'SIG_CD': VARCHAR,
    'WDR_RD_CD': VARCHAR,
    'geometry': Geometry('MultiLineString', srid=4326)
}

subway_tpop_column = {
    'date': VARCHAR,
    'line': VARCHAR,
    'stn': VARCHAR,
    'time': VARCHAR,
    'embark': INTEGER,
    'disembark': INTEGER
}
