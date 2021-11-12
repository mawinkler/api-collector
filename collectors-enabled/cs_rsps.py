"""Example metrics collector for Container Security

This script is a pluggable module for the api-collector. It collects
information from Container Security by it's RESTful API, calculates some
metrics and creates a dictionary which is feeded into Prometheus
by the api-collector.

Purpose of this collector is to provide metrics, how many runtime security
events are detected by the runtime security module of Container
Security within the last minute.

This file has one single funtion collect(), which is called by the
api-collector. For testing purposes, one can directly run the collector
with python3 <FILENAME>. You need to ensure the presence of the
credentials in the given directory.
"""

import requests
import logging
import sys
from datetime import datetime, timedelta
import pprint

# Constants
_LOGGER = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format='%(asctime)s %(levelname)s (%(threadName)s) [%(funcName)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

def collect() -> dict:
    """
    Query an API, calculate the required metrics and return a JSON object
    
    Parameters
    ----------
    none

    Raises
    ------
    ValueError
        Houston, we have a problem

    Returns
    -------
    {
        "CounterMetricFamilyName": <YOUR METRICS FAMILY NAME>,
        "CounterMetricFamilyHelpText": <DESCRIPTION OF YOUR METRICS>,
        "CounterMetricFamilyLabels": [<LABEL 1>, <LABEL 2>, ...],
        "Metrics": [<METRIC 1>, <METRIC 2>, ...]
    }
    """

    # API credentials are mounted to /etc
    c1_url = open('/etc/cloudone-credentials/c1_url', 'r').read().rstrip('\n')
    api_key = open('/etc/cloudone-credentials/api_key', 'r').read().rstrip('\n')

    _LOGGER.debug("Cloud One API endpoint: {}".format(c1_url))

    # Define your metrics here
    result = {
        "CounterMetricFamilyName": "cs_rsps",
        "CounterMetricFamilyHelpText": "Container Security Runtime Events per Slice",
        "CounterMetricFamilyLabels": ['clusterName', 'policyName', 'pod', 'name', 'mitigation', 'namespace', 'severity'],
        "Metrics": []
    }

    start_time = (datetime.utcnow() - timedelta(minutes=60)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # mitigation_table = {
    #     "log": 0,
    #     "isolate": 1,
    #     "terminate": 2
    # }

    # API query and response parsing here
    cursor = ""
    events = []
    while True:
        url = "https://container." + c1_url + "/api/events/sensors?" \
            + "next=" + cursor \
            + "&limit=" + str(25) \
            + "&fromTime=" + start_time \
            + "&toTime=" + end_time
        post_header = {
            "Content-Type": "application/json",
            "Authorization": "ApiKey " + api_key,
            "api-version": "v1",
        }
        try:
            response = requests.get(
                url, headers=post_header, verify=True
            )

            response.encoding = response.apparent_encoding
            response.raise_for_status()
        except requests.exceptions.Timeout as err:
            _LOGGER.error(response.text)
            raise SystemExit(err)
        except requests.exceptions.HTTPError as err:
            _LOGGER.error(response.text)
            raise SystemExit(err)
        except requests.exceptions.RequestException as err:
            # catastrophic error. bail.
            _LOGGER.error(response.text)
            raise SystemExit(err)

        response = response.json()
        # Error handling
        if "message" in response:
            if response['message'] == "Invalid API Key":
                _LOGGER.error("API error: {}".format(response['message']))
                raise ValueError("Invalid API Key")

        events_count = len(response.get('events', {}))
        _LOGGER.debug("Number of events in result set: %d", events_count)
        if events_count > 0:
            for event in response.get('events', {}):
                events.append(event)

        cursor = response.get('next', "")
        if cursor == "":
            break

    _LOGGER.debug("{} Container Security runtime events received".format(str(len(events))))

    # Calculate metrics
    # ['clusterName', 'policyName', 'pod', 'name', 'mitigation', 'namespace', 'severity']
    results = {}
    if len(events) > 0:
        for event in events:
            # pprint.pprint(event)
            labels = []
            labels.append(event['clusterName'])
            labels.append(event['policyName'])
            labels.append(event['k8s.pod.name'])
            labels.append(event['name'])
            labels.append(event['mitigation'])
            labels.append(event['k8s.ns.name'])
            labels.append(event['severity'])
            labelss = '#'.join(labels)

            if (labelss in results):
                results[labelss] = results[labelss] + 1
            else:
                results[labelss] = 1

    # Convert to [[,,,],]
    for entry in results:
        result['Metrics'].append([entry.split('#'), results[entry]])

    # Return results
    _LOGGER.debug("Metrics collected: {}".format(result))
    return result

if __name__ == '__main__':
    collect()
