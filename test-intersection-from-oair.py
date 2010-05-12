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

import osgeo.ogr
import osgeo.osr
import os
import os.path
import sys

import airspace.parser
import airspace.util
import airspace.track

p = airspace.parser.OAIRParser(sys.argv[1])

p.parse()

gpxtrack = airspace.track.loadGpx('test.gpx')

print gpxtrack.GetPointCount()

found_an_intersection = 0

for zone in p.zones:
    poly = zone.finish()
    if poly.Intersect(gpxtrack):
        found_an_intersection += 1
        print "Intersection of ", zone.name

if found_an_intersection > 0:
    print "Found %d intersections." % found_an_intersection
else:
    print "No intersection found."
