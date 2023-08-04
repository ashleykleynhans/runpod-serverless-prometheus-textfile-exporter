#!/usr/bin/env python3
import os
import sys
import httpx
import json
import yaml


def load_config(script_path):
    try:
        config_file = f'{script_path}/config.yml'

        with open(config_file, 'r') as stream:
            return yaml.safe_load(stream)
    except FileNotFoundError:
        print(f'ERROR: Config file {config_file} not found!')
        sys.exit()


def get_api_key(endpoint, config):
    api_key = None

    if 'api_key' in endpoint:
        api_key = endpoint['api_key']
    elif 'api_key' in config:
        api_key = config['api_key']
    else:
        raise Exception('No api_key configured in config.yml')

    return api_key


def get_health(endpoint, config):
    api_key = get_api_key(endpoint, config)
    endpoint_id = endpoint['endpoint_id']

    return httpx.get(
        f'https://api.runpod.ai/v2/{endpoint_id}/health',
        headers={
            'Authorization': f'Bearer {api_key}'
        }
    )


def write_health_data(tmp_output_file, endpoint, data):
    endpoint_name = endpoint['name']

    jobs_completed = data['jobs']['completed']
    jobs_failed = data['jobs']['failed']
    jobs_in_progress = data['jobs']['inProgress']
    jobs_in_queue = data['jobs']['inQueue']
    jobs_retried = data['jobs']['retried']

    workers_idle = data['workers']['idle']
    workers_running = data['workers']['running']

    f = open(tmp_output_file, 'a')
    f.write('jobs_completed{endpoint="' + endpoint_name + '"} ' + str(jobs_completed) + '\n')
    f.write('jobs_failed{endpoint="' + endpoint_name + '"} ' + str(jobs_failed) + '\n')
    f.write('jobs_in_progress{endpoint="' + endpoint_name + '"} ' + str(jobs_in_progress) + '\n')
    f.write('jobs_in_queue{endpoint="' + endpoint_name + '"} ' + str(jobs_in_queue) + '\n')
    f.write('jobs_retried{endpoint="' + endpoint_name + '"} ' + str(jobs_retried) + '\n')
    f.write('workers_idle{endpoint="' + endpoint_name + '"} ' + str(workers_idle) + '\n')
    f.write('workers_running{endpoint="' + endpoint_name + '"} ' + str(workers_running) + '\n')
    f.close()


def get_endpoint_health(config):
    filename = 'runpod_endpoints.prom'
    output_file = os.path.join(config['textfile_path'], filename)
    tmp_output_file = f'{output_file}.$$'

    for endpoint in config['endpoints']:
        endpoint_name = endpoint['name']
        r = get_health(endpoint, config)

        if r.status_code == 401:
            raise Exception(f'Authentication failed for {endpoint_name} endpoint, check your API key')
        elif r.status_code == 200:
            write_health_data(tmp_output_file, endpoint, r.json())
        else:
            raise Exception(f'Unexpected status code from /health endpoint: {r.status_code}')

    os.rename(tmp_output_file, output_file)


if __name__ == '__main__':
    script_path = os.path.dirname(__file__)
    config = load_config(script_path)
    get_endpoint_health(config)
