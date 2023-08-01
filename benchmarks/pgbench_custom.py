import os.path
import re
import time
import psycopg2
import psycopg2.extras

import folders
from collectors.collectd import CollectdCollector
from collectors.pg_stat_statements import PgStatStatementsCollector
from utils.logging import log
from utils.misc import run_cmd
from settings_local import *
from pathlib import Path
import glob

#change the path according to your need
from benchmarks.custom_queries.mybenchmark.parameters import *

class PgBench(object):
    'a simple wrapper around pgbench, running TPC-B-like workload by default'

    # TODO allow running custom scripts, not just the default
    #      read-write/read-only tests
    # TODO allow running 'prepared' mode

    def __init__(self, bin_path, dbname, scale, clients, iterations, duration, read_only, results_dir=None):
        '''
        bin_path   - path to PostgreSQL binaries (dropdb, createdb, psql
                     commands)
        dbname     - name of the database to use
        duration   - duration of each execution
        iterations       - number of iterations (for each client count)
        out_dir    - output directory
        '''

        self._bin = bin_path
        self._dbname = dbname
        self._duration = duration
        self._outdir = results_dir
        self._iterations = iterations
        self._scale = scale
        self._clients = clients
        self._read_only = read_only

        self._env = os.environ
        self._env['PATH'] = ':'.join([bin_path, self._env['PATH']])


    def _init(self, scale):
        """
        recreate the database (drop + create) and populate it with given scale
        """

        # initialize results for this dataset scale
        
        log("recreating '%s' database" % (self._dbname,))
        run_cmd(['dropdb', '-h', folders.SOCKET_PATH, '--if-exists', self._dbname], env=self._env)
        run_cmd(['createdb', '-h', folders.SOCKET_PATH, self._dbname], env=self._env)
    

        log("initializing pgbench '%s' with scale %s" % (self._dbname, scale))

        # path of init.py file , to initialize the database
        # change the path according to your need
        # init_path , imported from parameters.py

        r = run_cmd(['psql','-f',init_path, '-h', folders.SOCKET_PATH, '-p', '5432', self._dbname], env=self._env, cwd=self._outdir)
        #psql cammand to initialize the database
       
        with open(folders.LOG_PATH + '/pgbench_custom_log.txt', 'w+') as file:
            file.write("pgbench_custom log: \n")
            file.write(r[1].decode("utf-8"))
            file.write("\n")
        self._pgbench_init = r[2]
        

    @staticmethod
    def _parse_results(data):
        'extract results (including parameters) from the pgbench output'

        with open(folders.LOG_PATH + '/compiler.txt', 'r') as file:
            line = file.readline()
            r = re.search('PostgreSQL ([0-9\.]+)', line)
            postgres_version = float(r.group(1))

        data = data.decode('utf-8')

        with open(folders.LOG_PATH + '/pgbench_custom_log.txt', 'a+') as file:
            file.write(data)

        mode = -1
        r = re.search('query mode: (.+)', data)
        if r:
            mode = r.group(1)

        clients = -1
        r = re.search('number of clients: ([0-9]+)', data)
        if r:
            clients = r.group(1)

        threads = -1
        r = re.search('number of threads: ([0-9]+)', data)
        if r:
            threads = r.group(1)

        duration = -1
        r = re.search('duration: ([0-9]+) s', data)
        if r:
            duration = r.group(1)

        latency = -1
        r = re.search('latency average = ([0-9\.]+) ms', data)
        if r:
            latency = r.group(1)

        tps = -1
        if postgres_version >= 14:
            r = re.search('tps = ([0-9]+\.[0-9]+) \(without initial connection time\)', data)
        else:
            r = re.search('tps = ([0-9]+\.[0-9]+) \(excluding connections establishing\)', data)
        if r:
            tps = r.group(1)

        statement_latencies = -1
        r = re.search('statement latencies in milliseconds:([\s\S]+)', data)

        if r:
            statement_latencies = r.group(1)

        return {'mode': mode,
                'clients': clients,
                'threads': threads,
                'latency': latency,
                'statement_latencies' : statement_latencies,
                'tps': tps}

    def check_config(self):
        'check pgbench configuration (existence of binaries etc.)'

        issues = []

        if not os.path.isdir(self._bin):
            issues.append("bin_dir='%s' does not exist" % (self._bin,))
        elif not os.path.exists('%s/pgbench' % (self._bin,)):
            issues.append("pgbench not found in bin_dir='%s'" % (self._bin,))
        elif not os.path.exists('%s/createdb' % (self._bin,)):
            issues.append("createdb not found in bin_dir='%s'" % (self._bin,))
        elif not os.path.exists('%s/dropdb' % (self._bin,)):
            issues.append("dropdb not found in bin_dir='%s'" % (self._bin,))
        elif not os.path.exists('%s/psql' % (self._bin,)):
            issues.append("psql not found in bin_dir='%s'" % (self._bin,))

        if type(self._duration) is not int:
            issues.append("duration (%s) needs to be an integer" % self._duration)
        elif not self._duration >= 1:
            issues.append("duration (%s) needs to be >= 1" % (self._duration,))

        if type(self._iterations) is not int:
            issues.append("iterations (%s) needs to be an integer" % self._duration)
        elif not self._iterations >= 1:
            issues.append("iterations (%s) needs to be >= 1" % (self._iterations,))

        if type(self._clients) is not list:
            issues.append("clients (%s) needs to be an array" % self._clients)
        else:
            for client in self._clients:
                if not client >= 1:
                    issues.append("client (%s) needs to be >= 1" % (client))

        return issues




    def _run_custom(self, run, scale, duration, pgbench_init, read_only, nclients=1, njobs=1, aggregate=True, custom_query_folder=None):
        'run pgbench on the database (either a warmup or actual benchmark run)'

        custom_query_files = glob.glob(custom_query_folder + '/*.sql')

        # add -r here
        args = ['pgbench', '-r', '-h', folders.SOCKET_PATH, '-c', str(nclients), '-j', str(njobs), '-T',
                str(duration)]

        if read_only:
            rtag = "ro"
        else:
            rtag = "rw"

        prefix = "pgbench-%s-%d-%d-%d-%s-" % (rtag, scale, duration, nclients, str(run))

        # aggregate on per second resolution
        if aggregate:
            args.extend(['-l', '--aggregate-interval', '1', '--log-prefix', prefix])

        if read_only:
            args.extend(['-S'])

        args.extend([self._dbname])

        for query_file in custom_query_files:
            match = re.findall('[0-9]+', query_file)
            dot_cnt=re.findall('[.]',query_file)
            if len(dot_cnt)>1 and  match:

                weight = match[-1]
                log(weight)
                query_file+='@'+str(weight)
                args.extend(['-f', query_file])
            else:
                args.extend(['-f', query_file])  # Add the custom query file path

        # do an explicit checkpoint before each run
        run_cmd(['psql', '-h', folders.SOCKET_PATH, self._dbname, '-c', 'checkpoint'], env=self._env)
        log("pgbench: clients=%d, jobs=%d, aggregate=%s, read-only=%s, duration=%d" % (nclients, njobs, aggregate, read_only, duration))
            
        start = time.time()
        r = run_cmd(args, env=self._env, cwd=folders.LOG_PATH)
        end = time.time()
        r = PgBench._parse_results(r[1])
        r.update({'init': pgbench_init})
        r.update({'start': start, 'end': end})
        return r


    def collect_pg_stat_statements(self):
        conn = psycopg2.connect('host=%s dbname=%s' % (folders.SOCKET_PATH, self._dbname))
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute(
            'CREATE EXTENSION pg_stat_statements;'
            'SELECT * FROM pg_stat_statements;'
        )

        result = cur.fetchall()

        conn.close()

        return result




    def run_custom_tests_pgbench(self):
       
        
        """
        execute the whole benchmark, including initialization, warmup and
        benchmark iterations
        """
        results = []
        result = {}
        tmp = {}

        j = 0
        info = {}

        info['clients'] = self._clients
        scale = self._scale

        # init for the dataset scale and warmup
        self._init(scale)

        if self._read_only:
            tag = "read-only"
        else:
            tag = "read-write"

        for i in range(0, self._iterations):
            log("pgbench: %s iteration=%d" % (tag, i))

            for clients in self._clients:
                if clients not in results:
                    result['clients'] = clients

                self._init(scale)

                # start collectd collector before run
                collectd_collector = CollectdCollector(folders.OUTPUT_PATH, DATABASE_NAME)
                collectd_collector.start()

                r = self._run_custom(i, scale, self._duration, self._pgbench_init, self._read_only, clients, clients, True,custom_queries_path)
                

                r.update({'collectd': collectd_collector.result()})
                collectd_collector.stop()

                # start pg_stat_statements collector after run
                pg_stat_statements_collector = PgStatStatementsCollector(DATABASE_NAME)
                pg_stat_statements_collector.start()
                r.update({'pg_stat_statements': pg_stat_statements_collector.result()})

                r.update({'iteration': i})

                results.append(r)


        info['scale'] = scale
        info['iterations'] = results
        info['duration'] = self._duration
        info['read_only'] = self._read_only
        with open(init_path) as f:
                init_lines = f.readlines()
        init_lines=''.join(init_lines)
        info['init_sql'] = init_lines
        custom_query_files = glob.glob(custom_queries_path + '/*.sql')
        tmp=[]
        for query_file in custom_query_files:
            match = re.findall('[0-9]+', query_file)
            dot_cnt=re.findall('[.]',query_file)
            if len(dot_cnt)>1 and  match:
                weight = match[-1]
                with open(query_file) as f:
                    query_lines = f.readlines()
                query_lines="weight-: " +str(weight).join(query_lines)
                tmp.append(query_lines)
            else:
                with open(query_file) as f:
                    query_lines = f.readlines()
                query_lines=''.join(query_lines)
                tmp.append(query_lines)
                

        info['custom_queries'] = tmp
        return info
        
                
