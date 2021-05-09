"""Example metrics collector for Astro Weather

This script is a pluggable module for the api-collector. It collects
information from 7Timer by it's RESTful API, calculates some
metrics and creates a dictionary which is feedede into Prometheus
by the api-collector.

This file has one single funtion collect(), which is called by the
api-collector. For testing purposes, one can directly run the collector
with python3 <FILENAME>. You need to ensure the presence of the
credentials in the given directory.
"""

import json
import requests
import pprint
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

    # Define your metrics here
    result = {
        "CounterMetricFamilyName": "astroweather",
        "CounterMetricFamilyHelpText": "AstroWeather Cloudcoverage",
        "CounterMetricFamilyLabels": ['timepoint'],
        "Metrics": []
    }

    # API query and response parsing here
    url = "http://www.7timer.info/bin/api.pl?lon=11.985&lat=48.313&product=astro&output=json"
    data = {}
    post_header = {
        "Content-type": "application/json",
    }
    resp = requests.get(
        url, data=json.dumps(data), headers=post_header, verify=True
    )
    plain = str(resp.text).replace("\n", " ")
    response = json.loads(plain)
                
    # Error handling
    if "message" in response:
        if response["message"] == "Invalid API Key":
            raise ValueError("Invalid API Key")

    # Calculate your metrics
    if len(response["dataseries"]) > 0:
        for forecast in response["dataseries"]:
            labels = []
            labels.append(str(forecast["timepoint"]))
            metric = forecast["cloudcover"]
            if not isinstance(metric, int):
                metric = 0

            print([labels, metric])
            # Add a single metric
            result['Metrics'].append([labels, metric])

    pprint.pprint(result)
    # Return results
    return result


if __name__ == '__main__':
    collect()