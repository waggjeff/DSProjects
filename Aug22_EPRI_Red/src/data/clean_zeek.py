import pandas as pd
import os
from datetime import timedelta, datetime
import sys

sys.path.append(os.path.join("..",".."))
import helpers.zeek_logs_parser as zeek
from helpers.zeek_logs_parser import TimeInterval,Log
import helpers.lablog_parser as lablog



# -----------------------------------------------------------------------------
# Constants for reading data
DATA_PATH = os.path.join("..","..","data","raw","Zeek_Sensor_Logs")
LOG_KINDS = [ "conn" ]
SCAN_FIELDS = [
    'ts',
    'id.orig_h','id.orig_p','id.resp_h','id.resp_p',
    'proto'#,'duration'
    ]
LABLOG_PATH = os.path.join("..","..","data","processed")
DAYS = [
    ("07", "14"), ("07", "15"),
    ("07", "18"), ("07", "19"), ("07", "20"), ("07", "21"),
    ("07", "22"), ("07", "25"), ("07", "26"), ("07", "27"), ("07", "28"),
    ("07", "29"), ("08", "01")
]
"""DAYS = [("07","18")]"""
# Constants for storing the output
CLEAN_PATH=os.path.join("..","..","data","processed","Zeek_Sensor_Logs")


# -----------------------------------------------------------------------------
#
def filter_logs(logs,working_hours,log_kinds):
    logs_filtered = []
    for log in logs:
        if log.kind not in log_kinds:
            continue
        if log.t_interval[1] < working_hours[0] \
                or log.t_interval[0] > working_hours[1]:
            continue
        logs_filtered.append(log)
    return logs_filtered

def events_into_df(logs, filter_by_datetime, working_hours, fields: []=['ts']):
    logs_df = pd.DataFrame()
    for log in logs:
        log.read_events(fields,filter_by_datetime, working_hours)
        log_df = pd.DataFrame(
            {
                field : [ event[field] for event in log.events ] for field in fields
            }
        )
        log_df['ts'] = log_df['ts'].apply(lambda x: datetime.fromtimestamp(x) - timedelta(hours=6))
        log_df.rename(columns = {'ts' : 'datetime'} , inplace = True)
        #add a column with event kind
        log_df['kind'] = [ log.kind for event in log.events ]
        log_df.index = log_df['datetime']
        log_df = log_df.drop(columns=['datetime'])
        logs_df = pd.concat([logs_df, log_df], axis=0)
    return logs_df.sort_index()

def filter_by_datetime(content,time_interval):
    event_datetime = datetime.fromtimestamp(content['ts'])
    filter = True if event_datetime < time_interval[0] \
                  or time_interval[1] < event_datetime \
                  else False
    return filter


# -----------------------------------------------------------------------------
# Main block of code executed when the script runs as main

if __name__ == "__main__":
    for month, day in DAYS:

        #read files in date folder
        date_str = "2022-"+month+"-"+day
        path_1=os.path.join(DATA_PATH,"zeek-1_101",date_str)
        path_2=os.path.join(DATA_PATH,"zeek-2_102",date_str)
        #log file names
        logs1_raw, logs2_raw = zeek.read_log_names(path_1,month,day),\
                               zeek.read_log_names(path_2,month,day)
        #working hours from Lablog
        working_hours=lablog.read_anomalies(
            os.path.join(LABLOG_PATH,"Lablog_processed.xlsx"),[date_str]
        )[0][1:3]
        #filter uninteresting logs
        logs1_filtered, logs2_filtered = filter_logs(logs1_raw,working_hours,LOG_KINDS),\
                                         filter_logs(logs2_raw,working_hours,LOG_KINDS)
        #avoid generating empty files
        logs1 = [logs1[0]] if len(logs1_filtered) == 0 else logs1_filtered
        logs2 = [logs2[0]] if len(logs2_filtered) == 0 else logs2_filtered
        #create csv files with the contents
        events_into_df(logs1,filter_by_datetime,working_hours,SCAN_FIELDS).to_csv(os.path.join(CLEAN_PATH, 'zeek1', date_str + '.csv'))
        print("Created file ",os.path.join(CLEAN_PATH, 'zeek1', date_str + '.csv'))
        events_into_df(logs2,filter_by_datetime,working_hours,SCAN_FIELDS).to_csv(os.path.join(CLEAN_PATH, 'zeek2', date_str + '.csv'))
        print("Created file ",os.path.join(CLEAN_PATH, 'zeek2', date_str + '.csv'))
