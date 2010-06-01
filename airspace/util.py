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
    Returns a polygon buffer with an inner ring representing the circle.
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
    Returns a polygon buffer with an inner ring representing the circle.
    The buffer uses 'quadseg' segments for each quarter circle.
    The circle is defined by a 'center' point its radius in nm (nautic mile)
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

def createPoint(longitude, latitude, altitude=0):
    """
    Creates an ogr.Geometry Point from the longitude and
    latitude.
    """
    bufp = osgeo.ogr.Geometry(osgeo.ogr.wkbPoint)
    bufp.AddPoint(longitude, latitude, altitude)
    bufp.AssignSpatialReference(latlong)

    return bufp

def pointsOnArc(linestring, startpoint, endpoint, direction="ccw"):
    """
    Returns a list of tuple (x,y,z) of point along the arc 'linestring',
    between the 'startpoint' and 'endpoint'. The 'direction' parameters gives
    the rotation direction: 'cw' for clockwise, 'ccw' for counter-clockwise.
    """
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
    """
    Converts various lat/lon string coordinates representation
    to degrees representation.
    """
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

def getSubLineStringInZone(linestring, zone):
    linestrings = []

    active = False 
    ls = osgeo.ogr.Geometry(osgeo.ogr.wkbLineString)


    for idx in xrange(linestring.GetPointCount()):
        x,y,z = linestring.GetPoint(idx)
        p = createPoint(x,y,z)
        if zone.Contains(p):
            ls.AddPoint(x,y,z)
        else :
            if active:
                linestrings.append(ls)
                ls = osgeo.ogr.Geometry(osgeo.ogr.wkbLineString)

    if ls.GetPointCount() > 0:
        linestrings.append(ls)
    return linestrings

def writeGeometriesToShapeFile(geometries, shapefile):
    """
    Writes a set of OGRGeometry object to a shapefile (.shp)
    """

    driver = osgeo.ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(shapefile): os.remove(shapefile)
    shp = driver.CreateDataSource(shapefile)

    layer = shp.CreateLayer('defaultlayer')
    field_defn = osgeo.ogr.FieldDefn( "Name", osgeo.ogr.OFTString )
    field_defn.SetWidth( 32 )
    layer.CreateField(field_defn)

    for geom,name_field in geometries:
        feature = osgeo.ogr.Feature(layer.GetLayerDefn())
        #feature.SetStyleString("BRUSH(fc:#0000FF);PEN(c:#000000)")
        feature.SetGeometryDirectly(geom)
        feature.SetField("Name", name_field)
        layer.CreateFeature(feature)
        feature.Destroy()
    shp.Destroy()

