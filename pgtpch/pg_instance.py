import psycopg2
import json
from utils.logging import log

# class for connections to postgres


class PGDB:
    __connection__ = None
    __cursor__ = None

    def __init__(self, host, db_name):
        self.__connection__ = psycopg2.connect(
            "host='%s'  dbname='%s'" % (host, db_name))
        self.__cursor__ = self.__connection__.cursor()

    def close(self):
        if self.__cursor__ is not None:
            self.__cursor__.close()
            self.__cursor__ = None
        if self.__connection__ is not None:
            self.__connection__.close()
            self.__connection__ = None

    def executeQueryFromFile(self, filepath, function=None):
        if function is None:
            def function(x): return x
        with open(filepath) as query_file:
            query = query_file.read()
            query = function(query)
            return self.executeQuery(query)

    def executeQuery(self, query):
        if self.__cursor__ is not None:
            self.__cursor__.execute(query)
            return 0
        else:
            print("database has been closed")
            return 1

    def explainQuery(self, query):
        if self.__cursor__ is not None:
            self.__cursor__.execute(query)
            result = self.__cursor__.fetchall()
            # result=json.dumps(result)

            return result
        else:
            print("database has been closed")
            return 0

    def copyFrom(self, filepath, separator, table):
        if self.__cursor__ is not None:
            with open(filepath, 'r') as in_file:
                self.__cursor__.copy_from(in_file, table=table, sep=separator)
            return 0
        else:
            print("database has been closed")
            return 1

    def commit(self):
        if self.__connection__ is not None:
            self.__connection__.commit()
            return 0
        else:
            print("cursor not initialized")
            return 1
