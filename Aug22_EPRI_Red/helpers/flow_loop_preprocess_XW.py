import os
os.chdir(r"C:\Users\Wang\OneDrive\Data science\S2DS\Aug22_EPRI_Red\helpers")
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from datetime import timedelta
import lablog_parser as lablog

def table_formatting(raw):
    """
    Setting the raw df to a nice format
    
    Parameters
    ----------
    raw : Dataframe
        The raw dataframe get from pd.read_csv('path', header=None)

    Returns
    -------
    raw: Dataframe 
        formatted dataframe with correct column name and data types
    """
    # set the columns names as time_feature, feature
    for i in range(raw.shape[1]-1):
        if pd.isna(raw.iloc[4, i]):
            raw.iloc[4, i] = 'time_' + raw.iloc[4, i+1]
    raw.columns = list(raw.iloc[4, :])

    # start from row index 8, drop 1st and last columns since no info there
    raw = raw.iloc[8:, 1:-1].reset_index(drop=True)

    # replace all empty string to nan
    raw.replace(' ', np.nan, inplace=True)

    # now all columns are object types, which shall be corrected
    # column with odd number index should be datetime, col with even number index shall be numeric
    for i in range(raw.shape[1]):
        if i % 2 == 0:
            raw.iloc[:, i] = pd.to_datetime(raw.iloc[:, i], errors='coerce')
        else:
            raw.iloc[:, i] = pd.to_numeric(raw.iloc[:, i], errors='coerce')
    
    return raw


def pull_feature(idx1, idx2, data):
    """
    Extract two columns from formatted df, presumably, idealy idx1 = time_feature, idx2 = feature
    
    Parameters
    ----------
    idx : int
        the index of first column
    data: dataframe
        formatted dataframe 
        
    Returns
    -------
    feature_data: Dataframe 
        dataframe contains 
    """
    feature_data = data.iloc[:, [idx1, idx2]]
    feature_data.dropna(inplace=True)
    feature_data = feature_data.set_index(list(feature_data)[0], drop=True)
    return feature_data


def resample(data, time_interval:str, fill = False):
    """
    changing the interval with the values of the series. the values within each interval are grouped 
    
    Parameters
    ----------
    time_interval : str
        the length of the time interval, shall be string, e.g. '10S', '30S', '1Min', '2Min'
    data : dataframe
        formated.

    Returns
    -------
    df : dataframe
        df with new time_interval.

    """
    for col in data:
        if data[col].dtype == 'O':
            data[col] = pd.to_datetime(data[col])
    i = 0
    while i <= (data.shape[1] - 2):
        # pick every sensor data with its timeseries 
        sub_df = pull_feature(i, i+1, data)
        # resample with the given time_interval and take mean value
        if fill:
            sub_df = sub_df.resample(time_interval).mean().bfill()
        else:
            sub_df = sub_df.resample(time_interval).mean()
        if i == 0:
            df = sub_df
        else:
            # join to one uniform timeindex
            df = df.join(sub_df, how='outer')
        i += 2
        # take only the raw values
        df = df.loc[:, df.columns.str.contains('Raw')]
    return df

def labeling(date:str, df, rest_int: int = 5):
    """
    label the per second flow loop dataframe, labels are normal, restoring, and specific event name 
    
    Parameters
    ----------
    date : str
        the day the flow loop data was collected, format as "Year-month-day"
    data : dataframe
        formated and resampled (1s) df
    rest_int: int
        the minustes after event end shall be considered as restoring, default 5 mins

    Returns
    -------
    df : dataframe
        df with labels

    """
    path=os.path.join("..","data","raw","Lablog_processed.xlsx")
    anomalies=lablog.read_anomalies(path,[date])
    sod = anomalies[0][1] + timedelta(minutes=5)
    eod = anomalies[0][2] - timedelta(minutes=5)
    df = df[sod:eod]
    if len(anomalies) == 1:
        event_df = pd.DataFrame(index=df.index)
        event_df['event'] = 'normal' 
    else:
        event_df = pd.DataFrame()
        for anomaly in anomalies:
            if anomaly[0] != 'period':
                anomalie_period = pd.period_range(anomaly[1], anomaly[2], freq='S')
                restoring_period = pd.period_range(anomaly[2]+timedelta(seconds=1), 
                                                   anomaly[2]+timedelta(minutes=rest_int), freq='S')
                anomaly_df = pd.DataFrame(index=anomalie_period)
                anomaly_df['event'] = anomaly[0]
                restoring_df = pd.DataFrame(index=restoring_period)
                restoring_df['event'] = 'restoring'
                sub_df = pd.concat([anomaly_df, restoring_df])
                event_df = pd.concat([event_df, sub_df])
        event_df.index = event_df.index.to_timestamp()

    df = df.join(event_df, how='left')  
    df['event'] = df['event'].fillna('normal')
    df = df.reset_index().drop_duplicates(subset='index', keep='last')
    df = df.set_index('index', drop=True)
    return df



def feature_plot(idx1, idx2, data):
    """
    plot feature regards its timestamp, presumably, idealy idx1 = time_feature, idx2 = feature
    
    Parameters
    ----------
    idx1, 2 : int
        the index of first column and second column
    data: dataframe
        formatted dataframe 
        
    Returns
    -------
    feature plot with timestamp as x axis
    """
    feature_data = pull_feature(idx1, idx2, data)
    plt.figure(figsize=(20, 6))
    plt.plot(feature_data, '.')
    plt.title(feature_data.columns[0])
    plt.show()
    return 


def feature_correlation(idx1, idx2, idx3, idx4, data):
    """
    plot two features on the same time scale to check their correlation
    
    Parameters
    ----------
    idx1, 2, 3, 4 : int
        the index of 1st, 2nd, 3rd 4th column
        
    data: dataframe
        formatted dataframe 
        
    Returns
    -------
    plot of two features on the same time axis
    """
    data1 = pull_feature(idx1, idx2, data)
    data2 = pull_feature(idx3, idx4, data)
    plt.figure(figsize=(20, 6))
    plt.plot(data1, label='calculated values')
    plt.plot(data2, label='raw values')
    plt.legend()
    plt.yscale('log')
    plt.title(data1.columns[0])
    plt.show()    
    return 


class loop():
    def __init__(self, path):
        self.path = path
        self.data = pd.read_csv(self.path, header=None)
        #self.df = table_formattting(self.data)
    
    def formatting(self):
        self.df = table_formatting(self.data)
        return
    
    def transform(self, time_interval):
        self.df = resample(time_interval, self.df)
        return
    

        
        
        
        
        
        
        
        