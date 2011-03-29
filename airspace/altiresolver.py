#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   airspace checker
#   Copyright (C) 2010  Marc Poulhiès
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import urllib2
import error
import subprocess
import ossim

class AltiResolver:
    def getGroundLevelAt(self, lat, lon):
        pass

OSSIM_HEIGHT_EXEC="/usr/bin/ossim-height"

import random

class RandomResolver(AltiResolver):
    def __init__(self, amin=0, amax=5000, var=10):


        self.amin = amin
        self.amax = amax
        self.var = var
        self._last = amin

    def getGroundLevelAt(self, lon, lat):
        self._last += random.randint(-self.var, self.var)
        if self._last > self.amin:
            self._last = self.amin
        elif self._last > self.amax:
            self._last = self.amax
        return self._last

class OssimResolverProcess(AltiResolver):
    def __init__(self, ossim_config):
        self.config = ossim_config

    def getGroundLevelAt(self, lon, lat):
        args = [OSSIM_HEIGHT_EXEC,
                "-P", self.config,
                str(lat), str(lon)]
        
        p = subprocess.Popen(args, stdout=subprocess.PIPE)
        for l in p.stdout.xreadlines():
            if l.startswith("Height above MSL:"):
                return float(l.strip().split(':')[1].strip())

class OssimResolverWrapper(AltiResolver):
    def __init__(self, ossim_config):
        self.config = ossim_config
        ossim.init(self.config)

    def getGroundLevelAt(self, lat, lon):
        r = ossim.height(lat,lon)
        if r:
            return r[0]
        else:
            return None

VALID_GN_SRC=("gtopo30", "astergdem")

class GeoNamesResolver(AltiResolver):
    def __init__(self, datasource="astergdem", debug=False, unit="meter"):
        """
        Valid values for datasource are:
         * gtopo30
         * astergdem : uses gdem data (should be 1° precise, ~30m)
        unit can be foot or meter (default)
        """
        if datasource not in VALID_GN_SRC:
            raise error.ASCException()

        self.unit = unit
        self.debug = debug
        self.datasource = datasource

    def sendRequestForGroundLevel(self, datasource, lon, lat):
        url = "http://ws.geonames.org/%s?lat=%f&lng=%f" % (datasource,
                                                           lat, lon)
        # this is very basic as a check that it is ok.
        # if the http get fails, we should not get a valid float : error raised
        val_meters = float(urllib2.urlopen(url).read().strip())
        if self.unit == "foot":
            val = float(val_meters / 0.30480)
        else:
            val = float(val_meters)
        return val
        
    def getGroundLevelAt(self, lon, lat):
        ret = self.sendRequestForGroundLevel(self.datasource, lon, lat)
        if self.debug:
            for ds in VALID_GN_SRC:
                print "[%s]=" %ds, self.sendRequestForGroundLevel(ds, lon, lat)
        return ret
