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


def upload(api_url, results_directory, token):

    path_url = 'run/upload/'
    url = api_url + path_url

    json_file = results_directory + "/results.json"

    with open(json_file,'r') as load_f:
        load_dict = (json.load(load_f, encoding="UTF-8"))

    pgbench_logs = []

    # extracting logs
    for file in os.scandir(folders.LOG_PATH):

        filename = os.path.basename(file)
        name = os.path.splitext(filename)[0]

        if (name == 'runtime_log'):
            with open (file, 'r') as f:
                runtime_data = json.load(f)
                load_dict.update(runtime_data)

        elif (name.startswith('pgbench-')):
            with open (file, 'r') as f:
                log = f.read()
                pgbench_logs.append({name: log})

        else:

            with open (file, 'r') as f:
                content = f.read()

            temp = {name: content}
            load_dict.update(temp)

    load_dict.update({'pgbench_log_aggregate': pgbench_logs})

    with open(folders.OUTPUT_PATH + '/results_complete.json', 'w+') as results:
        results.write(json.dumps(load_dict, indent=4))
        http_post(url, load_dict, token)
