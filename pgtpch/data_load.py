import os
import pgtpch.pg_instance as pgdb
from utils.logging import log


def clean_database(host, db_name, tables):
    """Drops the tables if they exist

    Args:
        host (str): IP/hostname of the PG instance
        db_name (str): name of the tpch database
        tables (str): list of tables

    Return:
        0 if successful
        non-zero otherwise
    """
    try:
        conn = pgdb.PGDB(host, db_name)
        try:
            for table in tables:
                conn.executeQuery("DROP TABLE IF EXISTS %s " % table)
        except Exception as e:
            log("unable to remove existing tables. %s" % e)
            return 1
        log("dropped existing tables")
        conn.commit()
        conn.close()
        return 0
    except Exception as e:
        log("unable to connect to the database. %s" % e)
        return 1


def create_schema(query_root, host, db_name):
    """Creates the schema for the tests. Drops the tables if they exist

    Args:
        query_root (str): Directory in which generated queries directory exists
        host (str): IP/hostname of the PG instance
        db_name (str): name of the tpch database

    Return:
        0 if successful
        non-zero otherwise
    """
    try:
        conn = pgdb.PGDB(host, db_name)
        try:
            conn.executeQueryFromFile(os.path.join(query_root, "create_tbl.sql"))
        except Exception as e:
            log("unable to run create tables. %s" % e)
            return 1
        conn.commit()
        conn.close()
    except Exception as e:
        log("unable to connect to the database. %s" % e)
        return 1


def load_tables(host, db_name, tables, load_dir):
    """Loads data into tables. Expects that tables are already empty.

    Args:
        host (str): IP/hostname of the PG instance
        db_name (str): name of the tpch database
        tables (str): list of tables
        load_dir (str): directory with data files to be loaded

    Return:
        0 if successful
        non-zero otherwise
    """
    try:
        conn = pgdb.PGDB(host, db_name)
        try:
            for table in tables:
                filepath = os.path.join(load_dir, table.lower() + ".tbl")
                conn.copyFrom(filepath, separator="|", table=table)
            conn.commit()
        except Exception as e:
            log("unable to run load tables. %s" % e)
            return 1
        conn.close()
        return 0
    except Exception as e:
        log("unable to connect to the database. %s" % e)
        return 1


def index_tables(query_root, host, db_name):
    """Creates indexes and foreign keys for loaded tables.

    Args:
        query_root (str): Directory in which preparation queries directory exists
        host (str): IP/hostname of the PG instance
        db_name (str): name of the tpch database

    Return:
        0 if successful
        non-zero otherwise
    """
    try:
        conn = pgdb.PGDB(host, db_name)
        try:
            conn.executeQueryFromFile(os.path.join(query_root, "create_idx.sql"))
            conn.commit()
        except Exception as e:
            log("unable to run index tables. %s" % e)
            return 1
        conn.close()
        return 0
    except Exception as e:
        log("unable to connect to the database. %s" % e)
        return 1
