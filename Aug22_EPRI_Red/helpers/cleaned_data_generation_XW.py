# -*- coding: utf-8 -*-
"""
Created on Mon Aug 15 10:26:03 2022

@author: Wang
"""

import os
os.chdir(r"C:\Users\Wang\OneDrive\Data science\S2DS\Aug22_EPRI_Red\helpers")
os.getcwd()
import glob
import pandas as pd
import flow_loop_preprocess_XW as process
import re

file_paths = glob.glob("../../Data/flow_loop/processed/*.csv")
i = 0
for path in file_paths:
    print(f'{len(file_paths) - i} files ramaining')
    file_name = path.split("\\")[-1]
    date = re.findall(r'[0-9]+', path)[0]
    month = date[:2]
    day = date[2:4]
    year = '20' + date[4:]
    formatted_date = f'{year}-{month}-{day}'
    df = pd.read_csv(path)
    df = process.resample(df, '1S')
    df = process.labeling(formatted_date, df)
    new_path = os.path.join("..", "..", "Data", "flow_loop", "cleaned", file_name)
    df.to_csv(new_path)
    i += 1

