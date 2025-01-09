'''
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

Multithread logging of the THM1176 probe using the pyton API

This is ugly code, very clunky, and does not exit cleanly. But it has the merit of showing how to use the api to get
data and displaying it

Author: Cedric Hugon
Date: 30Apr2018

'''

BACKEND_CHOICE = 'usbtmc'  # or pyVISA

import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(CURRENT_DIR))

import time
import threading

if BACKEND_CHOICE == 'usbtmc':
    import usbtmc as backend
elif BACKEND_CHOICE == 'pyVISA':
    import visa as backend

    rm = backend.ResourceManager()
else:
    print("Unknown backend, exiting...")
    sys.exit()

import matplotlib.pyplot as plt
import numpy as np

if BACKEND_CHOICE == 'usbtmc':
    import pyTHM1176.api.thm_usbtmc_api as thm_api
elif BACKEND_CHOICE == 'pyVISA':
    import pyTHM1176.api.thm_visa_api as thm_api

if __name__ == '__main__':

    duration = 300

    params = {"trigger_type": "periodic", 'block_size': 500, 'period': 1.0 / 2000.0, 'range': '0.1T',
              'average': 1, 'format': 'INTEGER'}

    item_name = ['Bx', 'By', 'Bz', 'Temperature']
    labels = ['Bx', 'By', 'Bz', 'T']
    curve_type = ['F', 'F', 'F', 'T']
    to_show = [True, True, True, False]
    output_file = '~/desktop/test.dat'  # You may want to change this to your desired file

    if BACKEND_CHOICE == 'usbtmc':
        # You may want to have a smarter way of fetching the resource name
        thm = thm_api.Thm1176(backend.list_devices()[0], **params)
    elif BACKEND_CHOICE == 'pyVISA':
        resource = rm.list_resources()[0]
        print("Resource name: {}".format(resource))
        thm_res = rm.open_resource(resource)
        # You may want to have a smarter way of fetching the resource name
        thm = thm_api.Thm1176(thm_res, **params)

    data_stack = []  # list is thread safe

    # Get device id string and print output. This can be used to check communications are OK
    device_id = thm.get_id()
    for key in thm.id_fields:
        print('{}: {}'.format(key, device_id[key]))

    # Start the monitoring thread
    thread = threading.Thread(target=thm.start_acquisition)
    thread.start()

    # Plotting stuff
    # initialize figure

    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    plt.draw()

    plt.pause(5)  # Wait for the monitor to start filling data in
    plotdata = [thm.data_stack[key] for key in item_name]
    timeline = thm.data_stack['Timestamp']

    # Setup colors
    NTemp = curve_type.count('T')
    cmap1 = plt.get_cmap('autumn')
    colors1 = [cmap1(i) for i in np.linspace(0, 1, NTemp)]

    NField = curve_type.count('F')
    cmap2 = plt.get_cmap('winter')
    colors2 = [cmap2(i) for i in np.linspace(0, 1, NField)]

    colors = []
    count1 = 0
    count2 = 0
    for ct in curve_type:
        if ct == 'T':
            colors.append(colors1[count1])
            count1 += 1
        else:
            colors.append(colors2[count2])
            count2 += 1

    # Create the matplotlib lines for each curve
    lines = []
    for k, flag in enumerate(to_show):
        if flag:
            data_to_plot = plotdata[k]
            if curve_type[k] == 'F':
                ln, = ax1.plot(timeline, data_to_plot, label=labels[k], color=colors[k])
            else:
                ln, = ax2.plot(timeline, data_to_plot, label=labels[k], color=colors[k])
            lines.append(ln)

    ax1.legend(lines, labels, loc='best')

    plt.ion()

    time_start = time.time()

    while time.time() - time_start < duration:
        try:
            plt.pause(1)
            plotdata = [thm.data_stack[key] for key in item_name]
            timeline = thm.data_stack['Timestamp']

            count = 0
            for k, flag in enumerate(to_show):
                if flag:
                    lines[count].set_data(timeline, plotdata[k])
                    count += 1

            ax1.relim()
            ax1.autoscale_view()
            ax2.relim()
            ax2.autoscale_view()

            plt.draw()

        except:
            plt.ioff()
            thm.stop = True
            plt.pause(1)
            sys.exit("Done!")

    thm.stop = True

    # This is to keep the figure open when everything is done
    plt.ioff()
    plt.show()
