$(function() {
    function InfernoViewModel(parameters) {
        var self = this;
        this.plot_data = [];
        self.actualTemp = ko.observable (0.0)
        self.dutyCycle = ko.observable (0.0)
        self.setPoint = ko.observable (0.0)
        self.newSetpoint = ko.observable (40.0)
        self.actualTempString = ko.observable("0.0°C");
        self.isEnabled = ko.observable (false)
        self.newSetpoint.subscribe (function (newValue) {
          self.updatePluginSetpoint();
        });
        self.settings = parameters[0];
        // this will hold the URL currently displayed by the iframe
        //self.currentUrl = ko.observable();

        // this will hold the URL entered in the text field
        //self.newUrl = ko.observable();
        self.updatePluginEnabled = function() {
          xhr = new XMLHttpRequest();
          xhr.open ("POST", "api/plugin/inferno", true);
          xhr.setRequestHeader("Content-Type", "application/json");
          var data = JSON.stringify({
            "command": "enable",
            "value": self.isEnabled()
          });
          xhr.send(data);
        }
        self.getValuesFromPlugin = function() {

          $.getJSON("api/plugin/inferno?get=variables", function(response) {
              // Now use this data to update your view models,
              // and Knockout will update your UI automatically
              self.isEnabled(response['enabled']);
              self.newSetpoint(response['setpoint']);
            });

        }
        self.updatePluginSetpoint = function() {
          xhr = new XMLHttpRequest();
          xhr.open ("POST", "api/plugin/inferno", true);
          xhr.setRequestHeader("Content-Type", "application/json");
          var data = JSON.stringify({
            "command": "set_point",
            "value": self.newSetpoint()
          });
          xhr.send(data);
        }
        self.btnDeleteCSV= function() {
          xhr = new XMLHttpRequest();
          xhr.open ("POST", "api/plugin/inferno", true);
          xhr.setRequestHeader("Content-Type", "application/json");
          var data = JSON.stringify({ "command": "delete_log" });
          xhr.send(data);
          this.plot_data = [];
          self.makePlot();
        }
        self.btnToggleControl = function() {
          if (self.isEnabled()) self.isEnabled(false);
          else self.isEnabled(true);
          self.updatePluginEnabled();
        }

        self.btnDownloadCSV= function() {
          window.open('api/plugin/inferno?get=chart_data&format=csv');

        }

        self.updatePlot = function() {
          //$.getJSON("api/plugin/inferno?format=json", function(response) {
              // Now use this data to update your view models,
              // and Knockout will update your UI automatically
          //    this.plot_data = response.data;
          //    Plotly.style('chamber_plot', 'data', this.plot_data);
          //});
          var time = new Date();
          var trace1 = {
            x:  [[time]],
            y: [[self.actualTemp()]]
          }
          var trace2 = {
            x:  [[time]],
            y: [[self.dutyCycle()]]
          }
          var trace3 = {
            x:  [[time]],
            y: [[self.setPoint()]]
          }
          Plotly.extendTraces('chamber_plot', trace1, [0]);
          Plotly.extendTraces('chamber_plot', trace2, [1]);
          Plotly.extendTraces('chamber_plot', trace3, [2]);
        }
        self.makePlot = function() {
          var layout = {
            margin: {
              l: 80,
              r: 80,
              b: 0,
              t: 10,
              pad: 4
            },
            plot_bgcolor:"black",
            paper_bgcolor:"black",
            yaxis: {
              title: 'Temperature °C',
              gridcolor: "#666666",
              titlefont: {
                color: "white"
              },
              tickfont: {
                color: "white"
              }

            },
            yaxis2: {
              title: 'Duty Cycle %',
              titlefont: {color: 'white'},
              tickfont: {color: 'white'},
              overlaying: 'y',
              side: 'right',
              range: [0,100]
            },
            xaxis: {
              gridcolor: "#666666",
              tickfont: {
                color: "white"
              }
            },
            showlegend: true,
            legend: {
              orientation: "h",
              font: {
                color: "white"
              }
            }
          };

          $.getJSON("api/plugin/inferno?get=chart_data&format=json", function(response) {
              // Now use this data to update your view models,
              // and Knockout will update your UI automatically
              this.plot_data = response.data;
              Plotly.newPlot('chamber_plot', this.plot_data, layout);
          });
          //var myJson '{"data":{"type":"scatter","x":["2020-05-16 17:05:05","2020-05-16 17:07:01"],"y":[98,69]}}';
          //var figure = JSON.parse(myJson);
          //Plotly.newPlot('myDiv', figure.data, layout);

        }

        // This will get called before the HelloWorldViewModel gets bound to the DOM, but after its
        // dependencies have already been initialized. It is especially guaranteed that this method
        // gets called _after_ the settings have been retrieved from the OctoPrint backend and thus
        // the SettingsViewModel been properly populated.
        
        self.onStartupComplete = function() {
            self.makePlot();
            self.getValuesFromPlugin();
        }

        self.onDataUpdaterPluginMessage = function (plugin, data) {

          if (typeof plugin == 'undefined'){
            return;
          }

          if (plugin != "inferno") {
            return;
          }

          if (data.hasOwnProperty ("actual_temperature")) {
            self.actualTemp(data['actual_temperature']);
            self.actualTempString(data['actual_temperature']+'°C');

          }
          if (data.hasOwnProperty ("duty_cycle")) {
            self.dutyCycle(data['duty_cycle']);
          }
          if (data.hasOwnProperty ("set_point")) {
            self.setPoint(data['set_point']);
          }
          self.updatePlot();
        }

    }

    // This is how our plugin registers itself with the application, by adding some configuration
    // information to the global variable OCTOPRINT_VIEWMODELS
    OCTOPRINT_VIEWMODELS.push([
        // This is the constructor to call for instantiating the plugin
        InfernoViewModel,

        // This is a list of dependencies to inject into the plugin, the order which you request
        // here is the order in which the dependencies will be injected into your view model upon
        // instantiation via the parameters argument
        ["settingsViewModel"],

        // Finally, this is the list of selectors for all elements we want this view model to be bound to.
        ["#tab_plugin_inferno"]
    ]);

});
