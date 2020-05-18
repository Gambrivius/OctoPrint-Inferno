# OctoPrint-Inferno

Inferno is a barebones plugin for control and logging of your 3D printer's heated chamber.  Being barebones, it supports only my intended implementation, because I am too lazy and selfish to implement support for every type of temperature sensor or Raspberry Pi shield.  Maybe that will change in the future, but for now, I hope your implementation matches my own.

This plugin assumes you are using a One-Wire temperature sensor to measure chamber temperature.  It supports two GPIO outputs.  One output is always on when heating is enabled and is intended to control a fan, while the other is pulsed with a duty cycle to precisely control the temperature of your chamber.  I recommend using a transistor switch circuit on your outputs to protect your GPIOs from burning out.  If you're not the electronics type, I'm sure you can find a RaspberryPi shield with outputs meant for driving relays.  

## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/Gambrivius/OctoPrint-Inferno/archive/master.zip

