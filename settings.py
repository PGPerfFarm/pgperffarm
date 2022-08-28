import sys
import multiprocessing

# global configuration
UPDATE = True
AUTOMATIC_UPLOAD = False
BASIC_AUTH = False
# username and password for the basic authentication
USERNAME = 'username'
PASSWORD = 'password'

# default url: master branch
GIT_URL = 'https://github.com/postgres/postgres.git'

# base path where to clone, install and fetch results
# parent must exist!
# also should have non-superuser access
BASE_PATH = '/tmp/perffarm'

API_URL = 'http://140.211.168.111/'
MACHINE_SECRET = 'changeme'

# scale factor for tpc-h benchmark
TPCH_SCALE = 1

# mode for running the client
MODE = [
    'pgbench',
    # 'tpch'
]

POSTGRES_CONFIG = {
    'shared_buffers': '1GB',
    'work_mem': '64MB',
    'maintenance_work_mem': '128MB',
    'min_wal_size': '2GB',
    'max_wal_size': '4GB',
    'log_line_prefix': '%t [%p]: [%l-1] db=%d,user=%u,app=%a,client=%h ',
    'log_checkpoints': 'on',
    'log_autovacuum_min_duration': '0',
    'log_temp_files': '32',
    'checkpoint_timeout': '30min',
    'checkpoint_completion_target': '0.9',
}

DATABASE_NAME = 'postgres'

# configuration for PgBench
# iterations - number of repetitions (including test for all client counts)
# duration - duration (in seconds) of a single benchmark (per client count)
PGBENCH_CONFIG = [
    {
        'iterations': 2,
        'duration': 600,
        'scale': 3,
        'clients': [1, multiprocessing.cpu_count(), 2 * multiprocessing.cpu_count()],
        'read_only': False,
    },
    {
        'iterations': 2,
        'duration': 600,
        'scale': 5,
        'clients': [1, multiprocessing.cpu_count(), 2 * multiprocessing.cpu_count()],
        'read_only': False,
    }]

# ignore missing file with local config
try:
    from settings_local import *
except Exception as e:
    print(sys.stderr, "ERROR: local configuration (settings_local.py) " \
                      "not found")
    sys.exit(1)
