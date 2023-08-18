import multiprocessing
import os
import sys
from pathlib import Path

PGBENCH_CUSTOM_CONFIG = [
    {
         'iterations': 1,
        'duration':10,
        'scale': 5,
       'clients': [1],
       'read_only': False,
    }
   
    ]

init_path = os.path.join(Path(__file__).resolve().parent, 'init.sql')
custom_queries_path=os.path.join(Path(__file__).resolve().parent,'scripts')

