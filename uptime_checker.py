import os
import time
import json
import urllib.request
import boto3

sns = boto3.client("sns")
dynamodb = boto3.resource("dynamodb")
cloudwatch = boto3.client("cloudwatch")

URLS = [u.strip() for u in os.environ["URLS"].split(",") if u.strip()]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]
TABLE_NAME = os.environ["TABLE_NAME"]

table = dynamodb.Table(TABLE_NAME)

def check_url(url: str):
    start = time.time()
    code = None
    error = None

    try:
        req = urllib.request.Request(
            url,
            method="GET",
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; UptimeMonitor/1.0)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            code = resp.getcode()
    except Exception as e:
        error = str(e)

    latency_ms = int((time.time() - start) * 1000)

    # "Reachability" definition:
    # If we got ANY HTTP response code, the site is reachable (UP).
    # Only network/DNS/timeout exceptions count as DOWN.
    status = "UP" if code is not None else "DOWN"

    return status, code, error, latency_ms

def get_last_status(url: str):
    # Get the most recent record for this URL (used to alert only on state change)
    resp = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("url").eq(url),
        ScanIndexForward=False,  # newest first
        Limit=1,
    )
    items = resp.get("Items", [])
    return items[0]["status"] if items else None

def lambda_handler(event, context):
    ts = int(time.time())
    results = []

    for url in URLS:
        prev_status = get_last_status(url)
        status, code, error, latency_ms = check_url(url)

        item = {
            "url": url,
            "timestamp": ts,
            "status": status,
            "statusCode": code if code is not None else -1,
            "latencyMs": latency_ms,
        }
        if error:
            item["error"] = error[:900]

        # Persist to DynamoDB
        table.put_item(Item=item)
        results.append(item)

        # Custom CloudWatch metrics (per URL)
        cloudwatch.put_metric_data(
            Namespace="UptimeMonitor",
            MetricData=[
                {
                    "MetricName": "UptimeStatus",
                    "Dimensions": [{"Name": "Url", "Value": url}],
                    "Timestamp": ts,
                    "Value": 1 if status == "UP" else 0,
                    "Unit": "Count",
                },
                {
                    "MetricName": "LatencyMs",
                    "Dimensions": [{"Name": "Url", "Value": url}],
                    "Timestamp": ts,
                    "Value": latency_ms,
                    "Unit": "Milliseconds",
                },
            ],
        )

        # Alert only on state change: UP->DOWN or DOWN->UP
        if prev_status != status:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=f"Uptime change: {status} - {url}",
                Message=json.dumps(
                    {
                        "url": url,
                        "previousStatus": prev_status,
                        "currentStatus": status,
                        "statusCode": code,
                        "latencyMs": latency_ms,
                        "error": error,
                        "timestamp": ts,
                    },
                    indent=2,
                ),
            )

    return {"ok": True, "checked": len(URLS), "results": results}
