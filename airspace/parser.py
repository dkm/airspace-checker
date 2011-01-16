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


##
## The following RE are used to parse the OpenAir file
## It is rather weak compared to a real grammar.
## An antrl3 grammar is available in grammar/OpenAir.g
## But having some problems with antlr 3.0.1 and unable to
## install antlr 3.2, I decided to switch to a simpler
## but still ok solution. 
##

import re

import shapely

import osgeo.ogr
import osgeo.osr
import os
import os.path
import sys
import math

from rtree import Rtree

import util
import zone

aclass = re.compile('^AC (?P<aclass>R|Q|P|A|B|C|D|GP|CTR|W)$', re.IGNORECASE)

coords = '(?P<lat%s>\d+:\d+(:|\.)\d+)\s?(?P<d1%s>N|S) (?P<lon%s>\d+:\d+(:|\.)\d+)\s?(?P<d2%s>E|W)'

#
# F : Feet.
# AGL : Above Ground Level
# AMSL: Above Mean Sea Level
# SFC: Surface
# UNL: Unlimited height
# FL: Flight Level (x100 = Feets)

alti = '(((?P<height>\d+)F )?(?P<ref>AGL|AMSL|SFC|UNL))|(FL(?P<fl>\d+))\s*$'

aceil = re.compile('^AH ' + alti, re.IGNORECASE)
afloor = re.compile('^AL ' + alti, re.IGNORECASE)
aname = re.compile('^AN (?P<name>.*)\s*$', re.IGNORECASE)

poly_point = re.compile('^DP ' + coords % ("","","","") + '\s*$', re.IGNORECASE)
circle = re.compile('^DC (?P<radius>\d+(\.\d+)?)\s*$', re.IGNORECASE)

arc_coord = re.compile('^DB ' + coords % ("1","1","1","1") +','+ coords  % ("2","2","2","2") + '\s*$', re.IGNORECASE)
set_direction = re.compile('^V D=(?P<direction>\+|-)\s*$', re.IGNORECASE)
set_center = re.compile('^V X=' + coords % ("","","","") + '\s*$', re.IGNORECASE)
set_width = re.compile('^V W=(?P<width>\d+\.\d+)\s*$', re.IGNORECASE)
set_zoom = re.compile('^V Z=(?P<zoom>\d+\.\d+)\s*$', re.IGNORECASE)

airway = re.compile('^DY ' + coords %  ("","","","") + '\s*$', re.IGNORECASE)

re_lines = [aclass,
            aceil,
            afloor,
            aname,
            arc_coord,
            circle,
            poly_point,
            set_direction,
            set_center,
            set_width,
            set_zoom,
            airway]

class ZoneIndex:
    def __init__(self):
        self.list = []
        self.rtree_idx = Rtree()
        self.idx = 0

    def append(self, zone):
        zone.finish()
        minLong,maxLong,minLat,maxLat =  zone.poly.GetEnvelope()
        bbox = (minLong, minLat, maxLong, maxLat)
##        print "bbox: ", bbox
        self.rtree_idx.add(self.idx, bbox)
        self.idx += 1
        self.list.append(zone)
    
    def __len__(self):
        return len(self.list)

    def intersection(self, bbox):
        minLong,maxLong,minLat,maxLat = bbox
        n_bbox = (minLong, minLat, maxLong, maxLat)
        return [self.list[i] for i in self.rtree_idx.intersection(n_bbox)]

class OAIRParser:
    """
    A OAIRParser object is used to parse an OpenAir formated
    text file into corresponding OGR objects.
    """

    zones = ZoneIndex()
    current_zone = None

    def __init__(self, fname):
        """
        Creates a Parser object bound to file named 'fname'
        """

        self.fname = fname

        #
        # parses actions are function with the following 
        # interface: f(match object, text line)
        # that are called when a line in the 
        # input file matches. There should be one action
        # per regular expression in the re_lines array
        
        self.parse_actions = { aclass: self.aclass_action,
                               aceil: self.aceil_action,
                               afloor: self.afloor_action,
                               aname : self.aname_action,
                               circle : self.circle_action,
                               arc_coord : self.arc_coord_action,
                               poly_point: self.poly_point_action,
                               set_direction: self.set_direction_action,
                               set_center: self.set_center_action,
                               set_zoom: self.set_zoom_action,
                               set_width: self.set_width_action,
                               airway : self.airway_action}

    # beware that the code makes the asumption that
    # a name field always follows a class field:
    # example:
    # AC ....
    # AN ....

    def aname_action(self, line, m):
        """
        Creates a new Zone object.
        Triggered when a 'AN ...' line is matched
        """
        self.current_zone.name = m.group('name')

    def aclass_action(self, line, m):
        """
        Sets the class for the current zone being parsed.
        Triggered when a 'AC ...' line is matched
        """

        if self.current_zone != None:
            self.zones.append(self.current_zone)
        self.current_zone = zone.Zone(aclass=m.group('aclass'))

    def aceil_action(self, line, m):
        """
        Sets the ceiling altitude for the current zone being parsed.
        Triggered when a 'AH ...' line is matched
        """
        if m.group('height'):
            self.current_zone.ceil = int(m.group('height'))
            self.current_zone.ceil_ref = m.group('ref')
        elif m.group('fl'):
            self.current_zone.ceil = m.group('fl')
            self.current_zone.ceil_ref = "FL"
        else:
            self.current_zone.ceil = -1
            self.current_zone.ceil_ref = m.group('ref')

    def afloor_action(self, line, m):
        """
        Sets the floor altitude for the current zone being parsed.
        Triggered when a 'AL ...' line is matched
        """

        if m.group('height'):
            self.current_zone.floor = int(m.group('height'))
            self.current_zone.floor_ref = m.group('ref')
        elif m.group('fl'):
            self.current_zone.floor = m.group('fl')
            self.current_zone.floor_ref = "FL"
        else:
            self.current_zone.floor = -1
            self.current_zone.floor_ref = m.group('ref')

    def arc_coord_action(self, line, m):
        """
        Adds an arc to the current polygon for the zone being parsed.
        Triggered when a 'DB ...' line is matched.
        """
        if (self.current_zone.__class__.__name__ == "Zone"):
            self.current_zone = zone.PolyZone(self.current_zone)

        (lat1, lon1) = util.latlon_to_deg(m, 1)
        (lat2, lon2) = util.latlon_to_deg(m, 2)

        p1 = util.createPoint(latitude=lat1, longitude=lon1)
        p2 = util.createPoint(latitude=lat2, longitude=lon2)
        
        buf = util.getCircle(self.current_zone.current_center, p1)
        arcpoints = util.pointsOnArc(buf.GetGeometryRef(0), p1, p2, 
                                     direction="cw")

        for arcpoint in arcpoints:
            self.current_zone.addPoint(arcpoint[0], arcpoint[1], arcpoint[2])

                
    def circle_action(self, line, m):
        """
        Creates a circle for the zone being parsed.
        Triggered when a 'DC ...' line is matched
        """
        rad = float(m.group('radius'))
        buf = util.getCircleByRadius(self.current_zone.current_center, rad*1852)
        if (self.current_zone.__class__.__name__ == "Zone"):
            self.current_zone = zone.CircleZone(self.current_zone)
        self.current_zone.poly = buf

    def poly_point_action(self, line, m):
        """
        Adds a point to the polygon for the zone being parsed.
        Triggered when a 'DP ...' line is matched
        """
        (lat, lon) = util.latlon_to_deg(m)
        if (self.current_zone.__class__.__name__ == "Zone"):
            self.current_zone = zone.PolyZone(self.current_zone)

        self.current_zone.addPoint(lon, lat)

    def set_direction_action(self, line, m):
        """
        Sets the direction for the arcs.
        Triggered when a 'V D=...' line is matched
        """
        direct = m.group('direction')
        if direct == "+":
            self.current_zone.direct = "cw"
        elif direct == "-":
            self.current_zone.direct = "ccw"

    def set_center_action(self, line, m):
        """
        Sets the center for circles and arc.
        Triggered when a 'V X= ...' line is matched
        """

        lat, lon = util.latlon_to_deg(m)

        self.current_zone.current_center = util.createPoint(longitude=lon, latitude=lat)

    def set_zoom_action(self, line, m):
        """
        NOT IMPLEMENTED.
        Sets the zoom level.
        Triggered when a 'V Z=...' line is matched
        """
        pass

    def set_width_action(self, line, m):
        """
        NOT IMPLEMENTED.
        Sets width.
        Triggered when a 'V W=...' line is matched
        """
        pass

    def airway_action(self, line, m):
        """
        NOT IMPLEMENTED
        Adds a segment to an airway.
        Triggered when a 'DY ...' line is matched
        """
        pass
            
    def parse(self):
        """
        Do the actual parsing.
        Parsed zones are available in the 'zones' attribute.
        """

        fin = open(self.fname)
        for l in fin.xreadlines():
            for r in re_lines:
                m = r.match(l)
                if m != None:
                    self.parse_actions[r](l,m)
        
        if self.current_zone != None:
            self.zones.append(self.current_zone)
