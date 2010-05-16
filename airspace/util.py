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

latlong = osgeo.osr.SpatialReference()
ortho = osgeo.osr.SpatialReference()
latlong.ImportFromProj4('+proj=latlong')


def getCircle(center, point, quadseg=90):
    """
    Returns a tuple with the polygon buffer and the inner ring.
    Beware that garbage collecting the buffer will garbage collect
    the ring (within the C code, this means segfault)
    The buffer uses 'quadseg' segments for each quarter circle.
    The circle is defined by a 'center' point and another 'point'
    """

    new_c = createPoint(longitude=center.GetX(), latitude=center.GetY())
    new_c.AssignSpatialReference(latlong)
    proj = '+proj=ortho +lon_0=%f +lat_0=%f' % (center.GetX(), center.GetY())
    ortho.ImportFromProj4(proj)
    new_c.TransformTo(ortho)

    new_p = createPoint(longitude=point.GetX(), latitude=point.GetY())
    new_p.AssignSpatialReference(latlong)
    new_p.TransformTo(ortho)

    dist = new_c.Distance(new_p)
    
    buf = new_c.Buffer(dist, quadseg)

    buf.AssignSpatialReference(ortho)
    buf.TransformTo(latlong)

    return buf

def getCircleByRadius(center, radius, quadseg=90):
    """
    Returns a tuple with the polygon buffer and the inner ring.
    Beware that garbage collecting the buffer will garbage collect
    the ring (within the C code, this means segfault)
    The buffer uses 'quadseg' segments for each quarter circle.
    The circle is defined by a 'center' point its radius in nm (nautic mile)
    Beware that this method applies only to WGS84 data as there is a need for
    projection when computing the real radius.
    """
    new_c = createPoint(longitude=center.GetX(), latitude=center.GetY())
    new_c.AssignSpatialReference(latlong)
    proj = '+proj=ortho +lon_0=%f +lat_0=%f' % (center.GetX(), center.GetY())
    ortho.ImportFromProj4(proj)
    new_c.TransformTo(ortho)

    buf = new_c.Buffer(radius, quadseg)

    buf.AssignSpatialReference(ortho)
    buf.TransformTo(latlong)

    return buf
    

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

def createPoint(longitude, latitude):
    """
    Creates an ogr.Geometry Point from the longitude 'n' and
    latitude 'e'.
    """
    bufp = osgeo.ogr.Geometry(osgeo.ogr.wkbPoint)
    bufp.AddPoint(longitude, latitude)
    bufp.AssignSpatialReference(latlong)

    return bufp

def pointsOnArc(linestring, startpoint, endpoint, direction="ccw"):
    si,ei = getArcIndex(linestring, startpoint, endpoint)
    points = []

    if si > ei:
        if direction == "ccw":
            for i in xrange(si,ei+1,-1):
                x,y,z = linestring.GetPoint(i)
                points.append((x,y,z))
        else:
            for i in xrange(si, linestring.GetPointCount()):
                x,y,z = linestring.GetPoint(i)
                points.append((x,y,z))

            for i in xrange(0, ei):
                x,y,z = linestring.GetPoint(i)
                points.append((x,y,z))
                
    else: # si <= ei
        if direction == "ccw":
            for i in xrange(si,-1,-1):
                x,y,z = linestring.GetPoint(i)
                points.append((x,y,z))
            for i in xrange(linestring.GetPointCount()-1, ei, -1):
                x,y,z = linestring.GetPoint(i)
                points.append((x,y,z))
        else:
            for i in xrange(si, ei+1):
                x,y,z = linestring.GetPoint(i)
                points.append((x,y,z))
  
    return points

def getArcIndex(ls, startPoint, endPoint):
    """
    Given a LineString 'ls', a start point 'startPoint' and an end pont 'endPoint',
    returns a tuple with the index of the points in 'ls' that are the
    closests to 'startPoint' and 'endPoint'.
    """
    si,sd = findNearestIndexInLineString(ls, startPoint)
    ei,ed = findNearestIndexInLineString(ls, endPoint)
    return (si, ei)

def latlonStr_to_deg(lat, latdir, lon, londir):
            
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
        
    
    return latlonStr_to_deg(lat, latdir, lon, londir)

def getSpatialReferenceFromProj4(spatialReferenceAsProj4):
    """
    Return a new osgeo.osr.SpatialReference object, initialized
    with the projection defined in 'spatialReferenceAsProj4'.
    """
    spatialReference = osgeo.osr.SpatialReference()
    spatialReference.ImportFromProj4(spatialReferenceAsProj4)
    return spatialReference


def writeGeometriesToShapeFile(geometries, shapefile):
    """
    Writes a set of OGRGeometry object to a shapefile (.shp)
    """

    driver = osgeo.ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(shapefile): os.remove(shapefile)
    shp = driver.CreateDataSource(shapefile)

    layer = shp.CreateLayer('defaultlayer', geom_type=osgeo.ogr.wkbPolygon)
    for geom in geometries:
        feature = osgeo.ogr.Feature(layer.GetLayerDefn())
        feature.SetGeometryDirectly(geom)
        layer.CreateFeature(feature)
        feature.Destroy()
    shp.Destroy()

