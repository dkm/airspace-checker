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

import json
import shapely.wkt

def writeToShp(filename, zones):
    spatialRef = osgeo.osr.SpatialReference()
    spatialRef.SetWellKnownGeogCS('WGS84')
    driver = osgeo.ogr.GetDriverByName('ESRI Shapefile')
    dstFile = driver.CreateDataSource(filename)
    dstLayer = dstFile.CreateLayer("layer",  spatialRef)
    
    fieldDef = osgeo.ogr.FieldDefn("NAME", osgeo.ogr.OFTString)
    fieldDef.SetWidth(100)
    dstLayer.CreateField(fieldDef)
    
    fieldDef = osgeo.ogr.FieldDefn("CLASS", osgeo.ogr.OFTString)
    fieldDef.SetWidth(5)
    dstLayer.CreateField(fieldDef)

    fieldDef = osgeo.ogr.FieldDefn("CEILING", osgeo.ogr.OFTString)
    fieldDef.SetWidth(200)
    dstLayer.CreateField(fieldDef)

    fieldDef = osgeo.ogr.FieldDefn("FLOOR", osgeo.ogr.OFTString)
    fieldDef.SetWidth(200)
    dstLayer.CreateField(fieldDef)

    for meta,geometry in zones:
        buf = osgeo.ogr.CreateGeometryFromWkt(shapely.wkt.dumps(geometry))
        feature = osgeo.ogr.Feature(dstLayer.GetLayerDefn())
        feature.SetGeometry(buf)

        feature.SetField("NAME", meta['name'].encode("iso-8859-15"))
        feature.SetField("CLASS", meta['class'].encode("iso-8859-15"))
        feature.SetField("CEILING", json.dumps(meta['ceiling']))
        feature.SetField("FLOOR", json.dumps(meta['floor']))
        dstLayer.CreateFeature(feature)

        feature.Destroy()
            

    dstFile.Destroy()
        


def loadFromShp(shpfile):
    srcFile = osgeo.ogr.Open(shpfile)
    srcLayer = srcFile.GetLayer(0)
    
    zones = []

    for i in range(srcLayer.GetFeatureCount()):
        feature = srcLayer.GetFeature(i)
        name = feature.GetField("NAME")
        aclass = feature.GetField("CLASS")
        ceiling = feature.GetField("CEILING")
        floor = feature.GetField("FLOOR")
        geometry = feature.GetGeometryRef()
        
        meta = {'name' : name,
                'class': aclass,
                'ceiling': json.loads(ceiling),
                'floor' : json.loads(floor)}
        sh_geometry = shapely.wkt.loads(geometry.ExportToWkt())

        zones.append((meta,sh_geometry))
    return zones

