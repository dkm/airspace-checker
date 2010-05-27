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
print "Parsing..."
p.parse()
print "[OK] %d zones" %len(p.zones)

track = airspace.track.loadSimpleTxt('toto.txt')

print track.GetPointCount()

found_an_intersection = 0

intersected_segs = []

for zone in p.zones:
    poly = zone.finish()
    if poly.Intersect(track):
        found_an_intersection += 1
        print "Intersection with", zone.name
        intersected_segs += (airspace.util.getSubLineStringInZone(track,poly), poly)

if found_an_intersection > 0:
    print "Found %d potential intersections." % found_an_intersection
    true_positive_inters = []
    false_positive_inters = []

    for subtrack,interzone in intersected_segs:
        confirmed = False
        for pt_idx in xrange(subtrack.GetPointCount()):
            lon,lat,alt = subtrack.GetPoint(pt_idx)
            ceil_alt = interzone.getCeilAtPoint(lat,lon)
            floor_alt = interzone.getFloorAtPoint(lat,lon)
            if alt > floor_alt and alt < ceil_alt:
                confirmed = True
                print "%f/%f@%f in zone '%s' (%f/%f)" % (lat,lon,alt,
                                                         interzone.name,
                                                         floor_alt, ceil_alt)
        if confirmed:
            true_positive_inters += (subtrack,interzone)
        else:
            false_positive_inters += (subtrack,interzone)

    print "confirmed inter: %d" % len(true_positive_inters)
    print "false positive inter: %d" % len(false_positive_inters)

else:
    print "No intersection found."


##airspace.util.writeGeometriesToShapeFile(intersected_segs, "test.shp")
