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
import traceback

import altiresolver

class ZoneException(Exception):
    pass

class IgnoreZoneException(ZoneException):
    def __init__(self, reason):
        self.reason = reason

    def __str__(self):
        return self.reason

class Zone:
    """
    Describe a zone
    """
    

    """
    The ceiling of the zone
    """
    ceil = None
    ceil_ref = None
    
    """
    The floor of the zone
    """
    floor = None
    floor_ref = None
    
    """
    The class of the zone
    """
    aclass = None
    
    current_center = None
    direction = "cw"
    altitude_resolver = altiresolver.OssimResolverWrapper("/media/e35706d4-062b-4652-8c53-0a853d4dcb3b/storage/unzipe/ossim_preferences_template")
##    altitude_resolver = altiresolver.OssimResolverProcess("/mnt/supra-fat/dkm/marble-srtm-data/unzipe/ossim_preferences_template")
    #altiresolver.GeoNamesResolver(datasource="gtopo30")

    def __init__(self, name=None, aclass=None):
        """
        The name of the Zone
        """
        self.name = name

        self.current_center = None
        self.direction = "cw"

    def getCeilAtPoint(self, lat, lon):
        if self.ceil_ref == "FL":
            return self.ceil * 100
        elif self.ceil_ref == "SFC":
            # not 100% true, as SFC is not at 0 MSL.
            # approx valid when flying outside of a cave.
            #
            # /!\ does not really make sense to use SFC for the ceiling...
            return 0
        elif self.ceil_ref == "UNL":
            return sys.maxint
        elif self.ceil_ref == "AMSL":
            return self.ceil
        elif self.ceil_ref == "AGL":
            ground_level = self.altitude_resolver.getGroundLevelAt(lat,lon)
            return self.ceil + ground_level

    def getFloorAtPoint(self, lat, lon):
        if self.floor_ref == "FL":
            return self.floor * 100
        elif self.floor_ref == "SFC":
            # not 100% true, as SFC is not at 0 MSL.
            # approx valid when flying outside of a cave.
            return 0
        elif self.floor_ref == "UNL":
            # does not make sense to use UNL as floor.
            return sys.maxint
        elif self.floor_ref == "AMSL":
            return self.floor
        elif self.floor_ref == "AGL":
            ground_level = self.altitude_resolver.getGroundLevelAt(lat,lon)
            return self.floor + ground_level


    def duplicate(self, otherzone):
        self.ceil = otherzone.ceil
        self.ceil_ref = otherzone.ceil_ref

        self.floor = otherzone.floor
        self.floor_ref = otherzone.floor_ref

        self.current_center = otherzone.current_center
        self.direction = otherzone.direction

    def finish(self):
        raise ZoneException()

class PolyZone(Zone):

    def __init__(self, zone):
        Zone.__init__(self, zone.name, zone.aclass)
        self.duplicate(zone)

        self.poly = osgeo.ogr.Geometry(osgeo.ogr.wkbPolygon)
        self.ring = None

    def addPoint(self, x, y, z=0):
        """
        Adds a point to the polygon describing the zone
        """
        if self.ring == None:
            self.ring = osgeo.ogr.Geometry(osgeo.ogr.wkbLinearRing)

        self.ring.AddPoint(x,y,z)

    def finish(self):
        """
        Closes the zone and returns the polygon
        """
        if self.ring :
            if self.ring.GetPointCount() == 2:
                raise IgnoreZoneException("Only 2 points on polygon, most certainly a segment, discarding it.")
            
            
            self.ring.CloseRings()
            self.poly.AddGeometry(self.ring)
            self.ring = None
        else:
            raise ZoneException()

        return self.poly


class CircleZone(Zone):

    def __init__(self, zone):
        Zone.__init__(self, zone.name, zone.aclass)
        self.duplicate(zone)
        self.poly = None

    def finish(self):
        return self.poly
