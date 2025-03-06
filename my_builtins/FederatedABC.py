from abc import ABC, abstractmethod
from permetrics import RegressionMetric, ClassificationMetric
from collections import deque
import json
from pathlib import Path
from time import time
import numpy as np
from typing import Any
import random

from my_builtins.WorkerManager import WorkerManager
from my_builtins.MLFrameworkABC import MLFrameworkABC

RESULTS_FOLDER = "results"

METRICS = {
    'classification': [
        'MCC',
        'AS',
        'F1S'
    ],
    'regression': [
        'SMAPE',
        'MSE',
        'MAE'
    ]
}

class FederatedABC(ABC):

    def __init__(self, *,
        ml: MLFrameworkABC,
        wm: WorkerManager,
        all_args: dict,
        epochs: int = 10,
        target_score: float = None,
        patience: int = 5,
        delta: float = 0.01,
        main_metric: str = None,
        min_workers: int = 2,
        **kwargs
    ) -> None:
        self.ml = ml
        self.wm = wm
        self.all_args = all_args
        self.epochs = epochs
        self.target_score = target_score
        self.patience = patience
        self.delta = delta
        self.main_metric = main_metric
        self.min_workers = min_workers
        
        self.buffer = deque(maxlen=patience)
        self.compare_score = None
        self.best_score = None
        self.best_weights = None
        self.last_time = 0
        self.is_classification = None
        self.metrics = None
        self.evaluator = None
        self.new_score = None
        self.is_master = None

        self.setup_metrics()
        self.setup_nodes()


    @abstractmethod
    def setup(self):
        pass


    @abstractmethod
    def get_worker_info(self) -> dict:
        pass


    @abstractmethod
    def master_loop(self):
        pass


    def setup_metrics(self):
        self.is_classification = self.ml.dataset.is_classification

        if self.main_metric is None:
            self.main_metric = METRICS['classification'][0] if self.is_classification else METRICS['regression'][0]
        if self.target_score is None:
            self.target_score = 1.0 if self.is_classification else 0.0
        
        all_metrics, self.evaluator = (
            (METRICS['classification'], ClassificationMetric) 
            if self.is_classification else
            (METRICS['regression'], RegressionMetric)
        )
        assert self.main_metric in all_metrics, f"main_metric must be one of {all_metrics}"
        all_metrics.remove(self.main_metric)
        self.metrics = [self.main_metric] + all_metrics

    
    def setup_nodes(self):
        self.is_master = self.wm.c.id == 0
        self.id = self.wm.c.id
        self.base_path = f"{RESULTS_FOLDER}/{self.wm.c.start_time.strftime('%Y-%m-%d_%H:%M:%S')}"
        Path(self.base_path).mkdir(parents=True, exist_ok=True)
        with open(f"{self.base_path}/args.json", "w") as f:
            json.dump(self.all_args, f, indent=4)


    def run(self):
        self.setup()
        if not self.is_master:
            self.wm.setup_worker_info(self.get_worker_info())
        self.last_time = time()
        if self.is_master:
            self.master_loop()
        else:
            self.wm.recv(WorkerManager.EXIT_TYPE)
        self.end()
                

    def end(self):
        if self.is_master and self.best_weights is not None:
            self.ml.set_weights(self.best_weights)
            self.ml.save_model(f"{self.base_path}/model")
        self.wm.c.close()


    def force_end(self):
        self.wm.send_n(
            workers = self.wm.get_all_workers(), 
            type_ = WorkerManager.EXIT_TYPE
        )
        self.end()


    def validate(self, epoch: int, x, y) -> float:
        preds = self.ml.predict(x)
        if self.is_classification:
            preds = np.argmax(preds, axis=1)
        metrics = self.evaluator(y, preds).get_metrics_by_list_names(self.metrics)
        new_time = time()
        delta_time = new_time - self.last_time
        print(f"Epoch {epoch}/{self.epochs} - Time: {delta_time:.2f}s")
        self.last_time = new_time
        print(', '.join(f'{name}: {value:.4f}' for name, value in metrics.items()))
        self.new_score = metrics[self.metrics[0]]
        if (
            self.best_score is None or
            (self.is_classification and self.new_score > self.best_score) or
            (not self.is_classification and self.new_score < self.best_score)
        ):
            self.best_score = self.new_score
            self.best_weights = self.ml.get_weights()
        return metrics
    

    def early_stop(self) -> bool:
        if (
            (self.is_classification and self.new_score >= self.target_score) or
            (not self.is_classification and self.new_score <= self.target_score)
        ):
            return True

        if len(self.buffer) < self.patience:
            self.buffer.append(self.new_score)
            return False
        
        old_score = self.buffer.popleft()
        if (
            self.compare_score is None or
            (self.is_classification and old_score > self.compare_score) or
            (not self.is_classification and old_score < self.compare_score)
        ):
            self.compare_score = old_score
        
        self.buffer.append(self.new_score)
        if self.is_classification:
            return not any(score >= self.compare_score + self.delta for score in self.buffer)
        else:
            return not any(score <= self.compare_score - self.delta for score in self.buffer)
        

    def random_pool(self, size: int, workers_info: dict) -> list[int]:
        workers = list(workers_info.keys())
        return random.sample(workers, size)
    

    def random_worker(self, workers_info: dict, responses: dict) -> int:
        workers = set(workers_info.keys()) - set(responses.keys())
        return random.choice(list(workers)) if workers else None