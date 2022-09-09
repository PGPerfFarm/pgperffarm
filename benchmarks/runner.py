import os
import json
from time import gmtime, strftime
from subprocess import check_output
import simplejson as json
import folders
from pgtpch import tpch_runner
from utils.logging import log
from settings_local import *
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class BenchmarkRunner(object):
    'manages iterations of all the benchmarks, including cluster restarts etc.'

    def __init__(self, out_dir, cluster, collector):

        self._output = out_dir  # where to store output files
        self._benchmarks = {}  # bench name => class implementing the benchmark
        self._configs = []  # config name => (bench name, config)
        self._cluster = cluster
        self._collector = collector

    def register_benchmark(self, benchmark_name, benchmark_class):

        self._benchmarks.update({benchmark_name: benchmark_class})

    def register_config(self, config_name, benchmark_name, branch, commit,
                        postgres_config, **kwargs):

        self._configs.append({config_name: {'benchmark': benchmark_name, 'config': kwargs, 'branch': branch, 'commit': commit, 'postgres': postgres_config}})

    def _check_config(self, config_name):

        if not isinstance(self._configs, list):
            raise Exception("Configurations in settings_local.py must be a list.")

        issues = []

        # construct the benchmark class for the given config name
        for c in self._configs:
            config = c[config_name]
            bench = self._benchmarks[config['benchmark']]

            # expand the attribute names
            bench = bench(**config['config'])

            # run the tests
            issue = bench.check_config()
            if issue != []:
                issues.append(issue)

        return issues

    def check(self):
        'check configurations for all benchmarks'

        log("Checking benchmark configuration...")

        issues = {}

        for config in self._configs:
            for config_name in config:
                if config_name == 'pgbench-basic':
                    t = self._check_config(config_name)
                    if t:
                        issues.update({config_name: t})

        return issues

    def _run_config(self, config_name, mode):

        log("Running benchmark configuration")

        r = {}
        r['pgbench'] = []
        if mode == 'pgbench':
            self._cluster.start(config=self._configs[0]['pgbench-basic']['postgres'])
            dbname=self._configs[0]['pgbench-basic']['config']['dbname']
            socket_path = self._configs[0]['pgbench-basic']['postgres']['unix_socket_directories']
        elif mode == 'tpch':
            self._cluster.start(config=self._configs[0]['tpch']['postgres'])
            dbname = self._configs[0]['tpch']['config']['dbname']
            socket_path = self._configs[0]['tpch']['postgres']['unix_socket_directories']

        try:
            connection = psycopg2.connect("host='%s'  dbname='%s'" % (socket_path, 'postgres'))
            connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT);
            with connection.cursor() as cursor:
                cursor.execute("CREATE DATABASE %s" % dbname)
        finally:
            if connection:
                connection.close()

        # start collector(s) of additional info
        self._collector.start()

        # construct the benchmark class for the given config name
        for c in self._configs:
            config = c[config_name]
            if mode == 'pgbench':
                bench = self._benchmarks[config['benchmark']]

                # expand the attribute names
                bench = bench(**config['config'])

                # run the tests
                r['pgbench'].append(bench.run_tests())
            elif mode == 'tpch':
                tpch_runner.run_tpch(folders.SOCKET_PATH, self._configs[0]['tpch']['config']['dbname'], config['config']['results_dir'], TPCH_SCALE)

        # stop collectors
        self._collector.stop()

        # merge data from the collectors into the JSON document with results
        r.update(self._collector.result())

        r['meta'] = {
            'benchmark': config['benchmark'],
            'date': strftime("%Y-%m-%d %H:%M:%S.000000+00", gmtime()),
            'name': config_name,
        }

        r['git'] = {
            'branch': config['branch'],
            'commit': config['commit'],
            'remote': GIT_URL
        }

        r['kernel'] = {
            'uname_s': check_output(['uname', '-s']).rstrip(),
            'uname_r': check_output(['uname', '-r']).rstrip(),
            'uname_m': check_output(['uname', '-m']).rstrip(),
            'uname_v': check_output(['uname', '-v']).rstrip(),
        }

        uname = os.popen("uname").readlines()[0].split()[0]

        try:
            if uname == 'Linux':
                r['os_information'] = {
                    'distributor': check_output(['lsb_release', '-i']).rstrip().decode().split('\t')[1],
                    'description': check_output(['lsb_release', '-d']).rstrip().decode().split('\t')[1],
                    'release': check_output(['lsb_release', '-r']).rstrip().decode().split('\t')[1],
                    'codename': check_output(['lsb_release', '-c']).rstrip().decode().split('\t')[1]
                }

        except Exception as e:
            log("Error calling lsb_release, please install it.")
            sys.exit()

        try:
            if uname == 'Darwin':
                r['os_information'] = {
                    'distributor': check_output(['sw_vers', '-productName']).rstrip(),
                    'description': 'not available',
                    'release': check_output(['sw_vers', '-productVersion']).rstrip(),
                    'codename': check_output(['sw_vers', '-buildVersion']).rstrip()
                }

        except Exception as e:
            log("Error calling os_information, please install it.")
            sys.exit()

        with open('%s/%s' % (self._output, 'results.json'), 'w+') as f:
            f.write(json.dumps(r, indent=4))

    def run(self, mode):
        'run all the configured benchmarks'

        try:
            os.mkdir(self._output)
        except OSError as e:
            log("Output directory already exists: %s" % self._output)

        for config_name in self._configs[0]:
            self._run_config(config_name, mode)
