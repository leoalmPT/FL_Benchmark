import kaggle
import pandas as pd
from sklearn.preprocessing import StandardScaler

from my_builtins.DatasetABC import DatasetABC


class IOT_DNL(DatasetABC):

    @property
    def is_classification(self) -> bool:
        return True
    

    @property
    def output_size(self) -> int:
        return 6
    

    @property
    def scaler(self):
        return StandardScaler


    def download(self):
        kaggle.api.dataset_download_files(
            "speedwall10/iot-device-network-logs",
            path=f"{self.data_path}",
            quiet=False,
            unzip=True
        )

    
    def preprocess(self, val_size, test_size):
        data = pd.read_csv(f"{self.data_path}/Preprocessed_data.csv")
        data.dropna()
        x = data.drop('normality', axis=1)
        x = x.drop('frame.number', axis=1)
        x = x.drop('frame.time', axis=1)
        y = data['normality']
        self.save_features(x.columns)
        self.split_save(x, y, val_size, test_size)