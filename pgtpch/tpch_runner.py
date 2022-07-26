#!/usr/bin/env python3
import os
import time
from utils.logging import log
from settings_local import *
import pgtpch.data_load as load
import pgtpch.data_gen as pre
import pgtpch.perf_test as query
import pgtpch.tpch_res as r
from pgtpch.tpc_folder import *

def scale_to_num_streams(scale):
    """Converts scale factor to number of streams
    :param scale: scale factor
    :return: number of streams
    """
    num_streams = 2
    if scale <= 1:
        num_streams = 2
    elif scale <= 10:
        num_streams = 3
    elif scale <= 30:
        num_streams = 4
    elif scale <= 100:
        num_streams = 5
    elif scale <= 300:
        num_streams = 6
    elif scale <= 1000:
        num_streams = 7
    elif scale <= 3000:
        num_streams = 8
    elif scale <= 10000:
        num_streams = 9
    elif scale <= 30000:
        num_streams = 10
    else:
        num_streams = 11
    return num_streams


def run_tpch(host, db_name, results_dir,  scale=1):

    try:
        os.makedirs(BASE_PATH, exist_ok=True)
    except IOError as e:
        log("unable to create directory %s. (%s)" % (BASE_PATH, e))

    num_streams = scale_to_num_streams(scale)
    run_timestamp = "run_%s" % time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    # preprocessing
    if pre.make_dbgen():
        log("could not build the dbgen/querygen. Check logs.")
        exit(1)
    log("built dbgen from source")

    if pre.clean_data(scale, num_streams):
        log("could not generate data files.")
        exit(1)
    log("created data files in %s" % data_dir)

    if pre.generate_queries(DBGEN_PATH, query_root):
        log("could not generate query files")
        exit(1)
    log("created query files in %s" % query_root)
