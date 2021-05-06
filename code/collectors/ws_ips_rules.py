"""Example metrics collector for Workload Security

This script is a pluggable module for the api-collector. It collects
information from Workload Security by it's RESTful API, calculates some
metrics and creates a dictionary which will be feed into Prometheus
by the api-collector.

This file has one single funtion collect(), which is called by the
api-collector. For testing purposes, one can directly run the collector
with python3 <FILENAME>. You need to ensure the presence of the
credentials in the given directory.
"""

import json
import requests
# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context
# import urllib3

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
    ws_url=open('/etc/workload-security-credentials/ws_url', 'r').read()
    api_key=open('/etc/workload-security-credentials/api_key', 'r').read()

    # Define your metrics here
    result = {
        "CounterMetricFamilyName": "workload_security_computers",
        "CounterMetricFamilyHelpText": "Workload Security Assigned IPS Rules Metrics",
        "CounterMetricFamilyLabels": ['displayName', 'lastIPUsed'],
        "Metrics": []
    }

    # API query and response parsing here
    url = "https://" + ws_url + "/api/computers"
    data = {}
    post_header = {
        "Content-type": "application/json",
        "api-secret-key": api_key,
        "api-version": "v1",
    }
    response = requests.get(
        url, data=json.dumps(data), headers=post_header, verify=True
    ).json()

    # Error handling
    if "message" in response:
        if response["message"] == "Invalid API Key":
            raise ValueError("Invalid API Key")

    # Calculate your metrics
    if len(response["computers"]) > 0:
        for computer in response["computers"]:
            computer_name = computer["displayName"]
            computer_ip = str(computer["lastIPUsed"])
            computer_rule_count = 0

            if "ruleIDs" in computer["intrusionPrevention"]:
                computer_rule_count = len(computer["intrusionPrevention"]["ruleIDs"])
            else:
                computer_rule_count = 0

            # Add a single metric
            result['Metrics'].append({
                "hostname": computer_name,
                "ip": str(computer_ip),
                "metric": computer_rule_count
            })

    # Return results
    return result


if __name__ == '__main__':
    collect()