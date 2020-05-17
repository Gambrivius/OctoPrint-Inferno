# coding=utf-8
from __future__ import absolute_import

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.

import octoprint.plugin
import octoprint.util
from octoprint.util import RepeatedTimer
import time
import flask
import csv
from datetime import datetime
import os
from simple_pid import PID


class InfernoPlugin(octoprint.plugin.SettingsPlugin,
                    octoprint.plugin.AssetPlugin,
                    octoprint.plugin.TemplatePlugin,
                    octoprint.plugin.StartupPlugin,
                    octoprint.plugin.ShutdownPlugin,
                    octoprint.plugin.SimpleApiPlugin):

    def get_api_commands(self):
        return dict(
            delete_log=[],
            enable=["value"],
            set_point=["value"]
        )
    def on_api_command(self, command, data):
        if command == "delete_log":
            log_file = self.get_plugin_data_folder() + '/temperature_log.txt'
            os.remove (log_file)
            with open(log_file, 'w') as fp:
                pass
        elif command == "enable":
            self._enabled = bool(data["value"])
        elif command == "set_point":
            self._setpoint = float(data["value"])

    def on_api_get(self, request):
        get = request.args.get('get')
        if (get == "variables"):
            data = {"enabled": self._enabled, "setpoint": self._setpoint}
            return flask.json.jsonify (data)
        elif (get == "chart_data"):
            format = request.args.get('format')
            if (format == 'json'):
                log_file = self.get_plugin_data_folder() + '/temperature_log.txt'
                with open (log_file, 'r') as file:
                    reader = csv.reader(file)

                    trace1 = {"x" : [], "y": [], "type": "scatter", "name": "Power %", "yaxis": "y2", "opacity": 0.90, "line": {"color": "green"}}
                    trace2 = {"x" : [], "y": [], "type": "scatter", "name": "Target Temperature", "opacity": 0.50, "line": {"color": "yellow"}}
                    trace3 = {"x" : [], "y": [], "type": "scatter", "name": "Actual Temperature", "line": {"color": "red"}}

                    for row in reader:
                        date_string = row[0]
                        #x = datetime.strptime(date_string, TIMESTAMP_FORMAT)
                        trace1["x"].append (date_string)
                        trace1["y"].append (float(row[1])*100)
                        trace2["x"].append (date_string)
                        if (row[2] != "None"):
                            trace2["y"].append (float(row[2]))
                            trace3["x"].append (date_string)
                        trace3["y"].append (float(row[3]))
                    data = {"data" : [trace1, trace2, trace3]}
                    return flask.json.jsonify (data)
            if (format == 'csv'):
                log_file = self.get_plugin_data_folder() + '/temperature_log.txt'
                return flask.send_file(log_file,
                     mimetype='text/csv',
                     attachment_filename='inferno_log.csv',
                     as_attachment=True)
        return flask.make_response("Not found", 404)

    def on_after_startup(self):
        self.control_init()
        self.control_begin()
    def on_shutdown (self):
        self._control_loop.cancel()


    def get_settings_defaults(self):

        return dict(url= self.get_plugin_data_folder() + '/temperature_log.txt')
    def start_controller(self):
        self._controller = ChamberController(self)
        self._controller.start_loop()



    ##~~ AssetPlugin mixin

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return dict(
            js=["js/inferno.js", "js/plotly-latest.min.js"],
            css=["css/inferno.css"],
            less=["less/inferno.less"]
        )


    ##~~ Softwareupdate hook
    def log_data(self ):

        log_file = self.get_plugin_data_folder() + '/temperature_log.txt'
        with open (log_file, 'a+') as file:
            #x = octoprint.util.get_formatted_datetime (datetime.now())
            x =  datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            y = self._duty_cycle
            y2 = self.target_temperature()
            y3 = self._actual_temperature
            file.write ('%s,%s,%s,%s\n' %(x, y, y2, y3))
            file.close()
            return y

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return dict(
            inferno=dict(
                displayName="Inferno Plugin",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="Gambrivius",
                repo="OctoPrint-Inferno",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/Gambrivius/OctoPrint-Inferno/archive/{target_version}.zip"
            )
        )

    def control_init (self):
        self._enabled = False
        self.pid = PID(1, 0.1, 0.05, setpoint=1)
        self.pid.output_limits = (0, 1)
        self._setpoint = 55
        self._fan_pin = 12
        self._heater_pin = 13
        self._w1_serial = ""
        self._last_log_time = 0
        self._log_interval = 5 # log every n seconds
        self._broadcast_interval = 5
        self._last_broadcast_time = 0
        self._actual_temperature = 0
        self._v = 0
        self._duty_cycle = 0
        self.get_temperature()

    def get_temperature (self):
        # TODO: Read data from one wire
        self._actual_temperature = 25
        if (self._setpoint != 0):
            self._v = self._actual_temperature / self._setpoint
        else:
            self._v = 0

    def control_cycle (self):
        if (self._enabled):
            self._duty_cycle = self.pid (self._v)
        else:
            self._duty_cycle = 0

        # TODO: turn heaters on and off
        time.sleep (2.0)
        self.get_temperature()

        # update logs and clients
        if (time.time()-self._log_interval >= self._last_log_time):
            self._last_log_time = time.time()
            self.log_data()
        if (time.time()-self._broadcast_interval>= self._last_broadcast_time):
            self.broadcast()
    def target_temperature(self):
        if (self._enabled):
            return self._setpoint
        else:
            return None
    def control_cleanup(self):
        self._logger.info ('Control loop cancelled - Cleaing up IOS')
        pass
    def control_disable(self):
        pass
    def control_enable(self):
        pass
    def broadcast (self):
        self._last_broadcast_time = time.time()
        self._plugin_manager.send_plugin_message(self._identifier, dict(actual_temperature=self._actual_temperature,
                                                                        duty_cycle=self._duty_cycle*100,
                                                                        set_point=self.target_temperature()))

    def control_begin (self):
        self._control_loop = RepeatedTimer(0, self.control_cycle, on_finish = self.control_cleanup)
        self._logger.info ('Starting Control Loop')
        self._control_loop.start()

# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Inferno Plugin"

# Starting with OctoPrint 1.4.0 OctoPrint will also support to run under Python 3 in addition to the deprecated
# Python 2. New plugins should make sure to run under both versions for now. Uncomment one of the following
# compatibility flags according to what Python versions your plugin supports!
#__plugin_pythoncompat__ = ">=2.7,<3" # only python 2
#__plugin_pythoncompat__ = ">=3,<4" # only python 3self.updatePlot();
__plugin_pythoncompat__ = ">=2.7,<4" # python 2 and 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = InfernoPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
