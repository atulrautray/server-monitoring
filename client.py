#!/usr/bin/env python3

import argparse
import json
import requests
import pandas as pd
import multiprocessing
import os
from datetime import datetime, timedelta
import time

GET_REQ_HEADER = {"cpu": "100%", "memory": "53%", "service": "GroupService"}
DATA_JSON_PATH = "server.json"
FREQ = 2  # age of data allowed (minutes)
HEALTH_COUNT = 2  # minimum number of servers required for a service to be healthy
CPU_LIMIT = 80  # cpu usage limit (percentage)
MEMORY_LIMIT = 80  # memory usage limit (percentage)


def get_servers(port: int):
    try:
        req = requests.get(f"http://localhost:{port}/servers", timeout=5)
        req.raise_for_status()
        servers = json.loads(req.text)
    except (
        requests.exceptions.HTTPError,
        requests.exceptions.Timeout,
        json.decoder.JSONDecodeError,
        ConnectionRefusedError,
    ) as e:
        print(f"Error: {e}")
        servers = []
    # print(servers, type(servers))
    return servers


def get_server_details(port: int, server_ip: str):
    try:
        req = requests.get(
            f"http://localhost:{port}/{server_ip}", headers=GET_REQ_HEADER, timeout=5
        )
        req.raise_for_status()
        server_details = req.json()
    except (requests.exceptions.HTTPError, requests.exceptions.Timeout) as e:
        print(f"Error: {e}")
        server_details = {}
    server_details["ip"] = server_ip
    server_details["cpu"] = float(server_details["cpu"].strip('"%'))
    server_details["memory"] = float(server_details["memory"].strip('"%'))
    # print(server_details, type(server_details))
    return server_details


def get_all_data(port: int, servers: list):
    all_details = []
    with multiprocessing.Pool() as pool:
        results = [
            pool.apply_async(get_server_details, (port, server)) for server in servers
        ]
        server_details_list = [r.get() for r in results]

    for server_details in server_details_list:
        server_details["status"] = (
            "Healthy"
            if (
                server_details["cpu"] < CPU_LIMIT
                and server_details["memory"] < MEMORY_LIMIT
            )
            else "Unhealthy"
        )
        all_details.append(server_details)

    with open(DATA_JSON_PATH, "w") as f:
        json.dump(all_details, f)
    return


def check_data_validity():
    try:
        last_modified_time = os.path.getmtime(DATA_JSON_PATH)
    except OSError:
        return False
    last_modified_datetime = datetime.fromtimestamp(last_modified_time)
    current_time = datetime.now()
    if current_time - last_modified_datetime < timedelta(minutes=FREQ):
        return True
    else:
        return False


def print_services(port: int):
    if not check_data_validity():
        get_all_data(port, get_servers(port))
    with open(DATA_JSON_PATH, "r") as json_file:
        data = json.load(json_file)
        for server in data:
            print(
                server["ip"],
                server["cpu"],
                server["memory"],
                server["service"],
                server["status"],
                sep="\t",
            )
    return


def get_service_avg(port: int):
    if not check_data_validity():
        get_all_data(port, get_servers(port))
    with open(DATA_JSON_PATH, "r") as json_file:
        data = json.load(json_file)
        servers_df = pd.DataFrame(data)
    mean = servers_df.groupby("service").mean()
    print(mean)
    return mean


def find_unhealthy(port: int):
    if not check_data_validity():
        get_all_data(port, get_servers(port))
    with open(DATA_JSON_PATH, "r") as json_file:
        data = json.load(json_file)
        servers_df = pd.DataFrame(data)
    health_count = (
        servers_df.groupby("service")["status"]
        .apply(lambda x: (x == "Healthy").sum())
        .reset_index(name="healthy_count")
    )
    unhealthy_services = health_count.query(f"healthy_count < {HEALTH_COUNT}")
    healthy_services = health_count.query(f"healthy_count >= {HEALTH_COUNT}")
    if unhealthy_services.empty:
        print("No unhealthy services")
        return unhealthy_services, healthy_services
    else:
        print(unhealthy_services.to_string(index=False, col_space=15))
        return unhealthy_services, healthy_services


def service_cpu_memory(port: int, service: str):
    if not check_data_validity():
        get_all_data(port, get_servers(port))
    with open(DATA_JSON_PATH, "r") as json_file:
        data = json.load(json_file)
        servers_df = pd.DataFrame(data)
    services = servers_df[servers_df["service"] == service]
    print(services.to_string(index=False, col_space=15))
    return services


def service_cpu_memory_loop(port: int, service: str, refresh: int):
    try:
        while True:
            print(f"{service}")
            service_cpu_memory(port, service)
            print("\n")
            time.sleep(refresh)
    except KeyboardInterrupt:
        print("Exiting")


def main(args):
    start_time = time.perf_counter()
    if args.printservers:
        print_services(args.port)
    if args.avg:
        get_service_avg(args.port)
    if args.unhealthyservices:
        find_unhealthy(args.port)
    if args.service:
        service_cpu_memory_loop(args.port, args.service[0][0], int(args.service[0][1]))
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print("Elapsed time: ", elapsed_time)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This script gets server details, prints them, and also prints average cpu and memory usage of each service details, unhealthy and healthy servers"
    )
    parser.add_argument(
        "--printservers", action="store_true", help="Print details of all servers"
    )
    parser.add_argument(
        "--avg",
        action="store_true",
        help="Print average cpu and memory usage each of service",
    )
    parser.add_argument(
        "--unhealthyservices",
        action="store_true",
        help="Print services with less than two healthy servers",
    )
    parser.add_argument(
        "--service",
        action="append",
        nargs=2,
        metavar=("service", "refresh rate (sec)"),
        help="Print service details in a loop",
    )
    parser.add_argument("--port", type=int, help="Port number", required=True)
    args = parser.parse_args()
    main(args)
