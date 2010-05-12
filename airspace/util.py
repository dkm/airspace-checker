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
