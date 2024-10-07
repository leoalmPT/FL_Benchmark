from tensorflow.keras.datasets import cifar10
import numpy as np

from Utils.DatasetUtils import DatasetUtils

class CIFAR10(DatasetUtils):

    def download(self):
        return


    def preprocess(self, val_size, test_size):
        (x_train, y_train), (x_test, y_test) = cifar10.load_data()
        x = np.concatenate((x_train, x_test))
        y = np.concatenate((y_train, y_test))
        x = x.astype('float32')
        x = x / 255.0
        self.metadata['classes'] = len(np.unique(y))
        self.split_save(x, y, val_size, test_size)