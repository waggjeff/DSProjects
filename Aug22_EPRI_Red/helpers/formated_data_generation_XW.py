# -*- coding: utf-8 -*-
"""
Created on Mon Aug  1 09:45:13 2022

@author: Wang
"""
import warnings
warnings.filterwarnings('ignore')
import pandas as pd
import flow_loop_preprocess_XW as preprocess
import glob


flow_paths = glob.glob('../../Data/flow_loop/*.csv')
i = 0
for path in flow_paths:
    print(f'{len(flow_paths) - i} files remaining')
    file_name = path.split("\\")[-1]
    raw = pd.read_csv(path, header=None)
    raw = preprocess.table_formatting(raw)
    new_path = (r'C:\Users\Wang\OneDrive\Data science\S2DS\Data\flow_loop\processed' 
                + "\\" + file_name)
    raw.to_csv(new_path, index=False, date_format="%Y-%m-%d %H:%M:%S")
    i += 1
