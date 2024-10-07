import pandas as pd
from sklearn.preprocessing import LabelEncoder
import os
import numpy as np

from Utils.DatasetUtils import DatasetUtils

class Slicing5G(DatasetUtils):
    
    def download(self):
        self.download_file(
            os.getenv('SLICING5G_URL'),
        )


    def preprocess(self, val_size, test_size):
        dataset = f"Data/{self.name}/5G_Dataset_Network_Slicing_CRAWDAD_Shared/5G_Dataset_Network_Slicing_CRAWDAD_Shared.xlsx"
        df = pd.read_excel(dataset, sheet_name="Model_Inputs_Outputs")
        le = LabelEncoder()
        del df["Unnamed: 0"]
        #Transform features into categories
        df["Use CaseType (Input 1)"] = le.fit_transform(df["Use CaseType (Input 1)"])
        df["LTE/5G UE Category (Input 2)"] = df["LTE/5G UE Category (Input 2)"].astype(str)
        df["LTE/5G UE Category (Input 2)"] = le.fit_transform(df["LTE/5G UE Category (Input 2)"])
        df["Technology Supported (Input 3)"] = le.fit_transform(df["Technology Supported (Input 3)"])
        df["Day (Input4)"] = le.fit_transform(df["Day (Input4)"])
        df["QCI (Input 6)"] = le.fit_transform(df["QCI (Input 6)"])
        df["Packet Loss Rate (Reliability)"] = le.fit_transform(df["Packet Loss Rate (Reliability)"])
        df["Packet Delay Budget (Latency)"] = le.fit_transform(df["Packet Delay Budget (Latency)"])
        df["Slice Type (Output)"] = le.fit_transform(df["Slice Type (Output)"])
        x = df.drop('Slice Type (Output)', axis=1)
        y = df['Slice Type (Output)']
        self.metadata['classes'] = len(np.unique(y))
        self.save_features(x.columns)
        self.split_save(x.to_numpy(), y.to_numpy(), val_size, test_size)