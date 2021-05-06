import ssl

ssl._create_default_https_context = ssl._create_unverified_context
import urllib3

import time
import json
import yaml
import requests
import os

# dependency injection
import importlib
import inspect

from prometheus_client.core import GaugeMetricFamily, REGISTRY, CounterMetricFamily
from prometheus_client import start_http_server


class CustomCollector(object):
    def __init__(self):
        print("init")
        pass

    def collect(self):
        ws_url=open('/etc/workload-security-credentials/ws_url', 'r').read()
        api_key=open('/etc/workload-security-credentials/api_key', 'r').read()

        # this should be detected later on
        script = "ws_ips_rules.py"

        # convert the script file name into it's module name
        # (hoping it doesn't contain any spaces or dash characters)
        module_name = script.replace('.py', '')

        # import the module of that name
        module = importlib.import_module(module_name)

        # get it's parameter names
        args = inspect.signature(module.collect).parameters

        # construct a dictionary with these names as keys and the
        # instance of the API abstraction class, as the value
        kwargs = {}
        for name in args:
            kwargs[name] = get_service_instance(name)

        # call module.collect ans store the return value in response
        response = module.collect(**kwargs)
        

        c = CounterMetricFamily(response['CounterMetricFamilyName'],
                                response['CounterMetricFamilyHelpText'],
                                labels=response['CounterMetricFamilyLabels'])

        for metric in response["Metrics"]:
            computer_name = metric['hostname']
            computer_rule_count = metric['metric']
            computer_ip = metric['ip']
        
            c.add_metric([computer_name, str(computer_ip)], computer_rule_count)

        yield c


if __name__ == '__main__':
    start_http_server(8000)
    REGISTRY.register(CustomCollector())
    while True:
        time.sleep(1)
