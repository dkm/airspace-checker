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

class AltiResolver:
    def getGroundLevelAt(self, lat, lon):
        pass

class GeoNamesResolver(AltiResolver):
    def __init__(self, datasource="gtopo30"):
        self.datasource = datasource

    def getGroundLevelAt(self, lat, lon):
        url = "http://ws.geonames.org/%s?lat=%f&lng=%f" % (self.datasource,
                                                           lat, lon)
        # this is very basic as a check that it is ok.
        # if the http get fails, we should not get a valid float : error raised
        return float(urllib2.urlopen(url).read().strip())
