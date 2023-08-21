# PostgreSQL Performance Farm

This repository contains the code for the PostgreSQL Performance Farm, aiming to collect PostgreSQL performance data through a Python script, outputting results on a JSON file. Results are then being sent the REST API and can be browsed through a Website.

For detailed explanations about functioning of the script, check the documentation file in `docs/client.md`.



## Client

The Client is a Python script that clones the PostgreSQL source code from a specific branch and creates a temporary PostgreSQL cluster. Then runs pgbench and collect the results and finally uploads the results to the API server. The source code is in the `client` directory.

### Requirements

The Client can be run in macOS or any Linux based distribution using Python 3.6 (or later).

Below are the system requirements.

- collectd 5.9 (or later)
- bison 2.3 (or later)
- flex 2.5 (or later)
- zlib1g-dev
- libreadline-dev

It is tested on PostgreSQL 11, 12, 13, and 14.

### Installation

The Client code can work without virtual environment, yet requires the installation of a few additional packages. Remember not to run as root!

```bash
cd pgperffarm
$ pip3 install -r requirements.txt
```

Next, copy `settings.py` and edit the `settings_local.py` file to fit your needs.

The machine `secret` is obtained registering the machine in the website, therefore each test result will belong to the machine with the secret specified in the settings file.

Specifically, it is possible to set:

* Whether to test locally or upload results to the server
* When uploading whether to user basic authentication option or not
* Whether to call `git pull` at every execution
* Path in which to clone, install and collect output (should have non-superuser access)
* Postgres configuration
* Database name for PgBench (must exist)
* PgBench configuration or set of configurations (two of the same configurations are allowed, as long as all the parameters are integers and clients are arrays)
* TPC-H scale factor
* Modes to run the benchmark, running only PgBench, only TPC-H，or both.


In order to generate the TPC-h data, the [TPC-H tool](https://www.tpc.org/tpc_documents_current_versions/download_programs/tools-download-request5.asp?bm_type=TPC-H&bm_vers=3.0.0&mode=CURRENT-ONLY) is needed to be downloaded, 
unzipped to the folder `tpch-h` in the project root and renamed the inner folder `TPC-H_Toolsv*` to `TPC-H_Tools`.
so that the file structure looks like
```
- tpc-h
    - TPC-H_Tools
    - tpc-h_v3.*.docx
    - tpc-h_v3.*.pdf
```

And edit some files in the dbgen to suit your system. Taking linux as an example, you need to update the following lines in the makefile:
```
CC       = gcc
DATABASE = POSTGRESQL
MACHINE  = LINUX
WORKLOAD = TPCH
```

And add following lines to `tpcd.h`:
```c
#ifdef POSTGRESQL
#define GEN_QUERY_PLAN  "EXPLAIN"      
#define START_TRAN      "BEGIN TRANSACTION"
#define END_TRAN        "COMMIT;"
#define SET_OUTPUT      ""
#define SET_ROWCOUNT    "LIMIT %d\n"
#define SET_DBASE       ""
#endif /* VECTORWISE */
```

After setting up, run the Client script

```bash
$ python3 perffarm-client.py
```

The Client script clones and runs tests on each of the branches specified above, and uploads them automatically after each iteration is complete if the appropriate flag is set.

If mistakes occur, the \$PGDATA directory is removed and it should be safe to re-run again. However, if there are still problems, it is advised to just remove the whole ​\$BASE_PATH.

Note that there may be issues with directories, since each system has its own defaults and permissions. If you encounter any problem, feel free to open an issue.

### Uploading

These steps are needed to upload benchmark results to the REST API.

Login using PostgreSQL community login to the Performance Farm website.

Go to your profile page and create a machine and copy the machine secret and paste it in the `settings_local.py` and set `AUTOMATIC_UPLOAD` to True.

After the machine gets approved, you will be able to upload benchmark results.


### Automation

To set up automatic execution of the Client, it is advised to create a cron job for it.

```bash
$ crontab -e
```

Below is an example crontab configuration that executes the Client every 2 hours. The username should be the same as $PGUSER.

```
USER=username
0 */2 * * * python3 /path/to/pgperffarm/client/perffarm-client.py >> /path/to/perffarm.log 2>&1
```

A reasonable interval for the cron job would be 2-6 hours, roughly as often as the MASTER branch is being updated. 



## How  to run custom tests on pgbench

The folder of custom pgbench is located in benchmark/custom_queries. The folder format is as follows:

```
- custom_queries
    - custom1
        - init.sql   # The initialization script of the database
        - parameters.py   # The parameters of the custom test
        - scripts/
            - script1.sql   # The custom test script 
            - script2.10.sql   # The custom test script with 10 weight
    - custom2
        - init.sql
        - parameters.py
        - scripts/
            - script1.sql
            - script2.10.sql
    - ...
```

The parameters.py file is used to set the parameters of the custom test.

```
PGBENCH_CUSTOM_CONFIG = [
    {
        'iterations': 1,
        'duration': 10,
        'scale': 5,
        'clients': [1],
        'read_only': False,
    },
]

```
#### To run the custom test, you need to change the path of the parameters.py in the perffarm-client.py file  and pgbench_custom.py file
#### Add MODE=pgbench_custom in the settings_local.py file

```