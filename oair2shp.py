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


def getCircle(center, p2):
    dist = center.Distance(p2)
    buf = center.Buffer(dist,90)
    ring = buf.GetGeometryRef(0)

    return (buf,ring)

def getCircleByRadius(center, radius):
    
    a = 6378137/1852.0
    b = 6356752.3/1852

    a1 = a*a*math.cos(center.GetX())
    b1 = b*b*math.sin(center.GetX())
    ratn = a1*a1 + b1*b1
    
    a2 = a*math.cos(center.GetX())
    b2 = b * math.sin(center.GetX())
    ratd = a2*a2 + b2*b2
    R = math.sqrt(ratn/ratd)
    deg = math.atan(radius/R) * 180 / math.pi
    print deg
    buf = center.Buffer(deg, 90)
    ring = buf.GetGeometryRef(0)

    return (buf,ring)
    

def distOgrPTupleP(ogrp, tuplep):
    bufp = osgeo.ogr.Geometry(osgeo.ogr.wkbPoint)
    x,y,z = tuplep
    bufp.AddPoint(x,y,z)

    return ogrp.Distance(bufp)

def findNearestIndexInLineString(ls, point):
    md = distOgrPTupleP(point, ls.GetPoint(0))
    mi = 0
    
    for i in xrange(1, ls.GetPointCount()):
        d = distOgrPTupleP(point, ls.GetPoint(i))
        if d < md:
            md = d
            mi = i

    return (mi,md)

def createPoint(n,e):
    bufp = osgeo.ogr.Geometry(osgeo.ogr.wkbPoint)
    bufp.AddPoint(n,e)
    return bufp

def getArc(ls, startPoint, endPoint):
    si,sd = findNearestIndexInLineString(ls, startPoint)
    ei,ed = findNearestIndexInLineString(ls, endPoint)
    return (si, ei)

def latlon_to_deg(m, i=None):
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

    zones = []
    current_zone = None

    def __init__(self, fname):
        self.fname = fname
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
        self.current_zone = Zone(name=m.group('name'))

    def aclass_action(self, line, m):
        if self.current_zone != None:
            self.zones.append(self.current_zone)
        self.current_zone = Zone(aclass=m.group('aclass'))

    def aceil_action(self, line, m):
        if m.group('height'):
            self.current_zone.ceil = " ".join((m.group('height'), m.group('ref')))
        elif m.group('fl'):
            self.current_zone.ceil = m.group('ref')
        else:
            self.current_zone.ceil = m.group('ref')

    def afloor_action(self, line, m):
        if m.group('height'):
            self.current_zone.floor = " ".join((m.group('height'), m.group('ref')))
        elif m.group('fl'):
            self.current_zone.floor = m.group('ref')
        else:
            self.current_zone.floor = m.group('ref')

    def arc_coord_action(self, line, m):
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
        rad = float(m.group('radius'))
        (buf, ring) = getCircleByRadius(self.current_zone.current_center, rad)

        for i in xrange(ring.GetPointCount()):
            x,y,z = ring.GetPoint(i)
            self.current_zone.addPoint(y,x)

    def poly_point_action(self, line, m):
        (n,e) = latlon_to_deg(m)
        self.current_zone.addPoint(e,n)

    def set_direction_action(self, line, m):
        direct = m.group('direction')
        if direct == "+":
            self.current_zone.direct = "cw"
        elif direct == "-":
            self.current_zone.direct = "ccw"

    def set_center_action(self, line, m):
        n,e = latlon_to_deg(m)
        self.current_zone.current_center = createPoint(n,e)

    def set_zoom_action(self, line, m):
        pass

    def set_width_action(self, line, m):
        pass

    def airway_action(self, line, m):
        pass
            
    def parse(self):
        fin = open(self.fname)
        for l in fin.xreadlines():
            for r in re_lines:
                m = r.match(l)
                if m != None:
                    self.parse_actions[r](l,m)
        
        if self.current_zone != None:
            self.zones.append(self.current_zone)


def getSpatialReferenceFromProj4(spatialReferenceAsProj4):
    spatialReference = osgeo.osr.SpatialReference()
    spatialReference.ImportFromProj4(spatialReferenceAsProj4)
    return spatialReference

def validateShapePath(shapePath):
    return os.path.splitext(str(shapePath))[0] + '.shp'

p = Parser(sys.argv[1])

p.parse()

shapePath = sys.argv[2]

driver=osgeo.ogr.GetDriverByName('ESRI Shapefile')

shapePath = validateShapePath(shapePath)
if os.path.exists(shapePath): os.remove(shapePath)

shp = driver.CreateDataSource(shapePath)

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
        raise e
        print "[DROPPED] zone (probably because it contains an arc/circle)", zone.name

shp.Destroy()
