import argparse
import inspect
from itertools import chain
import json

from config import DATASETS, ML, COMM, FL, UTILS

new_args = set(
    chain.from_iterable(
        inspect.signature(fn).parameters.keys() 
        for fn in chain(
            DATASETS.values(), 
            ML.values(), 
            COMM.values(), 
            FL.values(),
            UTILS.values()
        )
    )
)
new_args -= set(['args', 'kwargs', 'file', 'dataset', 'ml', 'comm', 'fl'])

parser = argparse.ArgumentParser()
parser.add_argument("--file", type=str, required=False, help="Config file")
parser.add_argument("-d", "--dataset", type=str, required=True, help="Dataset name")
parser.add_argument("--ml", type=str, required=True, help="ML framework")
parser.add_argument("-c", "--comm", type=str, required=True, help="Communication framework")
parser.add_argument("--fl", type=int, required=True, help="FL framework")
for arg in new_args:
    parser.add_argument(f"--{arg}", type=str, required=False, help=f"{arg}")
args = parser.parse_args()

args = vars(args)
if args['file'] is not None:
    with open(args['file'], 'r') as f:
        file_args = json.load(f)
        args.update(file_args)
# args = {k: v for k, v in args.items() if v is not None}

dataset = DATASETS[args.pop('dataset')]()
ml = ML[args.pop('ml')](dataset = dataset, **args)
comm = COMM[args.pop('comm')]()
fl = FL[args.pop('fl')](ml = ml, comm = comm, **args)

print(f"\nDataset {dataset.__class__.__name__}:\n{dataset}")
print(f"\nML {ml.__class__.__name__}:\n{ml}")
print(f"\nComm: {comm.__class__.__name__}")
print(f"\nFL {fl.__class__.__name__}:\n{fl}")