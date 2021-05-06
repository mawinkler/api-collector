# import ssl

# ssl._create_default_https_context = ssl._create_unverified_context
# import urllib3
import json
import requests

def collect():
    ws_url=open('/etc/workload-security-credentials/ws_url', 'r').read()
    api_key=open('/etc/workload-security-credentials/api_key', 'r').read()

    result = {}

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

    # Define your metrics here
    result = {
        "CounterMetricFamilyName": "workload_security_computers",
        "CounterMetricFamilyHelpText": "Workload Security Assigned IPS Rules Metrics",
        "CounterMetricFamilyLabels": ['displayName', 'lastIPUsed'],
        "Metrics": []
    }

    # Calculate your metrics
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

            # Add a metric
            result['Metrics'].append({"hostname": computer_name, "ip": str(computer_ip), "metric": computer_rule_count})

    return result


if __name__ == '__main__':
    collect()