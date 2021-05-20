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
import logging
import sys
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY
from prometheus_client import start_http_server
from prometheus_client import Summary

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format='%(asctime)s %(levelname)s (%(threadName)s) [%(funcName)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("prometheus_client").setLevel(logging.DEBUG)

COLLECTOR_RUN_TIME = Summary('api_collector_collect_seconds', 'Full collector run seconds')

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

    @COLLECTOR_RUN_TIME.time()
    def collect(self):
        """Creates the metrics for Prometheus

        Injects the custom metrics generators and provides the metrics
        via the http server to Prometheus
        """

        _LOGGER.info("Starting Collector Run")

        for collector in glob.glob("collectors/*.py"):
            # convert the script file name into it's module name
            # (hoping it doesn't contain any spaces or dash characters)
            module_name = "." + os.path.basename(collector).replace('.py', '')

            _LOGGER.info("Running collector {}".format(collector))

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

            _LOGGER.info("Metrics from collector {} received: {} ".format(collector, len(response["Metrics"])))

            # loop over the the metrics reported
            for metric in response["Metrics"]:
                cmf.add_metric(metric[0], metric[1])

            yield cmf

        _LOGGER.info("Collector Run finished")

if __name__ == '__main__':
    start_http_server(8000)
    REGISTRY.register(CustomCollector())
    while True:
        time.sleep(1)
