# _  __  ____    _   _ 
# | |/ / |  _ \  | \ | |
# | ' /  | |_) | |  \| |
# | . \  |  __/  | |\  |
# |_|\_\ |_|     |_| \_|
# 
# (c) 2018 KPN
# License: MIT license.
# Author: Jan Bogaerts
# 
# sensor names

from kpn_senml.senml_unit import enum


SenmlNames = enum(KPN_SENML_PRESSURE="pressure",
                KPN_SENML_ANGLE="angle",
                KPN_SENML_LENGHT="lenght",
                KPN_SENML_BREADTH="breadth",
                KPN_SENML_HEIGHT="height",
                KPN_SENML_WEIGHT="weight",
                KPN_SENML_THICKNESS="thickness",
                KPN_SENML_DISTANCE="distance",
                KPN_SENML_AREA="area",
                KPN_SENML_VOLUME="volume",
                KPN_SENML_VELOCITY="velocity",
                KPN_SENML_ELECTRICCURRENT="electricCurrent",
                KPN_SENML_ELECTRICPOTENTIAL="electricPotential",
                KPN_SENML_ELECTRICRESISTANCE="electricResistance",
                KPN_SENML_TEMPERATURE="temperature",
                KPN_SENML_ILLUMINANCE="illuminance",
                KPN_SENML_ALTITUDE="altitude",
                KPN_SENML_ACCELERATIONX="accelerationX",
                KPN_SENML_ACCELERATIONY="accelerationY",
                KPN_SENML_ACCELERATIONZ="accelerationZ",
                KPN_SENML_HEADING="heading",
                KPN_SENML_LONGITUDE="longitude",
                KPN_SENML_LATTITUDE="lattitude",
                KPN_SENML_CARBONMONOXIDE="carbonMonoxide",
                KPN_SENML_CARBONDIOXIDE="carbonDioxide",
                KPN_SENML_SOUND="sound",
                KPN_SENML_FREQUENCY="frequency",
                KPN_SENML_BATTERYLEVEL="batteryLevel",
                KPN_SENML_HUMIDITY="humidity")