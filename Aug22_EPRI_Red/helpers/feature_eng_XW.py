# -*- coding: utf-8 -*-
"""
Created on Mon Aug 15 11:53:10 2022

@author: Wang
"""

import os
os.chdir(r"C:\Users\Wang\OneDrive\Data science\S2DS\Aug22_EPRI_Red\helpers")
import glob
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

def get_window(df, i, window_size: int = 30, pre_window_size: int = 120):
    """
    Parameters
    ----------
    df : dataframe
        cleaned, per second and labeled df.
    i : int
        starting index, arbitrary.
    window_size : int, optional
        DESCRIPTION. The default is 30.
    pre_window_size : int, optional
        DESCRIPTION. The default is 60.

    Returns
    -------
    window : dataframe
        chunks of the orginal df
    """
    window = df.iloc[(i - pre_window_size) : (i + window_size), :]
    window.index = pd.to_datetime(window.index)
    return window, window_size

def fill_window(window):
    na_feature = []
    for col in window.iloc[:, :-3]:
        test = window[col]
        
        ind = 0
        count = 0
        count_list = []
        ind_list = []
        for row in test:
            if pd.isna(row):
                count += 1
            else:
                if count >= 10:
                    count_list.append(count)
                    count = 0
                    ind_list.append(ind)
                else:
                    count = 0
            ind += 1
        if count_list:
            na_feature.append(1)
           # for i in range(len(count_list)):
           #     end = ind_list[i]
           #     begin = end - count_list[i] 
           #     window.iloc[begin:end, :][col].fillna(0, inplace=True)
        elif count >= 10:
            na_feature.append(1)
            # window[col].tail(count).fillna(0, inplace=True)
        else:
            na_feature.append(0)
    filled_window = window.bfill()
    filled_window = filled_window.ffill()
    return filled_window, na_feature


def get_features(window, na_feature):
    events = window['event']
    window.pop('event')
    
    #add in gradient features
    #create a 5 s gradient df, it means with 90 s of window size, we have 18 points and 17 gradients
    window_grad = window.iloc[:, :-2].resample('5S').mean().diff() / 5
    window_grad = window_grad.dropna()
    #aggregate the data to max, min, mean and std values / needs modifications maybe
    grad_df = window_grad.agg(['max', 'min', 'mean', 'std'])
    # all statistic values into one list, with column names 
    features = []
    columns = []
    features_dic = {}
    for col in grad_df:
        features += grad_df[col].to_list()
        for element in ['max_', 'min_', 'mean_', 'std_']:
            col_name = element + col
            columns.append(col_name)
            
    # add in na_features
    features = features + na_feature
    for col in window.iloc[:, :-2]:
        col_name = 'na_' + col
        columns.append(col_name)
        
    # add in zeek features
    zeek_feature = max(window['zeek1_connections'] + window['zeek2_connections'])
    features.append(zeek_feature)
    columns.append('zeek_conn')
    
    # assign target to the window
    abnormal_events = [event for event in events if event != 'normal']
    if abnormal_events:
        if 'restoring' in abnormal_events:
            target = 'restoring'
        else:
            target = abnormal_events[0]
    else:
        target = 'normal'
    features.append(target)
    columns.append('event')
    # earliest timestamp of the sub_df as key, values list as value
    end_time = window.index.max()
    features_dic[end_time] = features
    return features_dic, columns

def binary_class(target):
    """
    convert the event columns to binary categories: normal and abnormal
    
    """
    if target == 'normal':
        return 'normal'
    else: 
        return 'abnormal'

def ternary_class(target):
    """
    convert the event columns to three categories: normal, mechanical and cyber abnormal
    
    """
    if target == 'normal':
        return 'normal'
    elif target == 'dos' or target == 'injection':
        return 'cyber'
    else:
        return 'mechanical'


if __name__=='__main__':
    raw_dic = {}  
    file_paths = glob.glob("../../Data/flow_loop/flow_loop_plus_zeek/*.csv") 
    for path in file_paths:
        print(path)
        df = pd.read_csv(path, index_col='index')
        i = 300
        while i + 30 <= df.shape[0]:
            sub_df = get_window(df, i)[0]
            sub_df_filled, na_features = fill_window(sub_df)
            feature_dic, columns = get_features(sub_df_filled, na_features)
            target = list(feature_dic.values())[0][-1]
            raw_dic.update(feature_dic)
            if target != 'normal' and target != 'restoring':
                step_size = 10
            else: 
                step_size = 30
            i += step_size
        
    df_new = pd.DataFrame.from_dict(raw_dic, orient='index', columns=columns)
    df_new = df_new[df_new['event'] != 'restoring']
    df_new['binary'] = df_new['event'].apply(binary_class)
    df_new['ternary'] = df_new['event'].apply(ternary_class)
    df_new = df_new.dropna()

    new_path = os.path.join("..", "..", "Data", "flow_loop", "samples", 'final_4.csv')
    df_new.to_csv(new_path)
    
     
     