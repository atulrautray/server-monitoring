# Server Monitoring Script

Python script that helps monitor different services deployed on a cluster of servers.

## Description

client.py is a python script that makes HTTP requests to a local server running on a specified port (mocked by server.py), retrieves information about servers, and processes the data to determine the health status of each server.

The script uses the requests library to make GET requests to the server, and the json library to parse the responses. The multiprocessing library is used to perform the server details retrieval in parallel. The pandas library is used to create a DataFrame and calculate the mean values of the servers' properties. The argparse library is used to parse command line arguments.

The script defines several functions:

* get_servers: makes a GET request to the server's /servers endpoint, and returns a list of servers.
* get_server_details: makes a GET request to the server's /<server_ip\> endpoint, and returns a dictionary of details about the server.
* get_all_data: retrieves the details of all servers in parallel, and saves the results to a JSON file.
* check_data_validity: checks the last modified time of the JSON file, and returns whether the data is still considered valid.
* print_services: prints the information about all servers in tabular format.
* get_service_avg: calculates the mean values of the servers' properties grouped by service, and prints the result.
* find_unhealthy: finds services with less that 2 Healthy servers and prints the result.

The script also defines some global variables like GET_REQ_HEADER, DATA_JSON_PATH, FREQ, HEALTH_COUNT, CPU_LIMIT and MEMORY_LIMIT.
* GET_REQ_HEADER is a dictionary of headers that is sent with the GET request to the server.
* DATA_JSON_PATH is a string that contains the path of the JSON file that is used to store the servers' details.
* FREQ is an integer that represents the age of data allowed in minutes.
* HEALTH_COUNT is an integer that declares the minimum nuber of servers needed for a service to be healthy
* CPU_LIMIT is an integer denoting healthy cpu usage limit
* MEMORY_LIMIT is an integer denoting healthy memory usage limit

## Running the Project

### Dependencies

* requests
* pandas

### Executing program

* To run the server:
```
python3 server.py <port>
```

* To run the client (port is required, rest of the flags are optional):
```
python3 client.py --port <port> --printservers --avg --unhealthyservices --service <service name>
```