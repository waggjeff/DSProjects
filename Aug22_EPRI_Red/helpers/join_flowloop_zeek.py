import pandas as pd
import os
from datetime import datetime
import sys
sys.path.append(os.path.join("..",".."))
import helpers.lablog_parser as lablog


# -----------------------------------------------------------------------------
# Constants for reading data
DATA_PATH_ZEEK = os.path.join("..","data","processed","Zeek_Sensor_Logs")
DATA_PATH_FLOWLOOP =  os.path.join("..","data","processed","flow_loop_clean")
DAYS = [
    ("07", "14"), ("07", "15"), ("07", "18"), ("07", "19"),
    ("07", "20"), ("07", "21"), ("07", "22"), ("07", "25"),
    ("07", "26"), ("07", "27"), ("07", "28"), ("07", "29"),
    ("08", "01")
]
"""DAYS = [("07","29")]"""
LABLOG_PATH = os.path.join("..","data","processed")
# Constants for storing the output
CLEAN_PATH=os.path.join("..","data","processed","flow_loop_plus_zeek")


if __name__ == '__main__':
    for month, day in DAYS:
        print(month,day)
        data_zeek1 = pd.read_csv(os.path.join(DATA_PATH_ZEEK, 'zeek1', '2022-'+month+'-'+day+'.csv'),
         parse_dates=True,index_col='datetime')
        data_zeek1_1sec = pd.DataFrame(
            {"datetime": [lablog.read_anomalies(LABLOG_PATH,["2022-"+month+"-"+day])[1]]}
        ) if len(data_zeek1) == 0 else data_zeek1['kind'].resample("1S").count()
        data_zeek2 = pd.read_csv(os.path.join(DATA_PATH_ZEEK, 'zeek2', '2022-'+month+'-'+day+'.csv'),
                           parse_dates=True, index_col='datetime')
        data_zeek2_1sec = pd.DataFrame(
            {"datetime": [lablog.read_anomalies(LABLOG_PATH,["2022-"+month+"-"+day])[1]]}
        ) if len(data_zeek2) == 0 else data_zeek2['kind'].resample("1S").count()

        data_flowloop = pd.read_csv(os.path.join(DATA_PATH_FLOWLOOP,"Flow_Loop_Data_"+month+day+"22.csv"),
                      parse_dates=True,index_col='index')
        new_data = data_flowloop
        new_data["zeek1_connections"] = data_zeek1_1sec
        new_data["zeek2_connections"] = data_zeek2_1sec
        new_data["zeek1_connections"] = new_data["zeek1_connections"].fillna(0)
        new_data["zeek2_connections"] = new_data["zeek2_connections"].fillna(0)
        #create csv file
        new_data.to_csv(os.path.join(CLEAN_PATH, "Flow_Loop_Data_"+month+day+"22.csv"))
