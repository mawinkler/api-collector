"""Example metrics collector for Astro Weather

This script is a pluggable module for the api-collector. It collects
information from 7Timer by it's RESTful API, calculates some
metrics and creates a dictionary which is feedede into Prometheus
by the api-collector.

The metrics calculated reflect the expected astro view conditions of
this night based on cloud coverage, seeing and atmospheric transparency.

This file has one single funtion collect(), which is called by the
api-collector. For testing purposes, one can directly run the collector
with python3 <FILENAME>. You need to ensure the presence of the
credentials in the given directory.
"""

import json
import requests
import time
from datetime import datetime, timedelta
import logging

_LOGGER = logging.getLogger(__name__)

LONGITUDE=11.985
LATITUDE=48.313

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
        "CounterMetricFamilyHelpText": "AstroWeather this Nights Cloudcoverage",
        "CounterMetricFamilyLabels": ['timepoint'],
        "Metrics": []
    }

    # API query and response parsing here
    url = "http://www.7timer.info/bin/api.pl?lon=" + str(LONGITUDE) + "&lat=" + str(LATITUDE) + "&product=astro&output=json"
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
        if response['message'] == "Invalid API Key":
            raise ValueError("Invalid API Key")

    # Timezone Offset is currently calculated based on system time
    offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
    offset = offset / 60 / 60 * (-1)

    _LOGGER.debug("Timezone offset: " + str(offset))

    init = datetime.strptime(response['init'], "%Y%m%d%H") + timedelta(hours=offset)
    
    # Calculate your metrics
    if len(response['dataseries']) > 0:
        for forecast in response['dataseries']:
            forecast_time = init + timedelta(hours=forecast['timepoint'])

            tomorrow_3am = (datetime.now() + timedelta(days=1)).replace(hour=3, minute=0, second=0, microsecond=0)
            if  forecast_time > tomorrow_3am:
                continue

            hour_of_day = forecast_time.hour % 24
            if hour_of_day > 3 and hour_of_day < 19:
                continue

            cloudcover = forecast["cloudcover"]
            seeing = forecast["seeing"]
            transparency = forecast["transparency"]

            # Calculate Condition
            # round( (3*cloudcover + seeing + transparency) / (3*9+8+8) * 5)
            condition = round(
                (3 * cloudcover + seeing + transparency) / 43 * 5,
            )
            
            labels = []
            labels.append(str(forecast_time.strftime("%H:%M")))
            metric = condition

            # Add a single metric
            result['Metrics'].append([labels, metric])

    _LOGGER.debug(result)
    # Return results
    return result

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
    collect()