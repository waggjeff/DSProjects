import pandas as pd
import datetime
import math


"""
the function read_anomalies transform the spreadsheet Lablog_processed.xlsx into a list of anomalies,
each one of the form ["anomaly type", begin_datetime, end_datetime].
"""
def read_anomalies(path, sheets="all"):
    file=pd.ExcelFile(path)
    sheets=file.sheet_names[2:] if sheets=="all" else sheets
    file.close()
    anomalies=[]
    for sheet_name in sheets:
        sheet=pd.read_excel(path, sheet_name = sheet_name)
        for _,row in sheet.iterrows():
            anomalies.append([row["event name"],
                              assign_datetime(row["begin_time"],sheet_name),
                              assign_datetime(row["end_time"],sheet_name)])
    return anomalies
def assign_datetime(time: datetime.time,sheet_name):
    if type(time) != datetime.time:
        return None
    else:
        year,month,day=int(sheet_name[0:4]),int(sheet_name[5:7]),int(sheet_name[8:10])
        hour,mins,secs=int(time.hour), int(time.minute), int(time.second)
        return datetime.datetime(year,month,day,hour,mins,secs)