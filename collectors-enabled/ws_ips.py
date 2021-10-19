"""Example metrics collector for Workload Security

This script is a pluggable module for the api-collector. It collects
information from Workload Security by it's RESTful API, calculates some
metrics and creates a dictionary which is feedede into Prometheus
by the api-collector.

This file has one single funtion collect(), which is called by the
api-collector. For testing purposes, one can directly run the collector
with python3 <FILENAME>. You need to ensure the presence of the
credentials in the given directory.
"""

import json
import requests
import sys
import logging

# Constants
_RESULT_SET_SIZE = 5000
_LOGGER = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s (%(threadName)s) [%(funcName)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

def create_rules_dict(c1_url, api_key) -> dict:
    """
    Build a dictionary of IPS rules and some of their attributes
    
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
        "ID":
        {
            "priority",
            "severity",
            "type",
            "detectOnly"
        },
    }
    """

    result = {}
    
    dict_len = 0
    offset = 0
    while True:

        # API query and response parsing here
        url = "https://workload." + c1_url + "/api/intrusionpreventionrules/search"
        data = {
            "maxItems": _RESULT_SET_SIZE,
            "searchCriteria": [
                {
                    "fieldName": "ID",
                    "idTest": "less-than",
                    "idValue": offset + _RESULT_SET_SIZE,
                }
            ],
        }
        post_header = {
            "Content-type": "application/json",
            "api-secret-key": api_key,
            "api-version": "v1",
        }
        response = requests.post(
            url, data=json.dumps(data), headers=post_header, verify=True
        ).json()

        # Error handling
        if "message" in response:
            if response['message'] == "Invalid API Key":
                raise ValueError("Invalid API Key")

        for rule in response['intrusionPreventionRules']:
            result[rule['ID']] = {
                "priority": rule['priority'],
                "severity": rule['severity'],
                "type": rule['type'],
                "detectOnly": rule['detectOnly']
            }

        if len(rule) != 0 and len(rule) == dict_len:
            dict_len = len(rule)
            break
        if len(rule) != 0 and len(rule) != dict_len:
            dict_len = len(rule)

        offset += _RESULT_SET_SIZE

    _LOGGER.debug("Count of IPS rules in dictionary: {}".format(len(result)))
    return result

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
    api_key = open('/etc/cloudone-credentials/ws_key', 'r').read().rstrip('\n')

    _LOGGER.debug("Cloud One API endpoint: {}".format(c1_url))

    # Define your metrics here
    result = {
        "CounterMetricFamilyName": "ws_ips",
        "CounterMetricFamilyHelpText": "Workload Security IPS Module",
        "CounterMetricFamilyLabels": [
            'cloud_provider',
            'agentStatus',
            'platform',
            'updateStatus',
            'agentVersion',
            'displayName',
            'arribute'],
        "Metrics": []
    }

    # API query and response parsing here
    url = "https://workload." + c1_url + "/api/computers"
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
        if response['message'] == "Invalid API Key":
            _LOGGER.error("API error: {}".format(response['message']))
            raise ValueError("Invalid API Key")

    _LOGGER.debug("Computer listing received")

    rules_dict = create_rules_dict(c1_url, api_key)

    # Calculate your metrics
    if len(response['computers']) > 0:
        for computer in response['computers']:
            rule_count = 0
            severity_low = 0
            severity_medium = 0
            severity_high = 0
            severity_crititcal = 0
            type_vulnerability = 0
            type_exploit = 0

            # Count severities and rule types
            if "ruleIDs" in computer['intrusionPrevention']:
                rule_count = len(computer['intrusionPrevention']['ruleIDs'])
                for ruleId in computer['intrusionPrevention']['ruleIDs']:

                    if rules_dict[ruleId]['severity'] == "low":
                        severity_low += 1
                    if rules_dict[ruleId]['severity'] == "medium":
                        severity_medium += 1
                    if rules_dict[ruleId]['severity'] == "high":
                        severity_high += 1
                    if rules_dict[ruleId]['severity'] == "critical":
                        severity_crititcal += 1
                    if rules_dict[ruleId]['type'] == "vulnerability":
                        type_vulnerability += 1
                    if rules_dict[ruleId]['type'] == "exploit":
                        type_exploit += 1

            labels = []

            # Location
            if "gcpVirtualMachineSummary" in computer:
                labels.append("GCP")
                labels.append(computer['gcpVirtualMachineSummary']['state'].title())

            elif "ec2VirtualMachineSummary" in computer:
                labels.append("AWS")
                labels.append(computer['ec2VirtualMachineSummary']['state'].title())
            elif "azureARMVirtualMachineSummary" in computer:
                labels.append("Azure")
                labels.append(computer['azureARMVirtualMachineSummary']['state'].title())
            else:
                labels.append("On-Prem")
                labels.append(computer['computerStatus']['agentStatus'].title())

            labels.append(computer['platform'])

            if 'securityUpdates' in computer:
                labels.append(computer['securityUpdates']['updateStatus']['statusMessage'])
            else:
                labels.append("Unmanaged")

            labels.append(computer['agentVersion'])
            labels.append(computer['displayName'])

            # Specific metrics
            attlabels = labels[:]
            attlabels.append("info")
            result['Metrics'].append([attlabels, 1])

            attlabels = labels[:]
            attlabels.append("rule_count")
            result['Metrics'].append([attlabels, rule_count])

            attlabels = labels[:]
            attlabels.append("severity_low")
            result['Metrics'].append([attlabels, severity_low])

            attlabels = labels[:]
            attlabels.append("severity_medium")
            result['Metrics'].append([attlabels, severity_medium])

            attlabels = labels[:]
            attlabels.append("severity_high")
            result['Metrics'].append([attlabels, severity_high])

            attlabels = labels[:]
            attlabels.append("severity_crititcal")
            result['Metrics'].append([attlabels, severity_crititcal])

            attlabels = labels[:]
            attlabels.append("type_vulnerability")
            result['Metrics'].append([attlabels, type_vulnerability])

            attlabels = labels[:]
            attlabels.append("type_exploit")
            result['Metrics'].append([attlabels, type_exploit])

    # Return results
    _LOGGER.debug("Metrics collected: {}".format(result))
    return result

if __name__ == '__main__':
    collect()