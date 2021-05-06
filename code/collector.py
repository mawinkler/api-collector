import ssl

ssl._create_default_https_context = ssl._create_unverified_context
import urllib3

import time
import json
import yaml
import requests
from prometheus_client.core import GaugeMetricFamily, REGISTRY, CounterMetricFamily
from prometheus_client import start_http_server


class CustomCollector(object):
    def __init__(self):
        print("init")
        pass

    def collect(self):
        dsm_url="app.deepsecurity.trendmicro.com:443"
        api_key="E0B772FA-1C18-C615-74AC-7B7E44E5E19E:643B3386-22CC-E6E7-CAAB-479876125D44:2CXw4VOf5UnfN2yEIaa4j3kUCEoVL5lFnXgH2tppRT4="

        url = "https://" + dsm_url + "/api/computers"
        # data = {
        #     "maxItems": 1,
        #     "searchCriteria": [
        #         {"fieldName": "hostName", "stringTest": "equal", "stringValue": hostname}
        #     ],
        # }
        data = {}
        post_header = {
            "Content-type": "application/json",
            "api-secret-key": api_key,
            "api-version": "v1",
        }
        # response = requests.post(
        #     url, data=json.dumps(data), headers=post_header, verify=False
        # ).json()
        response = requests.get(
            url, data=json.dumps(data), headers=post_header, verify=False
        ).json()

        # Error handling
        if "message" in response:
            if response["message"] == "Invalid API Key":
                raise ValueError("Invalid API Key")

        c = CounterMetricFamily("workload_security_computers", 'Workload Security Computer Metrics', labels=['hostname', 'ip'])

        if len(response["computers"]) > 0:
            for computer in response["computers"]:
                computer_name = ""
                computer_rule_count = 0
                computer_ip = ""
                if "ID" in computer:
                    computer_name = computer["displayName"]
                else:
                    computer_name = "(none)"

                computer_ip = str(computer["lastIPUsed"])
                if "ruleIDs" in computer["intrusionPrevention"]:
                    computer_rule_count = len(computer["intrusionPrevention"]["ruleIDs"])
                else:
                    computer_rule_count = 0
            
                c.add_metric([computer_name, str(computer_ip)], computer_rule_count)
        # g = GaugeMetricFamily("MemoryUsage", 'Help text', labels=['instance'])
        # g.add_metric(["instance01.local"], 20)
        # yield g

        # c = CounterMetricFamily("HttpRequests", 'Help text', labels=['app'])
        # c.add_metric(["example"], 2000)
        yield c


if __name__ == '__main__':
    start_http_server(8000)
    REGISTRY.register(CustomCollector())
    while True:
        time.sleep(1)
