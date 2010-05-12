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

import re
import osgeo.ogr
import osgeo.osr
import os
import os.path
import sys
import math

##
## The following RE are used to parse the OpenAir file
## It is rather weak compared to a real grammar.
## An antrl3 grammar is available in grammar/OpenAir.g
## But having some problems with antlr 3.0.1 and unable to
## install antlr 3.2, I decided to switch to a simpler
## but still ok solution. 
##

aclass = re.compile('^AC (?P<aclass>R|Q|P|A|B|C|D|GP|CTR|W)$')

coords = '(?P<lat%s>\d+:\d+(:|\.)\d+)\s?(?P<d1%s>N|S) (?P<lon%s>\d+:\d+(:|\.)\d+)\s?(?P<d2%s>E|W)'
alti = '(?P<height>\d+F )?((?P<ref>AGL|AMSL|FL|SFC|UNL)|(?P<fl>FL\d+))$'

aceil = re.compile('^AH ' + alti)
afloor = re.compile('^AL ' + alti)
aname = re.compile('^AN (?P<name>.*)$')

poly_point = re.compile('^DP ' + coords % ("","","","") + '$')
circle = re.compile('^DC (?P<radius>\d+(\.\d+)?)$')

arc_coord = re.compile('^DB ' + coords % ("1","1","1","1") +','+ coords  % ("2","2","2","2") + '$')
set_direction = re.compile('^V D=(?P<direction>\+|-)$')
set_center = re.compile('^V X=' + coords % ("","","","") + '$')
set_width = re.compile('^V W=(?P<width>\d+\.\d+)$')
set_zoom = re.compile('^V Z=(?P<zoom>\d+\.\d+)$')

airway = re.compile('^DY ' + coords %  ("","","","") + '$')

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

        self.ring = None
        
    def addPoint(self, x, y):
        """
        Adds a point to the polygon describing the zone
        """
        if self.ring == None:
            self.ring = osgeo.ogr.Geometry(osgeo.ogr.wkbLinearRing)
        self.ring.AddPoint(x,y)

    def finish(self):
        """
        Closes the zone and returns the polygon
        """
        self.ring.CloseRings()
        poly = osgeo.ogr.Geometry(osgeo.ogr.wkbPolygon)
        poly.AddGeometry(self.ring)
        print "finished,", self.ring.GetPointCount()

        return poly


def getCircle(center, point, quadseg=90):
    """
    Returns a tuple with the polygon buffer and the inner ring.
    Beware that garbage collecting the buffer will garbage collect
    the ring (within the C code, this means segfault)
    The buffer uses 'quadseg' segments for each quarter circle.
    The circle is defined by a 'center' point and another 'point'
    """

    dist = center.Distance(point)
    buf = center.Buffer(dist, quadseg)
    ring = buf.GetGeometryRef(0)

    return (buf,ring)

def getCircleByRadius(center, radius, quadseg):
    """
    Returns a tuple with the polygon buffer and the inner ring.
    Beware that garbage collecting the buffer will garbage collect
    the ring (within the C code, this means segfault)
    The buffer uses 'quadseg' segments for each quarter circle.
    The circle is defined by a 'center' point its radius in nm (nautic mile)
    Beware that this method applies only to WGS84 data as there is a need for
    projection when computing the real radius.
    """

    a = 6378137/1852.0
    b = 6356752.3/1852

    a1 = a*a*math.cos(math.radians(center.GetX()))
    b1 = b*b*math.sin(math.radians(center.GetX()))
    ratn = a1**2 + b1**2
    
    a2 = a*math.cos(math.radians(center.GetX()))
    b2 = b * math.sin(math.radian(center.GetX()))
    ratd = a2**2 + b2**2
    R = math.sqrt(ratn/ratd)
    deg = degrees(math.atan(radius/R))

    buf = center.Buffer(deg, quadseg)
    ring = buf.GetGeometryRef(0)

    return (buf,ring)
    

def distOgrPTupleP(ogrgeom, tuplep):
    """
    Returns the distance between an ogr.Geometry 'ogrgeom'
    and a point as a tuple 'tuplep' == (x,y,z)
    """

    bufp = osgeo.ogr.Geometry(osgeo.ogr.wkbPoint)
    x,y,z = tuplep
    bufp.AddPoint(x,y,z)

    return ogrgeom.Distance(bufp)

def findNearestIndexInLineString(ls, point):
    """
    Given an ogr.Geometry 'point' and an ogr.Geometry LineString 'ls',
    returns a tuple with the closest point in 'ls' from 'point' (as
    a tuple) and the distance between the two.
    """

    md = distOgrPTupleP(point, ls.GetPoint(0))
    mi = 0
    
    for i in xrange(1, ls.GetPointCount()):
        d = distOgrPTupleP(point, ls.GetPoint(i))
        if d < md:
            md = d
            mi = i

    return (mi,md)

def createPoint(n,e):
    """
    Creates an ogr.Geometry Point from the longitude 'n' and
    latitude 'e'.
    """
    bufp = osgeo.ogr.Geometry(osgeo.ogr.wkbPoint)
    bufp.AddPoint(n,e)
    return bufp

def getArc(ls, startPoint, endPoint):
    """
    Given a LineString 'ls', a start point 'startPoint' and an end pont 'endPoint',
    returns a tuple with the index of the points in 'ls' that are the
    closests to 'startPoint' and 'endPoint'.
    """
    si,sd = findNearestIndexInLineString(ls, startPoint)
    ei,ed = findNearestIndexInLineString(ls, endPoint)
    return (si, ei)

def latlon_to_deg(m, i=None):
    """
    Converts a match object for the coord regular expression
    to a tuple (latitude, longitude)
    If the match object contains multiple coordinates matches,
    give the index with 'i'
    """
    if i == None:
        lat = m.group('lat')
        lon = m.group('lon')
        latdir = m.group('d1')
        londir = m.group('d2')
    else:
        lat = m.group('lat%d' % i)
        lon = m.group('lon%d' % i)
        latdir = m.group('d1%d' % i)
        londir = m.group('d2%d' % i)
        
    lats = [float(x) for x in lat.split(':')]
    lons = [float(x) for x in lon.split(':')]

    if len(lats) == 3: ## hours,mins,secs
        lat_deg = lats[0] + lats[1]/60.0 + lats[2]/3600.
    elif len(lats) == 2: ## hours, mins.decimals
        lat_deg = lats[0] + lats[1]/60.0
    if latdir == "S":
        lat_deg = -lat_deg

    if len(lons) == 3: ## hours,mins,secs
        lon_deg = lons[0] + lons[1]/60.0 + lons[2]/3600.
    elif len(lons) == 2: ## hours, mins.decimals
        lon_deg = lons[0] + lons[1]/60.0
    if londir == "W":
        lon_deg = -lon_deg

    return (lat_deg, lon_deg)

class Parser:
    """
    A Parser object is used to parse an OpenAir formated
    text file into corresponding OGR objects.
    """

    zones = []
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

    def aname_action(self, line, m):
        """
        Creates a new Zone object.
        Triggered when a 'AN ...' line is matched
        """
        self.current_zone = Zone(name=m.group('name'))

    def aclass_action(self, line, m):
        """
        Sets the class for the current zone being parsed.
        Triggered when a 'AC ...' line is matched
        """

        if self.current_zone != None:
            self.zones.append(self.current_zone)
        self.current_zone = Zone(aclass=m.group('aclass'))

    def aceil_action(self, line, m):
        """
        Sets the ceiling altitude for the current zone being parsed.
        Triggered when a 'AH ...' line is matched
        """
        if m.group('height'):
            self.current_zone.ceil = " ".join((m.group('height'), m.group('ref')))
        elif m.group('fl'):
            self.current_zone.ceil = m.group('ref')
        else:
            self.current_zone.ceil = m.group('ref')

    def afloor_action(self, line, m):
        """
        Sets the floor altitude for the current zone being parsed.
        Triggered when a 'AL ...' line is matched
        """

        if m.group('height'):
            self.current_zone.floor = " ".join((m.group('height'), m.group('ref')))
        elif m.group('fl'):
            self.current_zone.floor = m.group('ref')
        else:
            self.current_zone.floor = m.group('ref')

    def arc_coord_action(self, line, m):
        """
        Adds an arc to the current polygon for the zone being parsed.
        Triggered when a 'DB ...' line is matched.
        """

        (n1, e1) = latlon_to_deg(m, 1)
        (n2, e2) = latlon_to_deg(m, 2)

        p1 = createPoint(n1, e1)
        p2 = createPoint(n2, e2)

        (buf,ring) = getCircle(self.current_zone.current_center, p1)

        si,ei = getArc(ring, p1, p2)
        print "Count:", ring.GetPointCount()
        if si > ei:
            
            if self.current_zone.direction == "cw":
                for i in xrange(si,ei+1,-1):
                    x,y,z = ring.GetPoint(i)
                    print "add [solo] [%d] %f,%f" %(i,y,x)
                    self.current_zone.addPoint(y,x)
            else:
                for i in xrange(si, ring.GetPointCount()):
                    x,y,z = ring.GetPoint(i)
                    self.current_zone.addPoint(y,x)
                    print "add [p1] [%d] %f,%f" %(i,y,x)
                for i in xrange(0, ei):
                    x,y,z = ring.GetPoint(i)
                    self.current_zone.addPoint(y,x)
                    print "add [p2] [%d] %f,%f" %(i,y,x)
                
        else: # si <= ei
            if self.current_zone.direction == "cw":
                for i in xrange(si,-1,-1):
                    x,y,z = ring.GetPoint(i)
                    self.current_zone.addPoint(y,x)
                    print "add [p1] [%d] %f,%f" %(i,y,x)
                for i in xrange(ring.GetPointCount()-1, ei, -1):
                    x,y,z = ring.GetPoint(i)
                    self.current_zone.addPoint(y,x)
                    print "add [p2] [%d] %f,%f" %(i,y,x)
            else:
                for i in xrange(si, se+1):
                    x,y,z = ring.GetPoint(i)
                    print "add [solo] [%d] %f,%f" %(i,y,x)
                    self.current_zone.addPoint(y,x)
                
    def circle_action(self, line, m):
        """
        Creates a circle for the zone being parsed.
        Triggered when a 'DC ...' line is matched
        """
        rad = float(m.group('radius'))
        (buf, ring) = getCircleByRadius(self.current_zone.current_center, rad)

        for i in xrange(ring.GetPointCount()):
            x,y,z = ring.GetPoint(i)
            self.current_zone.addPoint(y,x)

    def poly_point_action(self, line, m):
        """
        Adds a point to the polygon for the zone being parsed.
        Triggered when a 'DP ...' line is matched
        """
        (n,e) = latlon_to_deg(m)
        self.current_zone.addPoint(e,n)

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

        n,e = latlon_to_deg(m)
        self.current_zone.current_center = createPoint(n,e)

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


def getSpatialReferenceFromProj4(spatialReferenceAsProj4):
    """
    Return a new osgeo.osr.SpatialReference object, initialized
    with the projection defined in 'spatialReferenceAsProj4'.
    """
    spatialReference = osgeo.osr.SpatialReference()
    spatialReference.ImportFromProj4(spatialReferenceAsProj4)
    return spatialReference

def validateShapePath(shapePath):
    """
    Checks path 'shapePath' to the shape file.
    """
    return os.path.splitext(str(shapePath))[0] + '.shp'


p = Parser(sys.argv[1])

p.parse()

shapePath = sys.argv[2]

driver=osgeo.ogr.GetDriverByName('ESRI Shapefile')

shapePath = validateShapePath(shapePath)
if os.path.exists(shapePath): os.remove(shapePath)

shp = driver.CreateDataSource(shapePath)

# use regular WGS84 system.
# beware that some method rely on this system and won't work
# correctly if using a different system.
# These method should be ported to be projection agnostic.
spatialReference = getSpatialReferenceFromProj4('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')

layer = shp.CreateLayer('layer1', spatialReference, osgeo.ogr.wkbPolygon)
layerDefinition = layer.GetLayerDefn()

i=0
for zone in p.zones:
    try:
        poly = zone.finish()
        feature = osgeo.ogr.Feature(layerDefinition)
        feature.SetGeometry(poly)
        feature.SetFID(i)

        i+=1
        layer.CreateFeature(feature)
    except Exception,e:
        print "[DROPPED] zone (probably because it contains an arc/circle)", zone.name
        print e

# don't forget to destroy the shape object (this will purge content to file)x
shp.Destroy()
