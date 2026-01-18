#!/usr/bin/env python3
"""
Simple runner to exercise the minimal Vector-style flow on a live Reddit thread.
"""

import argparse
import os
import sys

import requests


def call_api(base_url, method, path, **kwargs):
    url = f"{base_url}{path}"
    response = requests.request(method, url, **kwargs)
    if response.status_code >= 400:
        print(f"[✗] {method} {url} failed: {response.status_code} {response.text}")
        sys.exit(1)
    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Run one live Reddit thread through EchoFix")
    parser.add_argument("url", help="Reddit thread URL")
    parser.add_argument(
        "--base-url",
        default=os.getenv("ECHOFIX_API_URL", "http://localhost:8000"),
        help="EchoFix backend base URL"
    )
    args = parser.parse_args()

    print("[1/4] Ingesting thread")
    ingest = call_api(
        args.base_url,
        "POST",
        "/api/reddit/ingest-url",
        json={"url": args.url}
    )
    print("    Imported:", ingest.get("imported_count"))

    print("[2/4] Refreshing scores")
    refresh = call_api(args.base_url, "POST", "/api/reddit/refresh-scores")
    print("    Pending checked:", refresh.get("pending_checked"), "Ready:", refresh.get("ready"))

    print("[3/4] Auto-processing READY entries")
    ready = call_api(args.base_url, "POST", "/api/pipeline/auto-process-ready")
    print("    Processed IDs:", ready["report"].get("processed_ids"))
    print("    Issues created:", ready["report"].get("created_issue_urls"))
    print("    PRs created:", ready["report"].get("created_pr_urls"))
    print("    Plan paths:", ready["report"].get("plan_paths"))

    print("[4/4] Full report")
    print(ready)


if __name__ == "__main__":
    main()
