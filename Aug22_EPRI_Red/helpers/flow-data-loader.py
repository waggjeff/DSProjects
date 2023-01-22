import pandas as pd
import os

def read_flow_loop_data(data_path,file):
    data_list=pd.read_excel(os.path.join(data_path,file),sheet_name='Variable  List')
    data_timeseries=pd.read_excel(os.path.join(data_path,file),sheet_name='Variable Data')
    #extract units from the first sheet. "adim" stands for adimensional
    units={}
    for index, row in data_list.iterrows():
        if str(row["Unit"])=="nan":
            units[row["Name"]]="adim"
        else:
            units[row["Name"]]=row["Unit"]
    #construct new column names
    column_names=[name for name in data_timeseries.loc[[3]].values]
    for i in range(1,len(column_names[0])):
        if pd.isnull(column_names[0][i]):
            column_names[0][i]='time_'+column_names[0][i+1]
        else:
            column_names[0][i]=column_names[0][i]+"("+units[column_names[0][i]]+")"
    #construct new dataframe from timeseries
    data_timeseries.columns=column_names
    data_timeseries=data_timeseries.drop(
                                        data_timeseries.columns[0],axis=1
                                        ).drop([0,1,2,3,4,5,6]).reset_index(drop=True)
    return data_timeseries

if __name__=='__main__':
    data_path=input("Input the path where the data is stored: ")
    file=input("Input file name: ")
    data=read_flow_loop_data(data_path,file)
    #produce name for csv file
    if file.endswith('.xlsx'):
        csv_file = file[:-4]+csv
    data.to_csv(csv_file)    
