"""Example metrics collector for Application Security

This script is a pluggable module for the api-collector. It collects
information from Application Security by it's RESTful API, calculates some
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
        "CounterMetricFamilyName": "as_settings",
        "CounterMetricFamilyHelpText": "Application Security Settings",
        "CounterMetricFamilyLabels": ['name', 'setting'],
        "Metrics": []
    }
    # setting can be
    # 0 - disable
    # 1 - report
    # 2 - mitigate
    setting_table = {
        "disable": 0,
        "report": 1,
        "mitigate": 2
    }

    # API query and response parsing here
    url = "https://" + c1_url + "/api/application/accounts/groups"
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

    # Calculate metrics
    if len(response) > 0:
        for group in response:
            labels = []
            labels.append(group['name'])

            if "credential_stuffing" in group['settings']:
                attlabels = labels[:]
                attlabels.append("credential_stuffing")
                result['Metrics'].append([attlabels, setting_table[group['settings']['credential_stuffing']]])

            if "file_access" in group['settings']:
                attlabels = labels[:]
                attlabels.append("file_access")
                result['Metrics'].append([attlabels, setting_table[group['settings']['file_access']]])

            if "ip_protection" in group['settings']:
                attlabels = labels[:]
                attlabels.append("ip_protection")
                result['Metrics'].append([attlabels, setting_table[group['settings']['ip_protection']]])

            if "malicious_file_upload" in group['settings']:
                attlabels = labels[:]
                attlabels.append("malicious_file_upload")
                result['Metrics'].append([attlabels, setting_table[group['settings']['malicious_file_upload']]])

            if "malicious_payload" in group['settings']:
                attlabels = labels[:]
                attlabels.append("malicious_payload")
                result['Metrics'].append([attlabels, setting_table[group['settings']['malicious_payload']]])

            if "rce" in group['settings']:
                attlabels = labels[:]
                attlabels.append("rce")
                result['Metrics'].append([attlabels, setting_table[group['settings']['rce']]])

            if "redirect" in group['settings']:
                attlabels = labels[:]
                attlabels.append("redirect")
                result['Metrics'].append([attlabels, setting_table[group['settings']['redirect']]])

            if "sqli" in group['settings']:
                attlabels = labels[:]
                attlabels.append("sqli")
                result['Metrics'].append([attlabels, setting_table[group['settings']['sqli']]])

    # Return results
    pprint.pprint(result)
    return result

if __name__ == '__main__':
    collect()