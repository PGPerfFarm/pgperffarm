import os
from settings_local import BASE_PATH
from pathlib import Path

# where to store the output of the tpch procedure
OUTPUT_PATH = os.path.join(BASE_PATH, 'tpc-h')

if not os.path.exists(OUTPUT_PATH):
    os.makedirs(OUTPUT_PATH)

# current project root
PROJECT_PATH = os.path.join(Path().parent.resolve(), 'tpc-h')

# path of the tpch tool
TPC_TOOL_PATH = os.path.join(PROJECT_PATH, 'TPC-H_Tools')

# path of the dbgen tool
DBGEN_PATH = os.path.join(TPC_TOOL_PATH, 'dbgen')

# folder to store the data which to be loaded to database
data_dir = os.path.join(OUTPUT_PATH, 'data')

# tables in tpch benchmark models
TABLES = ['LINEITEM', 'PARTSUPP', 'ORDERS', 'CUSTOMER', 'SUPPLIER', 'NATION', 'REGION', 'PART']

query_root = '/home/yedil/Documents/pgperffarm/pgtpch/queries'

UPDATE_DIR = os.path.join(OUTPUT_PATH, 'update')
DELETE_DIR = os.path.join(OUTPUT_PATH, 'delete')

GENERATED_QUERY_DIR = os.path.join(query_root, 'generated_queries')