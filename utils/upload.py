# -*- encoding:utf-8 -*-

import json
import requests
import os
import folders
from settings_local import BASIC_AUTH, USERNAME, PASSWORD

def byteify(input):
    if isinstance(input, dict):
        return {byteify(key):byteify(value) for key, value in input.items()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

def http_post(url, data, token):  
    postdata = data  
    post = []  
    post.append(postdata)

    headers = {'Content-Type': 'application/json; charset=utf-8', 'Authorization': token}
    # check if using basic auth, if so add the auth details.
    if BASIC_AUTH:
        r = requests.post(url.encode('utf-8'), data=json.dumps(post).encode('utf-8'), headers=headers,
                          auth=(USERNAME, PASSWORD))
    else:
        r = requests.post(url.encode('utf-8'), data=json.dumps(post).encode('utf-8'), headers=headers)


def upload(api_url, results_directory, token, mode):

    path_url = 'run/upload/'
    url = api_url + path_url
    json_file = folders.OUTPUT_PATH + "/results.json"

    with open(json_file,'r') as load_f:
        load_dict = (json.load(load_f))

    if mode == "tpch":
        upload_path = os.path.join(results_directory, 'metrics')
        upload_path_expalainResults = os.path.join(results_directory, 'Explaintest')
        explain_json_file = upload_path_expalainResults + "/Explain.json"
        with open(explain_json_file, 'r') as load_f:
            tmp_dict = (json.load(load_f))
        explain_dict = {}
        for s, v in tmp_dict.items():
            explain_dict[s] = v
        load_dict["explaine_results"]=explain_dict

        json_file = upload_path + "/Metric.json"
        with open(json_file, 'r') as load_f:
            tpch_res = json.load(load_f)
            load_dict.update(tpch_res)

    pgbench_logs = []
    # extracting logs
    for file in os.scandir(folders.LOG_PATH):

        filename = os.path.basename(file)
        name = os.path.splitext(filename)[0]

        if name == 'runtime_log':
            with open (file, 'r') as f:
                runtime_data = json.load(f)
                load_dict.update(runtime_data)

        elif name.startswith('pgbench-') and mode == "pgbench":
            with open (file, 'r') as f:
                log = f.read()
                pgbench_logs.append({name: log})

        else:
            with open (file, 'r') as f:
                content = f.read()

            temp = {name: content}
            load_dict.update(temp)

    if mode == "pgbench":
        load_dict.update({'pgbench_log_aggregate': pgbench_logs})

    complete_res_file_name = '/pgbench_results_complete.json' if mode == "pgbench" else '/tpch_results_complete.json'
    with open(folders.OUTPUT_PATH + complete_res_file_name, 'w+') as results:
        results.write(json.dumps(load_dict, indent=4))
        http_post(url, load_dict, token)
