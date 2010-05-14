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
import util

class Zone:
    """
    Describe a zone
    """
    
    def __init__(self, name=None, aclass=None):
        """
        The name of the Zone
        """
        self.name = name

        """
        The ceiling of the zone
        """
        self.ceil = None

        """
        The floor of the zone
        """
        self.floor = None

        """
        The class of the zone
        """
        self.aclass = None

        self.current_center = None
        self.direction = "cw"

        self.finish_need_to_close_ring = False
        self.poly = None
        self.ring = None
        
    def addPoint(self, x, y):
        """
        Adds a point to the polygon describing the zone
        """
        if self.ring == None:
            self.ring = osgeo.ogr.Geometry(osgeo.ogr.wkbLinearRing)

        self.finish_need_to_close_ring = True

        self.ring.AddPoint(x,y)

    def finish(self):
        """
        Closes the zone and returns the polygon
        """
        if self.finish_need_to_close_ring:
            self.ring.CloseRings()
            self.poly = osgeo.ogr.Geometry(osgeo.ogr.wkbPolygon)
            self.poly.AddGeometry(self.ring)
            self.poly.AssignSpatialReference(util.latlong)
            print "finished,", self.ring.GetPointCount()

        return self.poly
