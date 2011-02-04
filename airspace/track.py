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

# For the loadFromGpx() method, mainly based on ogr2osm.py:
#####################################################################################
#   "THE BEER-WARE LICENSE":                                                        #
#   <ivan@sanchezortega.es> wrote this file. As long as you retain this notice you  #
#   can do whatever you want with this stuff. If we meet some day, and you think    #
#   this stuff is worth it, you can buy me a beer in return.                        #
#####################################################################################

import re
import util
import osgeo.ogr
import shapely.wkt

def loadSimpleTxt(txtfile):
    fin = open(txtfile, "r")
    ls = osgeo.ogr.Geometry(osgeo.ogr.wkbLineString)

    for line in fin.xreadlines():
        lon,lat,alt = line.strip().split()
        ls.AddPoint(float(lon), 
                    float(lat),
                    float(alt))
    fin.close()
    return ls

def loadFromGpxToShapely(gpxfilename, detectProjection=True):
    """
    From a GPX, loads all lines/multilines and returns
    a list of shapely representation
    """
    return [shapely.wkt.loads(x) for x in loadFromGpx(gpxfilename, detectProjection)]

def loadFromGpx(gpxfilename, detectProjection=True):
    """
    From a GPX, loads all lines/multilines and returns
    WKT representation
    """
    driver = osgeo.ogr.GetDriverByName('GPX')
    dataSource = driver.Open(gpxfilename, 0)
    geoms_to_return = []

    for i in xrange(dataSource.GetLayerCount()):
	layer = dataSource.GetLayer(i)
	layer.ResetReading()
	
	spatialRef = None
	if detectProjection:
            spatialRef = layer.GetSpatialRef()
	# elif useProj4:
	# 	spatialRef = osr.SpatialReference()
	# 	spatialRef.ImportFromProj4(sourceProj4)

            
	if spatialRef == None:	
            # No source proj specified yet? Then default to do no reprojection.
            # Some python magic: skip reprojection
            # altogether by using a dummy lamdba
            # funcion. Otherwise, the lambda will
            # be a call to the OGR reprojection
            # stuff.
            reproject = lambda(geometry): None
	else:
            destSpatialRef = osgeo.osr.SpatialReference()
            destSpatialRef.ImportFromEPSG(4326)	
            # Destionation projection will *always* be EPSG:4326,
            # WGS84 lat-lon
            coordTrans = osgeo.osr.CoordinateTransformation(spatialRef,destSpatialRef)
            reproject = lambda(geometry): geometry.Transform(coordTrans)

        featureDefinition = layer.GetLayerDefn()

	for j in range(layer.GetFeatureCount()):
            feature = layer.GetNextFeature()
            geometry = feature.GetGeometryRef()
            geometryType = geometry.GetGeometryType()
            
            ls = []

            if  geometryType == osgeo.ogr.wkbLineString or geometryType == osgeo.ogr.wkbLineString25D:
                if geometry.GetPointCount() <= 2:
                    continue
                ls.append(geometry)
            elif geometryType == osgeo.ogr.wkbMultiLineString or geometryType == osgeo.ogr.wkbMultiLineString25D:
                for i in xrange(geometry.GetGeometryCount()):
                    subgeom = geometry.GetGeometryRef(i)
                    if subgeom.GetPointCount() <= 2:
                        continue
                    else:
                        ls.append(subgeom)
                for line in ls:
                    reproject(line)
                    geoms_to_return.append(line.ExportToWkt())

    return geoms_to_return


