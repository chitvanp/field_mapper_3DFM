"""
Copyright 2018 Hyperfine

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Example of single acquisition with the Metrolab THM1176
Only usbtmc is supported for single acquisition

Author: Cedric Hugon
Date: 12Jan2021
"""

import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(CURRENT_DIR))

import time
import threading

import usbtmc as backend
import pyTHM1176.api.thm_usbtmc_api as thm_api
import numpy as np

params = {"trigger_type": "single", 'range': '0.1T', 'average': 10, 'format': 'ASCII'}


if __name__ == "__main__":

    thm = thm_api.Thm1176(backend.list_devices()[0], **params)
    # Get device id string and print output. This can be used to check communications are OK
    device_id = thm.get_id()
    for key in thm.id_fields:
        print('{}: {}'.format(key, device_id[key]))

    thm.make_measurement(**params)
    print("Measurement is: {}".format(thm.last_reading))
