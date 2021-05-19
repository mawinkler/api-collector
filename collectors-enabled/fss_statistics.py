"""Example metrics collector for File Storage Security

This script is a pluggable module for the api-collector. It collects
information from File Storage Security by it's RESTful API, calculates some
metrics and creates a dictionary which is feedede into Prometheus
by the api-collector.

This file has one single funtion collect(), which is called by the
api-collector. For testing purposes, one can directly run the collector
with python3 <FILENAME>. You need to ensure the presence of the
credentials in the given directory.
"""

import json
import requests
import logging
import pprint
from datetime import datetime, timedelta

# Constants
_LOGGER = logging.getLogger(__name__)

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
    c1_url=open('/etc/workload-security-credentials/c1_url', 'r').read()
    api_key=open('/etc/workload-security-credentials/api_key', 'r').read()

    # Define your metrics here
    result = {
        "CounterMetricFamilyName": "fss_statistics",
        "CounterMetricFamilyHelpText": "File Storage Daily Statistics",
        "CounterMetricFamilyLabels": ['statistic'],
        "Metrics": []
    }

    startTime = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    endTime = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999).strftime("%Y-%m-%dT%H:%M:%SZ")
    interval = "1h"

    # API query and response parsing here
    url = "https://" + c1_url + "/api/filestorage/statistics/scans?from=" \
        + startTime + "&to=" \
        + endTime + "&interval=" + interval
    post_header = {
        "Content-Type": "application/json",
        "api-secret-key": api_key,
        "api-version": "v1",
    }
    response = requests.get(
        url, headers=post_header, verify=True
    ).json()

    # Error handling
    if "message" in response:
        if response['message'] == "Invalid API Key":
            raise ValueError("Invalid API Key")

    # Calculate scan and detection metrics
    scans = 0
    detections = 0
    if len(response['statistics']) > 0:
        for statistic in response['statistics']:
            scans += statistic['scans']
            detections += statistic['detections']

    # Add metrics
    result['Metrics'].append([['scans'], scans])
    result['Metrics'].append([['detections'], detections])

    url = "https://" + c1_url + "/api/filestorage/stacks" 
    post_header = {
        "Content-Type": "application/json",
        "api-secret-key": api_key,
        "api-version": "v1",
    }
    response = requests.get(
        url, headers=post_header, verify=True
    ).json()

    # Error handling
    if "message" in response:
        if response['message'] == "Invalid API Key":
            raise ValueError("Invalid API Key")

    scanner_stacks = 0
    storage_stacks = 0
    if len(response['stacks']) > 0:
        for stack in response['stacks']:
            if stack['type'] == "scanner":
                scanner_stacks += 1
            if stack['type'] == "storage":
                storage_stacks += 1
            
    # Add metrics
    result['Metrics'].append([['scanner_stacks'], scanner_stacks])
    result['Metrics'].append([['storage_stacks'], storage_stacks])

    # Return results
    pprint.pprint(result)
    return result

if __name__ == '__main__':
    collect()