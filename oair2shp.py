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
import os
import os.path
import sys

import airspace.parser
import airspace.util

p = airspace.parser.OAIRParser(sys.argv[1])

p.parse()

shapePath = sys.argv[2]

driver=osgeo.ogr.GetDriverByName('ESRI Shapefile')

shapePath = airspace.util.validateShapePath(shapePath)
if os.path.exists(shapePath): os.remove(shapePath)

shp = driver.CreateDataSource(shapePath)

# use regular WGS84 system.
# beware that some method rely on this system and won't work
# correctly if using a different system.
# These method should be ported to be projection agnostic.
# spatialReference = airspace.util.getSpatialReferenceFromProj4('+proj=longlat')
## +ellps=WGS84 +datum=WGS84 +no_defs')

layer = shp.CreateLayer('layer1', geom_type=osgeo.ogr.wkbPolygon)


for zone in p.zones:
    try:
        poly = zone.finish()
        feature = osgeo.ogr.Feature(layer.GetLayerDefn())
        feature.SetGeometryDirectly(poly)

        layer.CreateFeature(feature)
        feature.Destroy()
    except Exception,e:
        print "[DROPPED] zone", zone.name
        print e

# don't forget to destroy the shape object (this will purge content to file)
shp.Destroy()
