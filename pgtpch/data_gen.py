import os
import glob
import re
import subprocess
from utils.logging import log
from pgtpch.tpc_folder import *


def remove_final_delimiter(in_dir, out_dir, file_pattern):
    try:
        os.makedirs(out_dir, exist_ok=True)
        for in_fname in glob.glob(os.path.join(in_dir, file_pattern)):
            fname = os.path.basename(in_fname)
            out_fname = os.path.join(out_dir, fname)
            try:
                with open(in_fname) as in_file, open(out_fname, "w") as out_file:
                    for inline in in_file:
                        outline = re.sub("\|$", "", inline)
                        out_file.write(outline)
                os.remove(in_fname)
            except IOError as e:
                log("exception happened while transforming data files. (%s)" % e)
                return 1
    except IOError as e:
        log("unable to create directory %s. (%s)" % (out_dir, e))
        return 1
    return 0


def make_dbgen():
    p = subprocess.Popen(
        ["make", "-f", os.path.join(DBGEN_PATH, "makefile.suite")], cwd=DBGEN_PATH)
    p.communicate()
    return p.returncode


def clean_data(scale, num_streams):
    p = subprocess.Popen(
        [os.path.join(".", "dbgen"), "-vf", "-s", str(scale)], cwd=DBGEN_PATH)
    p.communicate()
    if not p.returncode:
        out_dir = os.path.join(OUTPUT_PATH, 'data')
        if remove_final_delimiter(DBGEN_PATH, out_dir, '*.tbl'):
            log("unable to generate data for load phase")
            return 1
        log("generated data for the load phase")
    else:
        return p.returncode

    # Update/Delete phase data
    # we generate num_streams + 1 number of updates because 1 is used by the power tests
    p = subprocess.Popen([os.path.join(".", "dbgen"), "-vf", "-s", str(scale), "-U", str(num_streams + 1)],
                         cwd=DBGEN_PATH)
    p.communicate()
    if not p.returncode:
        update_out_path = os.path.join(OUTPUT_PATH, 'update')
        delete_out_path = os.path.join(OUTPUT_PATH, 'delete')
        if remove_final_delimiter(DBGEN_PATH, update_out_path, "*.tbl.u*"):
            log("unable to generate data for the update phase")
            return 1
        log("generated data for the update phase")
        if remove_final_delimiter(DBGEN_PATH, delete_out_path, "delete.*"):
            log("unable to generate data for the delete phase")
            return 1
        log("generated data for the delete phase")
        # All files written successfully. Return success code.
        return 0
    else:
        return p.returncode


def generate_queries(dbgen_dir, query_root):
    """Generates queries for performance tests.

    Args:
        dbgen_dir (str): Directory in which the source code is placed.
        query_root (str): Directory in which query templates directory exists.
                          Also, the place where the generated queries are going to be placed.

    Return:
        0 if successful
        non-zero otherwise
    """
    query_root = os.path.abspath(query_root)
    dss_query_path = os.path.join(query_root, 'query_template')
    query_env = os.environ.copy()
    query_env['DSS_QUERY'] = dss_query_path
    os.makedirs(GENERATED_QUERY_DIR, exist_ok=True)
    for i in range(1, 23):
        try:
            with open(os.path.join(GENERATED_QUERY_DIR, str(i) + ".sql"), "w") as out_file:
                p = subprocess.Popen([os.path.join(".", "qgen"), str(i)],
                                     cwd=dbgen_dir, env=query_env, stdout=out_file)
                p.communicate()
                if p.returncode:
                    log("Process returned non zero when generating query number %s" % i)
                    return p.returncode
        except IOError as e:
            log("IO Error during query generation %s" % e)
            return 1
    return p.returncode
