import csv
import json
import hashlib
import io
import re
from datetime import datetime

from postgres.models import PostgresSettingsSet, PostgresSettings
from benchmarks.models import PgBenchBenchmark, PgBenchResult, PgBenchStatement, PgBenchLog, PgBenchRunStatement, PgStatStatementsQuery, PgStatStatements, CollectdCpu, CollectdProcess, CollectdContextswitch, CollectdIpcShm, CollectdIpcMsg, CollectdIpcSem, CollectdMemory, CollectdSwap, CollectdVmem
from systems.models import HardwareInfo, Compiler, Kernel, OsDistributor, OsKernelVersion, OsVersion
from runs.models import GitRepo, Branch


def parse_sysctl(raw_data):

    data = json.loads(raw_data)
    json_dict = {}

    known_sysctl_linux = Kernel.objects.filter(kernel_id=1).get()

    for parameter in known_sysctl_linux.sysctl:

        if parameter in data:
            json_dict.update({parameter: data[parameter]})

    known_sysctl_mac = Kernel.objects.filter(kernel_id=2).get()

    for parameter in known_sysctl_mac.sysctl:

        if parameter in data:
            json_dict.update({parameter: data[parameter]})

    if json_dict == {}:
        return 'known sysctl info not found'

    else:
        return json_dict


def hash(json_data):

    hash_value = hashlib.sha256(json.dumps(json_data).encode('utf-8'))
    return hash_value.hexdigest()


def parse_linux_data(json_data):

    if ('brand' in json_data['system']['cpu']['information']):
        brand = json_data['system']['cpu']['information']['brand']

    else:
        brand = json_data['system']['cpu']['information']['brand_raw']

    if ('hz_actual_raw' in json_data['system']['cpu']['information']):
        hz = json_data['system']['cpu']['information']['hz_actual_raw'][0]

    else:
        hz = json_data['system']['cpu']['information']['hz_actual'][0]

    sysctl = parse_sysctl(json_data['sysctl_log'])

    result = {
        'cpu_brand': brand,
        'hz': hz,
        'cpu_cores': json_data['system']['cpu']['information']['count'],
        'total_memory': json_data['system']['memory']['virtual']['total'],
        'total_swap': json_data['system']['memory']['swap']['total'],
        'mounts_hash': hash(json_data['system']['memory']['mounts']),
        'mounts': json_data['system']['memory']['mounts'],
        'sysctl': sysctl,
        'sysctl_hash': hash(sysctl)
    }

    return result


def get_hash(postgres_settings):

    reader = csv.DictReader(io.StringIO(postgres_settings))
    postgres_settings_json = json.loads(json.dumps(list(reader)))

    hash_json = []

    for setting in postgres_settings_json:
        if setting['source'] != "default" and setting['source'] != "client":
            hash_json.append(setting)

    hash_string = hash(hash_json)

    return hash_string, hash_json


def add_postgres_settings(hash_value, settings):

    settings_set = PostgresSettingsSet.objects.filter(settings_sha256=hash_value).get()

    # now parsing all settings
    for row in settings:
        name = row['name']
        unit = row['source']
        value = row['setting']

        postgres_settings = PostgresSettings(db_settings_id=settings_set, setting_name=name, setting_unit=unit, setting_value=value)

        try:
            postgres_settings.save()

        except Exception as e:
            raise RuntimeError(e)


def parse_pgbench_options(item, clients):

    result = {
        'clients': clients,
        'scale': item['scale'],
        'duration': item['duration'],
        'read_only': item['read_only']
    }

    return result


def parse_pgbench_statement_latencies(statement_latencies, pgbench_result_id):

    # extract the nonempty statements
    statements = statement_latencies.split("\n")
    statements = list(filter(None, statements))

    line_id = 0

    for statement in statements:
        latency = re.findall('\d+\.\d+', statement)[0]
        text = (statement.split(latency)[1]).strip()

        try:
            pgbench_statement = PgBenchStatement.objects.filter(statement=text).get()

        except PgBenchStatement.DoesNotExist:

            pgbench_statement = PgBenchStatement(statement=text)

            try:
                pgbench_statement.save()

            except Exception as e:
                raise RuntimeError(e)

        run_statement = PgBenchRunStatement(latency=latency, line_id=line_id, pgbench_result_id=pgbench_result_id, result_id=pgbench_statement)

        try:
            run_statement.save()
            line_id += 1

        except Exception as e:
            raise RuntimeError(e)


def parse_pgbench_log_values(result, values):

    lines = values.splitlines()

    for line in lines:
        results = line.split()

        date = datetime.utcfromtimestamp(int(results[0])).strftime("%Y-%m-%dT%H:%M:%S%z")

        log = PgBenchLog(pgbench_result_id=result, interval_start=date, num_transactions=results[1], sum_latency=results[2], sum_latency_2=results[3], min_latency=results[4], max_latency=results[5])

        try:
            log.save()

        except Exception as e:
            raise RuntimeError(e)


def parse_pgbench_logs(result, log_array, iteration):

    found = False

    for log in log_array:

        for key, value in log.items():

            # tag-scale-duration-clients-iteration
            configs = key.split('-')

            if configs[1] == 'ro':
                read_only = True
            else:
                read_only = False

            # first of all, check that the config of each benchmark actually exists
            pgbench_config = PgBenchBenchmark.objects.filter(clients=configs[4], scale=configs[2], duration=configs[3], read_only=read_only).get()

            # then, check if it is the same as the test result
            if pgbench_config.pgbench_benchmark_id == result.benchmark_config.pgbench_benchmark_id:
                if int(configs[5]) == iteration:
                    parse_pgbench_log_values(result, value)
                    found = True

    # if no match has been found, return error
    if not found:
        raise RuntimeError('Invalid PgBench logs.')


def parse_pg_stat_statements(pgbench_result_id, result):
    for item in result:

        try:
            query = PgStatStatementsQuery.objects.get(query=item['query'])

        except PgStatStatementsQuery.DoesNotExist:

            try:

                query = PgStatStatementsQuery(query=item['query'])
                query.save()

            except Exception as e:
                raise RuntimeError(e)

        pg_stat_statements = PgStatStatements(
            pgbench_result_id=pgbench_result_id,
            query=query,
            queryid=item.get('queryid', None),
            userid=item.get('userid', None),
            dbid=item.get('dbid', None),
            plans=item.get('plans', None),
            total_plan_time=item.get('total_plan_time', None),
            min_plan_time=item.get('min_plan_time', None),
            max_plan_time=item.get('max_plan_time', None),
            mean_plan_time=item.get('mean_plan_time', None),
            stddev_plan_time=item.get('stddev_plan_time', None),
            calls=item.get('calls', None),
            total_exec_time=item.get('total_exec_time', None),
            min_exec_time=item.get('min_exec_time', None),
            max_exec_time=item.get('max_exec_time', None),
            mean_exec_time=item.get('mean_exec_time', None),
            stddev_exec_time=item.get('stddev_exec_time', None),
            rows=item.get('rows', None),
            shared_blks_hit=item.get('shared_blks_hit', None),
            shared_blks_read=item.get('shared_blks_read', None),
            shared_blks_dirtied=item.get('shared_blks_dirtied', None),
            shared_blks_written=item.get('shared_blks_written', None),
            local_blks_hit=item.get('local_blks_hit', None),
            local_blks_read=item.get('local_blks_read', None),
            local_blks_dirtied=item.get('local_blks_dirtied', None),
            local_blks_written=item.get('local_blks_written', None),
            temp_blks_read=item.get('temp_blks_read', None),
            temp_blks_written=item.get('temp_blks_written', None),
            blk_read_time=item.get('blk_read_time', None),
            blk_write_time=item.get('blk_write_time', None),
            wal_records=item.get('wal_records', None),
            wal_fpi=item.get('wal_fpi', None),
            wal_bytes=item.get('wal_bytes', None),
        )

        try:
            pg_stat_statements.save()

        except Exception as e:
            raise RuntimeError(e)


def parse_collectd(pgbench_result_id, result):

    def parse_epoch_value(raw_data):
        data = {}

        for key, value in raw_data.items():
            for item in value:
                if item['epoch'] not in data:
                    data[item['epoch']] = {}

        for key, value in raw_data.items():
            for item in value:
                if 'value' in item:
                    data[item['epoch']][key] = item['value']

        return data

    def get_collectd_item(target, data):
        for key, value in data.items():
            if target in key:
                return value

        return None

    collectd = list(result.values())[0]

    cpu_average = parse_epoch_value(collectd['aggregation-cpu-average'])
    processes = parse_epoch_value(collectd['processes'])
    contextswitch = parse_epoch_value(collectd['contextswitch'])
    ipc_shm = parse_epoch_value(collectd['ipc-shm'])
    ipc_msg = parse_epoch_value(collectd['ipc-msg'])
    ipc_sem = parse_epoch_value(collectd['ipc-sem'])
    memory = parse_epoch_value(collectd['memory'])
    swap = parse_epoch_value(collectd['swap'])
    vmem = parse_epoch_value(collectd['vmem'])

    try:

        try:
            for key, value in cpu_average.items():
                collectd_cpu = CollectdCpu(
                    epoch=float(key),
                    percent_user=float(get_collectd_item('percent-user', value)),
                    percent_system=float(get_collectd_item('percent-system', value)),
                    percent_idle=float(get_collectd_item('percent-idle', value)),
                    percent_wait=float(get_collectd_item('percent-wait', value)),
                    percent_nice=float(get_collectd_item('percent-nice', value)),
                    percent_interrupt=float(get_collectd_item('percent-interrupt', value)),
                    percent_softirq=float(get_collectd_item('percent-softirq', value)),
                    percent_steal=float(get_collectd_item('percent-steal', value)),
                    pgbench_result_id=pgbench_result_id,
                )

                collectd_cpu.save()

        except TypeError:
            pass

        try:
            for key, value in processes.items():
                collectd_processes = CollectdProcess(
                    epoch=float(key),
                    fork_rate=int(float(get_collectd_item('fork_rate', value))),
                    ps_state_running=int(float(get_collectd_item('ps_state-running', value))),
                    ps_state_stopped=int(float(get_collectd_item('ps_state-stopped', value))),
                    ps_state_sleeping=int(float(get_collectd_item('ps_state-sleeping', value))),
                    ps_state_paging=int(float(get_collectd_item('ps_state-paging', value))),
                    ps_state_blocked=int(float(get_collectd_item('ps_state-blocked', value))),
                    ps_state_zombies=int(float(get_collectd_item('ps_state-zombies', value))),
                    pgbench_result_id=pgbench_result_id,
                )

                collectd_processes.save()

        except TypeError:
            pass

        try:
            for key, value in contextswitch.items():
                collectd_contextswitch = CollectdContextswitch(
                    epoch=float(key),
                    contextswitch=int(float(get_collectd_item('contextswitch', value))),
                    pgbench_result_id=pgbench_result_id,
                )

                collectd_contextswitch.save()

        except TypeError:
            pass

        try:
            for key, value in ipc_shm.items():
                collectd_ipc_shm = CollectdIpcShm(
                    epoch=float(key),
                    segments=int(float(get_collectd_item('segments', value))),
                    bytes_total=int(float(get_collectd_item('bytes-total', value))),
                    bytes_rss=int(float(get_collectd_item('bytes-rss', value))),
                    bytes_swapped=int(float(get_collectd_item('bytes-swapped', value))),
                    pgbench_result_id=pgbench_result_id,
                )

                collectd_ipc_shm.save()

        except TypeError:
            pass

        try:
            for key, value in ipc_msg.items():
                collectd_ipc_msg = CollectdIpcMsg(
                    epoch=float(key),
                    count_space=int(float(get_collectd_item('count-space', value))),
                    count_queues=int(float(get_collectd_item('count-queues', value))),
                    count_headers=int(float(get_collectd_item('count-headers', value))),
                    pgbench_result_id=pgbench_result_id,
                )

                collectd_ipc_msg.save()

        except TypeError:
            pass

        try:
            for key, value in ipc_sem.items():
                collectd_ipc_sem = CollectdIpcSem(
                    epoch=float(key),
                    count_total=int(float(get_collectd_item('count-total', value))),
                    count_arrays=int(float(get_collectd_item('count-arrays', value))),
                    pgbench_result_id=pgbench_result_id,
                )

                collectd_ipc_sem.save()

        except TypeError:
            pass

        try:
            for key, value in memory.items():
                collectd_memory = CollectdMemory(
                    epoch=float(key),
                    memory_free=int(float(get_collectd_item('memory-free', value))),
                    memory_used=int(float(get_collectd_item('memory-used', value))),
                    memory_cached=int(float(get_collectd_item('memory-cached', value))),
                    memory_buffered=int(float(get_collectd_item('memory-buffered', value))),
                    memory_slab_recl=int(float(get_collectd_item('memory-slab_recl', value))),
                    memory_slab_unrecl=int(float(get_collectd_item('memory-slab_unrecl', value))),
                    pgbench_result_id=pgbench_result_id,
                )

                collectd_memory.save()

        except TypeError:
            pass

        try:
            for key, value in swap.items():
                collectd_swap = CollectdSwap(
                    epoch=float(key),
                    swap_free=int(float(get_collectd_item('swap-free', value))),
                    swap_used=int(float(get_collectd_item('swap-used', value))),
                    swap_cached=int(float(get_collectd_item('swap-cached', value))),
                    swap_io_in=int(float(get_collectd_item('swap_io-in', value))),
                    swap_io_out=int(float(get_collectd_item('swap_io-out', value))),
                    pgbench_result_id=pgbench_result_id,
                )

                collectd_swap.save()

        except TypeError:
            pass

        try:
            for key, value in vmem.items():
                collectd_vmem = CollectdVmem(
                    epoch=float(key),
                    vmpage_number_active_file=int(float(get_collectd_item('vmpage_number-active_file', value))),
                    vmpage_number_inactive_file=int(float(get_collectd_item('vmpage_number-inactive_file', value))),
                    vmpage_number_isolated_file=int(float(get_collectd_item('vmpage_number-isolated_file', value))),
                    vmpage_number_active_anon=int(float(get_collectd_item('vmpage_number-active_anon', value))),
                    vmpage_number_inactive_anon=int(float(get_collectd_item('vmpage_number-inactive_anon', value))),
                    vmpage_number_isolated_anon=int(float(get_collectd_item('vmpage_number-isolated_anon', value))),
                    vmpage_number_file_pages=int(float(get_collectd_item('vmpage_number-file_pages', value))),
                    vmpage_number_file_hugepages=int(float(get_collectd_item('vmpage_number-file_hugepages', value))),
                    vmpage_number_file_pmdmapped=int(float(get_collectd_item('vmpage_number-file_pmdmapped', value))),
                    vmpage_number_kernel_stack=int(float(get_collectd_item('vmpage_number-kernel_stack', value))),
                    vmpage_number_kernel_misc_reclaimable=int(float(get_collectd_item('vmpage_number-kernel_misc_reclaimable', value))),
                    vmpage_number_slab_reclaimable=int(float(get_collectd_item('vmpage_number-slab_reclaimable', value))),
                    vmpage_number_slab_unreclaimable=int(float(get_collectd_item('vmpage_number-slab_unreclaimable', value))),
                    vmpage_number_zone_write_pending=int(float(get_collectd_item('vmpage_number-zone_write_pending', value))),
                    vmpage_number_zone_unevictable=int(float(get_collectd_item('vmpage_number-zone_unevictable', value))),
                    vmpage_number_zone_active_anon=int(float(get_collectd_item('vmpage_number-zone_active_anon', value))),
                    vmpage_number_zone_inactive_anon=int(float(get_collectd_item('vmpage_number-zone_inactive_anon', value))),
                    vmpage_number_zone_active_file=int(float(get_collectd_item('vmpage_number-zone_active_file', value))),
                    vmpage_number_zone_inactive_file=int(float(get_collectd_item('vmpage_number-zone_inactive_file', value))),
                    vmpage_number_foll_pin_acquired=int(float(get_collectd_item('vmpage_number-foll_pin_acquired', value))),
                    vmpage_number_foll_pin_released=int(float(get_collectd_item('vmpage_number-foll_pin_released', value))),
                    vmpage_number_dirty=int(float(get_collectd_item('vmpage_number-dirty', value))),
                    vmpage_number_dirty_threshold=int(float(get_collectd_item('vmpage_number-dirty_threshold', value))),
                    vmpage_number_dirty_background_threshold=int(float(get_collectd_item('vmpage_number-dirty_background_threshold', value))),
                    vmpage_number_vmscan_write=int(float(get_collectd_item('vmpage_number-vmscan_write', value))),
                    vmpage_number_vmscan_immediate_reclaim=int(float(get_collectd_item('vmpage_number-vmscan_immediate_reclaim', value))),
                    vmpage_number_anon_pages=int(float(get_collectd_item('vmpage_number-anon_pages', value))),
                    vmpage_number_anon_transparent_hugepages=int(float(get_collectd_item('vmpage_number-anon_transparent_hugepages', value))),
                    vmpage_number_shmem=int(float(get_collectd_item('vmpage_number-shmem', value))),
                    vmpage_number_shmem_hugepages=int(float(get_collectd_item('vmpage_number-shmem_hugepages', value))),
                    vmpage_number_shmem_pmdmapped=int(float(get_collectd_item('vmpage_number-shmem_pmdmapped', value))),
                    vmpage_number_writeback=int(float(get_collectd_item('vmpage_number-writeback', value))),
                    vmpage_number_writeback_temp=int(float(get_collectd_item('vmpage_number-writeback_temp', value))),
                    vmpage_number_free_pages=int(float(get_collectd_item('vmpage_number-free_pages', value))),
                    vmpage_number_free_cma=int(float(get_collectd_item('vmpage_number-free_cma', value))),
                    vmpage_number_bounce=int(float(get_collectd_item('vmpage_number-bounce', value))),
                    vmpage_number_unevictable=int(float(get_collectd_item('vmpage_number-unevictable', value))),
                    vmpage_number_page_table_pages=int(float(get_collectd_item('vmpage_number-page_table_pages', value))),
                    vmpage_number_mapped=int(float(get_collectd_item('vmpage_number-mapped', value))),
                    vmpage_number_zspages=int(float(get_collectd_item('vmpage_number-zspages', value))),
                    vmpage_number_mlock=int(float(get_collectd_item('vmpage_number-mlock', value))),
                    vmpage_number_unstable=int(float(get_collectd_item('vmpage_number-unstable', value))),
                    vmpage_action_written=int(float(get_collectd_item('vmpage_action-written', value))),
                    vmpage_action_dirtied=int(float(get_collectd_item('vmpage_action-dirtied', value))),
                    pgbench_result_id=pgbench_result_id,
                )

                collectd_vmem.save()

        except TypeError:
            pass

    except Exception as e:
        raise RuntimeError(e)


def parse_pgbench_results(item, run_id, pgbench_log):

    json = item['iterations']
    iterations = 0

    for client in item['clients']:

        for result in json:

            if int(result['clients']) == client:

                pgbench_config = PgBenchBenchmark.objects.filter(clients=result['clients'], scale=item['scale'], duration=item['duration'], read_only=item['read_only']).get()

                pgbench_result_last = PgBenchResult.objects.order_by('-pgbench_result_id').first()

                if pgbench_result_last is None:
                    iterations = 0

                # assuming results get added in order
                elif (pgbench_result_last.benchmark_config.pgbench_benchmark_id == pgbench_config.pgbench_benchmark_id) and (pgbench_result_last.run_id.run_id == run_id):
                    iterations += 1

                else:
                    iterations = 0

                # remove statement latencies
                statement_latencies = result['statement_latencies']

                result_object = PgBenchResult(run_id=run_id, benchmark_config=pgbench_config, tps=result['tps'], mode=result['mode'], latency=result['latency'], start=result['start'], end=result['end'], iteration=result['iteration'], init=result['init'])

                try:
                    result_object.save()

                    parse_pgbench_logs(result_object, pgbench_log, iterations)
                    parse_pgbench_statement_latencies(statement_latencies, result_object)

                    # parse pg_stat_statements
                    pg_stat_statements = result['pg_stat_statements']
                    parse_pg_stat_statements(result_object, pg_stat_statements)

                    # parse collectd
                    collectd = result['collectd']
                    parse_collectd(result_object, collectd)

                except Exception as e:
                    raise RuntimeError(e)


def parse_os_kernel(json_data):
    try:
        os_distributor = OsDistributor.objects.filter(dist_name=json_data['os_information']['distributor']).get()

    except OsDistributor.DoesNotExist:

        try:

            os_distributor = OsDistributor(dist_name=json_data['os_information']['distributor'])
            os_distributor.save()

        except Exception as e:
            raise RuntimeError(e)
    try:
        os_kernel = Kernel.objects.filter(kernel_name=json_data['kernel']['uname_s']).get()

    except Kernel.DoesNotExist:

        try:

            os_kernel = Kernel(kernel_name=json_data['kernel']['uname_s'])
            os_kernel.save()

        except Exception as e:
            raise RuntimeError(e)

    try:
        os_version = OsVersion.objects.filter(dist_id=os_distributor.os_distributor_id, release=json_data['os_information']['release'], codename=json_data['os_information']['codename'], description=json_data['os_information']['description']).get()

    except OsVersion.DoesNotExist:

        try:

            os_version = OsVersion(dist_id=os_distributor, release=json_data['os_information']['release'], codename=json_data['os_information']['codename'], description=json_data['os_information']['description'])
            os_version.save()

        except Exception as e:
            raise RuntimeError(e)

    try:
        kernel_version = OsKernelVersion.objects.filter(kernel_id=os_kernel.kernel_id, kernel_release=json_data['kernel']['uname_r'], kernel_version=json_data['kernel']['uname_v']).get()

    except OsKernelVersion.DoesNotExist:

        try:

            kernel_version = OsKernelVersion(kernel_id=os_kernel, kernel_release=json_data['kernel']['uname_r'], kernel_version=json_data['kernel']['uname_v'])
            kernel_version.save()

        except Exception as e:
            raise RuntimeError(e)

    return os_version, kernel_version


def parse_compiler(json_data):
    compiler_raw = json_data['compiler']
    compiler_match = re.search('compiled by (.*),', compiler_raw)

    if compiler_match:
        compiler = compiler_match.group(1)

    else:
        compiler = 'impossible to parse compiler'

    try:
        compiler_result = Compiler.objects.filter(compiler=compiler).get()

    except Compiler.DoesNotExist:

        try:

            compiler_result = Compiler(compiler=compiler)
            compiler_result.save()

        except Exception as e:
            raise RuntimeError(e)

    return compiler_result


def parse_git(json_data):
    try:
        repo = GitRepo.objects.filter(url=json_data['git']['remote']).get()

    except GitRepo.DoesNotExist:

        try:

            repo = GitRepo(url=json_data['git']['remote'])
            repo.save()

        except Exception as e:
            raise RuntimeError(e)

    try:
        branch = Branch.objects.filter(name=json_data['git']['branch'], git_repo=repo.git_repo_id).get()

    except Branch.DoesNotExist:

        try:

            branch = Branch(name=json_data['git']['branch'], git_repo=repo)
            branch.save()

        except Exception as e:
            raise RuntimeError(e)

    commit = json_data['git']['commit']

    return branch, commit


def parse_hardware(json_data):
    hardware_info_new = parse_linux_data(json_data)

    try:
        hardware_info = HardwareInfo.objects.filter(cpu_brand=hardware_info_new['cpu_brand'], cpu_cores=hardware_info_new['cpu_cores'], hz=hardware_info_new['hz'], total_memory=hardware_info_new['total_memory'], total_swap=hardware_info_new['total_swap'], sysctl_hash=hardware_info_new['sysctl_hash'], mounts_hash=hardware_info_new['mounts_hash']).get()

    except HardwareInfo.DoesNotExist:

        try:

            hardware_info = HardwareInfo(cpu_brand=hardware_info_new['cpu_brand'], cpu_cores=hardware_info_new['cpu_cores'], hz=hardware_info_new['hz'], total_memory=hardware_info_new['total_memory'], total_swap=hardware_info_new['total_swap'], sysctl_hash=hardware_info_new['sysctl_hash'], mounts_hash=hardware_info_new['mounts_hash'], sysctl=hardware_info_new['sysctl'], mounts=hardware_info_new['mounts'])

            hardware_info.save()

        except Exception as e:
            raise RuntimeError(e)

    return hardware_info


def parse_postgres(json_data):
    postgres_hash, postgres_hash_object = get_hash(json_data['postgres_settings'])

    try:
        postgres_info = PostgresSettingsSet.objects.filter(settings_sha256=postgres_hash).get()

    except PostgresSettingsSet.DoesNotExist:

        try:

            postgres_info = PostgresSettingsSet(settings_sha256=postgres_hash)
            postgres_info.save()
            add_postgres_settings(postgres_hash, postgres_hash_object)

        except Exception as e:
            raise RuntimeError(e)

    return postgres_info
