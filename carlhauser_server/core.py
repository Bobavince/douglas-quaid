#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ==================== ------ STD LIBRARIES ------- ====================
import sys, os
import logging.config
import argparse
import pathlib
import subprocess
import datetime
import time

# ==================== ------ PERSONAL LIBRARIES ------- ====================
sys.path.append(os.path.abspath(os.path.pardir))
from carlhauser_server.Helpers.environment_variable import get_homedir

import carlhauser_server.Helpers.database_start_stop as database_start_stop
import carlhauser_server.Configuration.database_conf as database_conf

from carlhauser_server.API.carlhauser_server import FlaskAppWrapper
import carlhauser_server.Configuration.webservice_conf as webservice_conf

import carlhauser_server.Configuration.feature_extractor_conf as feature_extractor_conf

import carlhauser_server.DatabaseAccessor.database_adder as database_adder
import carlhauser_server.Helpers.json_import_export as json_import_export
import carlhauser_server.Helpers.worker_start_stop as worker_start_stop

# ==================== ------ PREPARATION ------- ====================
# load the logging configuration
logconfig_path = (get_homedir() / pathlib.Path("carlhauser_server", "logging.ini")).resolve()
logging.config.fileConfig(str(logconfig_path))


# ==================== ------ LAUNCHER ------- ====================
class launcher_handler():
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def launch(self):
        # Create configuration
        db_conf = database_conf.Default_database_conf()
        ws_conf = webservice_conf.Default_webservice_conf()
        fe_conf = feature_extractor_conf.Default_feature_extractor_conf()

        # Launch elements
        self.start_database(db_conf)
        self.start_adder_workers(db_conf)
        self.start_requester_workers(db_conf)
        self.start_feature_workers(db_conf, fe_conf)
        self.check_worker(db_conf)

        time.sleep(5)
        self.start_webservice(ws_conf, db_conf)

        # If the webservice is down, then we want to shutdown everything
        self.shutdown_workers(db_conf)
        self.check_worker(db_conf)

    # ==================== ------ DB ------- ====================

    def start_database(self, db_conf):
        self.logger.info(f"Launching redis database (x2) ...")

        # Create database handler from configuration file
        db_handler = database_start_stop.Database_StartStop(conf=db_conf)

        # Launch redis db (cache and storage)
        db_handler.launch_all_redis()

    # ==================== ------ DB WORKERS ------- ====================

    def start_adder_workers(self, db_conf):
        self.logger.info(f"Launching to_add worker (x{db_conf.ADDER_WORKER_NB}) ...")

        # Get the Singleton instance of worker handler and start N workers
        worker_handler = worker_start_stop.Worker_StartStop(db_conf)
        worker_handler.start_n_adder_worker(db_conf=db_conf, nb=db_conf.ADDER_WORKER_NB)

    def start_requester_workers(self, db_conf):
        self.logger.info(f"Launching to_request worker (x{db_conf.REQUESTER_WORKER_NB}) ...")

        # Get the Singleton instance of worker handler and start N workers
        worker_handler = worker_start_stop.Worker_StartStop(db_conf)
        worker_handler.start_n_requester_worker(db_conf=db_conf, nb=db_conf.REQUESTER_WORKER_NB)

    # ==================== ------ FEATURE WORKERS ------- ====================

    def start_feature_workers(self, db_conf, fe_conf):
        self.logger.info(f"Launching feature worker (x{fe_conf.FEATURE_ADDER_WORKER_NB} + x{fe_conf.FEATURE_REQUEST_WORKER_NB}) ...")

        # Get the Singleton instance of worker handler and start N workers
        worker_handler = worker_start_stop.Worker_StartStop(db_conf)
        worker_handler.start_n_feature_adder_worker(db_conf=db_conf, fe_conf=fe_conf, nb=fe_conf.FEATURE_ADDER_WORKER_NB)
        worker_handler.start_n_feature_request_worker(db_conf=db_conf, fe_conf=fe_conf, nb=fe_conf.FEATURE_REQUEST_WORKER_NB)

    # ==================== ------ UTLITIES ON WORKERS ------- ====================

    def check_worker(self, db_conf):
        self.logger.info(f"Checking for workers ...")
        worker_handler = worker_start_stop.Worker_StartStop(db_conf)
        worker_handler.check_worker()

    def shutdown_workers(self, db_conf):
        self.logger.info(f"Requesting workers to stop ...")
        worker_handler = worker_start_stop.Worker_StartStop(db_conf)
        worker_handler.request_shutdown()

    # ==================== ------ WEBSERVICE ------- ====================

    def start_webservice(self, ws_conf, db_conf):
        self.logger.info(f"Launching webservice ...")

        # Create configuration file
        ws_conf.CERT_FILE = pathlib.Path(ws_conf.CERT_FILE).resolve()
        ws_conf.KEY_FILE = pathlib.Path(ws_conf.KEY_FILE).resolve()

        # Create Flask endpoint from configuration files
        api = FlaskAppWrapper('api', conf=ws_conf, db_conf=db_conf)
        api.add_all_endpoints()

        # Run Flask API endpoint
        api.run()  # debug=True


if __name__ == '__main__':
    try :
        launcher = launcher_handler()
        launcher.launch()
    except KeyboardInterrupt:
        print('Interrupted detected')
        try:
            #TODO : Handle interrupt and shutdown, and clean ...
            sys.exit(0)
        except SystemExit:
            os._exit(0)

'''
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Manage backend DBs.')
    parser.add_argument("--start", action='store_true', default=False, help="Start all")
    parser.add_argument("--stop", action='store_true', default=False, help="Stop all")
    parser.add_argument("--status", action='store_true', default=True, help="Show status")
    args = parser.parse_args()

    if args.start:
        launch_all()
    if args.stop:
        stop_all()
    if not args.stop and args.status:
        check_all()
'''
