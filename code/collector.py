"""API Metric Collector

This script is a generic metrics collector, designed to work with any
available APIs. It uses dependency injection to dynamically add and
remove metrics collectors located in ./collectors. It uses the
Prometheus python client for the interaction with Prometheus.

It creates an http server on port 8000, which enables Prometheus to
scrape the produced metrics.
"""

import time
import os
import glob
import inspect
import importlib
import ssl
import requests
from collectors import *
from prometheus_client.core import GaugeMetricFamily, REGISTRY, CounterMetricFamily
from prometheus_client import start_http_server

ssl._create_default_https_context = ssl._create_unverified_context

class CustomCollector():
    """
    This class represents the CustomCollector for Prometheus

    Methods
    -------
    collect
        The collector which injects the custom metrics generators
        located inside the collectors namespace
    """

    def __init__(self):
        pass

    def collect(self):
        """Creates the metrics for Prometheus

        Injects the custom metrics generators and provides the metrics
        via the http server to Prometheus
        """

        for collector in glob.glob("collectors/*.py"):
            # convert the script file name into it's module name
            # (hoping it doesn't contain any spaces or dash characters)
            module_name = "." + os.path.basename(collector).replace('.py', '')

            # import the module of that name
            module = importlib.import_module(module_name, 'collectors')

            # get it's parameter names
            args = inspect.signature(module.collect).parameters

            # construct a dictionary with these names as keys and the
            # instance of the API abstraction class, as the value
            kwargs = {}
            for name in args:
                kwargs[name] = get_service_instance(name)

            # call module.collect and store the return value in response
            response = module.collect(**kwargs)

            cmf = CounterMetricFamily(response['CounterMetricFamilyName'],
                                      response['CounterMetricFamilyHelpText'],
                                      labels=response['CounterMetricFamilyLabels'])

            # loop over the the metrics reported
            for metric in response["Metrics"]:
                cmf.add_metric(metric[0], metric[1])

            yield cmf

if __name__ == '__main__':
    start_http_server(8000)
    REGISTRY.register(CustomCollector())
    while True:
        time.sleep(1)
