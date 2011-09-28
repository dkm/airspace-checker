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
import airspace 
from datetime import date

def setAlti(fieldName, dataDict, feature):
    upFN = fieldName.upper()

    alti, unit = dataDict.get('basealti', ("",""))
    ref = dataDict.get('ref', "")
    flevel = dataDict.get('flevel', -1)
    sfc = 1 if dataDict.get('fromground', False) else 0
    unl = 1 if dataDict.get('nolimit', False) else 0
    
    if alti and unit:
        if unit == "M":
            feature.SetField(upFN + "_ALTIM", int(alti))
        else: ## unit == "F"
            feature.SetField(upFN + "_ALTIM", int(alti) * 0.3048)
    
        feature.SetField(upFN + "_ALTI", str(alti) + " " + unit)
    elif flevel != -1:
        feature.SetField(upFN + "_ALTIM", flevel * 100 * 0.3048)
        feature.SetField(upFN + "_ALTI", "")
    else:
        feature.SetField(upFN + "_ALTIM", -1)
        feature.SetField(upFN + "_ALTI", "")
        
    feature.SetField(upFN + "_REF", ref)
    feature.SetField(upFN + "_FL", flevel)
    feature.SetField(upFN + "_F_SFC", sfc)
    feature.SetField(upFN + "_UNL", unl)


def writeToShp(filename, zones):
    spatialRef = osgeo.osr.SpatialReference()
    spatialRef.SetWellKnownGeogCS('WGS84')
    driver = osgeo.ogr.GetDriverByName('ESRI Shapefile')
    dstFile = driver.CreateDataSource(filename)
    dstLayer = dstFile.CreateLayer("layer",  spatialRef)
    
    fieldDef = osgeo.ogr.FieldDefn("NAME", osgeo.ogr.OFTString)
    dstLayer.CreateField(fieldDef)
    
    fieldDef = osgeo.ogr.FieldDefn("CLASS", osgeo.ogr.OFTString)
    dstLayer.CreateField(fieldDef)

    # DateTime not supported, fallback to String as we really need
    # Time info for zone.
    fieldDef = osgeo.ogr.FieldDefn("START_DATE", osgeo.ogr.OFTString)
    dstLayer.CreateField(fieldDef)

    fieldDef = osgeo.ogr.FieldDefn("STOP_DATE", osgeo.ogr.OFTString)
    dstLayer.CreateField(fieldDef)

    fieldDef = osgeo.ogr.FieldDefn("EXT_INFO", osgeo.ogr.OFTString)
    dstLayer.CreateField(fieldDef)

    fieldDef = osgeo.ogr.FieldDefn("CEIL_ALTIM", osgeo.ogr.OFTReal)
    dstLayer.CreateField(fieldDef)

    fieldDef = osgeo.ogr.FieldDefn("CEIL_ALTI", osgeo.ogr.OFTString)
    dstLayer.CreateField(fieldDef)

    fieldDef = osgeo.ogr.FieldDefn("CEIL_REF", osgeo.ogr.OFTString)
    dstLayer.CreateField(fieldDef)

    fieldDef = osgeo.ogr.FieldDefn("CEIL_FL", osgeo.ogr.OFTInteger)
    dstLayer.CreateField(fieldDef)

    fieldDef = osgeo.ogr.FieldDefn("CEIL_F_SFC", osgeo.ogr.OFTInteger)
    dstLayer.CreateField(fieldDef)

    fieldDef = osgeo.ogr.FieldDefn("CEIL_UNL", osgeo.ogr.OFTInteger)
    dstLayer.CreateField(fieldDef)


    fieldDef = osgeo.ogr.FieldDefn("FLR_ALTIM", osgeo.ogr.OFTReal)
    dstLayer.CreateField(fieldDef)

    fieldDef = osgeo.ogr.FieldDefn("FLR_ALTI", osgeo.ogr.OFTString)
    dstLayer.CreateField(fieldDef)

    fieldDef = osgeo.ogr.FieldDefn("FLR_REF", osgeo.ogr.OFTString)
    dstLayer.CreateField(fieldDef)

    fieldDef = osgeo.ogr.FieldDefn("FLR_FL", osgeo.ogr.OFTInteger)
    dstLayer.CreateField(fieldDef)

    fieldDef = osgeo.ogr.FieldDefn("FLR_F_SFC", osgeo.ogr.OFTInteger)
    dstLayer.CreateField(fieldDef)

    fieldDef = osgeo.ogr.FieldDefn("FLR_UNL", osgeo.ogr.OFTInteger)
    dstLayer.CreateField(fieldDef)


    for z in zones:
        meta,geometry = z.meta, z.geometry
        buf = osgeo.ogr.CreateGeometryFromWkt(shapely.wkt.dumps(geometry))
        feature = osgeo.ogr.Feature(dstLayer.GetLayerDefn())
        feature.SetGeometry(buf)

        feature.SetField("NAME", meta['name'].encode("utf-8"))
        feature.SetField("CLASS", meta['class'].encode("utf-8"))

        
        setAlti("CEIL", meta['ceiling'], feature)
        setAlti("FLR", meta['floor'], feature)

        feature.SetField("START_DATE", date.today().strftime("%Y-%m-%d %H:%M"))
        feature.SetField("STOP_DATE", date.today().strftime("%Y-%m-%d %H:%M"))
        
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

        zones.append(airspace.Zone(meta,sh_geometry))
    return zones

