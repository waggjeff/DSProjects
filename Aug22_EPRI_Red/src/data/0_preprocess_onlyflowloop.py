# This script generates a training dataset from the data on BUSY_DAYS
# and QUIET_DAYS according to the methods sampling_method() and feature_eng()
# defined below.
# This might serve as a good template for implementing different
# proposals for feature engineering. For that, you might modify these functions
# and run the script as it is to generate a training set with the new features.


import pandas as pd
from pandas import DataFrame
import numpy as np
import os
from datetime import timedelta, datetime

import sys
sys.path.append("../..")
import helpers.lablog_parser as lablog

from math import ceil


# -----------------------------------------------------------------------------
# Constants for reading data
DATA_PATH = os.path.join("..", "..", "data", "processed")
LABLOG_PATH = os.path.join("..", "..", "data", "processed")
QUIET_DAYS = [
    ("07", "13"), ("07", "14"), ("07", "17")
]
BUSY_DAYS = [
    ("07", "15"), ("07", "18"), ("07", "19"), ("07", "20"), ("07", "21"),
    ("07", "22"), ("07", "25"), ("07", "26"), ("07", "27"), ("07", "28"),
    ("07", "29"), ("08", "01")
]
# Constants for storing the output
TR_PATH = os.path.join("..", "..", "data", "training")
NAME_TR_FILE = "training_0_preprocess_onlyflowloop.csv"


# -----------------------------------------------------------------------------
# methods determining how we extract the training dataset

def sampling_method(event: list) -> datetime:
    """
       Samples a time to generate a training sample.

       In particular, this function generates a datetime 2 mins after the start of the event.

       Parameters
       ----------
       event : list
           List containing lablog's information [event_kind,start_time,end_time]

       Returns
       -------
       sample_datetime : datetime
           Datetime 2 minutes after the start of the event
       """
    sample_datetime = event[1] + timedelta(minutes=2)
    return sample_datetime


def feature_eng(df: DataFrame, event_kind: str, event_time: datetime) -> DataFrame:
    """
       Computes features representing the event at time event_time.

       In particular, this function computes the standard deviation of each
       raw signal in the Flow Loop data during the 2 mins before the event.

       Parameters
       ----------
       df : Dataframe
           Flow Loop timeseries
       event_kind : str
           Type of event. In the simplest case: normal/abnormal <-> 0/1
       event_time : datetime
           Time returned from sampling_method(event)

       Returns
       -------
        : Dataframe
           One-row dataframe containing features and label.
       """
    # compute features
    label = 0 if event_kind == "normal" else 1
    scanning_interval = timedelta(minutes=2)
    features = df[event_time - scanning_interval:event_time].std()
    # prepare output
    values = np.matrix(np.append(event_time,np.append(features, label)))
    columns = features.index.tolist()
    columns.append("Label")
    columns.insert(0, 'Datetime')
    return pd.DataFrame(values, columns=columns)


# -----------------------------------------------------------------------------
# method for generating normal samples

def generate_normal_samples(n_abnormal: int, proportion: int =1) -> DataFrame:
    """
       Generate samples for normal events from QUIET_DAYS

       Parameters
       ----------
       n_abnormal : int
           number of abnormal events generated before invoking this function
       proportion : float
           desired proportion of normal points vs abnormal points

       Returns
       -------
       tr_normal_samples : Dataframe
           DataFrame containing features and label for normal events
       """
    global QUIET_DAYS
    #TODO: improve on that
    n_normal_per_day = {
        QUIET_DAYS[0] : ceil(3/7 * proportion * n_abnormal),
        QUIET_DAYS[1] : ceil(3/7 * proportion * n_abnormal),
        QUIET_DAYS[2] : ceil(1/7 * proportion * n_abnormal)
    }  # amount of normal events to be sampled from each day
    tr_normal_samples = pd.DataFrame()
    for month, day in QUIET_DAYS:
        df = read_clean_data(month, day)
        working_interval = read_lablog(month, day)[0]
        event_times = [
            working_interval[1] + i * (working_interval[2] - working_interval[1]) / n_normal_per_day[(month,day)]
            for i in range(1, n_normal_per_day[(month,day)])
        ]
        tr_samples_of_the_day = pd.DataFrame()
        for t in event_times:
            new_sample = feature_eng(df, "normal", t)
            tr_samples_of_the_day = pd.concat(
                [tr_samples_of_the_day, new_sample],
                ignore_index=True, sort=False
            )
        tr_normal_samples = pd.concat([tr_normal_samples, tr_samples_of_the_day], ignore_index=True, sort=False)
    return tr_normal_samples


# -----------------------------------------------------------------------------
# auxiliary methods

def read_clean_data(month: str, day: str, file_name_root: str ="Flow_Loop_Data_") -> DataFrame:
    """
       Read "clean and homogeneous" data of a given day

       Parameters
       ----------
       month : str
       day : str
       file_name_root : str
           Beginning of the name of the file to be read. The file where the
           clean and homogeneous data is stored is called something like
           "Flow_Loop_Data_monthdayyear.csv"

       Returns
       -------
       df: DataFrame
           DataFrame with the "clean and homogeneous" timeseries
       """
    global DATA_PATH
    df = pd.read_csv(os.path.join(DATA_PATH, "flow_loop_clean", file_name_root + month + day + "22.csv"), index_col="index")
    df.index = pd.to_datetime(df.index)
    return df


def read_lablog(month: str, day: str) -> list:
    """
       Read events in a given day stored in Lablog_processed.xlsx

       Parameters
       ----------
       month : int
       day : int

       Returns
       -------
       events: list
           List formatted as [event_kind,start_time,end_time]
       """
    global LABLOG_PATH
    path = os.path.join(LABLOG_PATH, "Lablog_processed.xlsx")
    events = lablog.read_anomalies(path, ["2022-" + month + "-" + day])
    return events


# -----------------------------------------------------------------------------
# Main block of code executed when the script is executed


if __name__ == "__main__":

    # Generate abnormal samples
    tr_samples = pd.DataFrame()
    for month, day in BUSY_DAYS:
        df = read_clean_data(month, day)
        abnormal_events = read_lablog(month, day)
        tr_samples_of_the_day = pd.DataFrame()
        for event in abnormal_events:
            event_time = sampling_method(event)
            event_kind = event[0]
            new_sample = feature_eng(df, event_kind, event_time)
            tr_samples_of_the_day = pd.concat(
                [tr_samples_of_the_day, new_sample],
                ignore_index=True, sort=False
            )
        tr_samples = pd.concat([tr_samples, tr_samples_of_the_day], ignore_index=True, sort=False)

    # add normal events
    tr_normal_samples = generate_normal_samples(len(tr_samples))
    tr_samples = pd.concat([tr_samples, tr_normal_samples], ignore_index=True, sort=False)

    # randomize order
    tr_samples = tr_samples.sample(frac=1).reset_index(drop=True)

    # store into a file
    tr_samples.to_csv(os.path.join(TR_PATH, NAME_TR_FILE))

    # print message
    print("Training set generated. Days considered:")
    print("Quiet days: ".rjust(30),QUIET_DAYS)
    print(" "*10,"Busy days: ".rjust(30),BUSY_DAYS)
    print("File created: ", os.path.join(TR_PATH, NAME_TR_FILE))

# -----------------------------------------------------------------------------
