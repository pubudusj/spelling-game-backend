import json
import random


def lambda_handler(event, context):
    unique_results = []
    seen_sks = set()

    for item in event:
        if item is not None:
            sk_value = item["id"]
            if sk_value not in seen_sks:
                unique_results.append(item)
                seen_sks.add(sk_value)

    return unique_results
