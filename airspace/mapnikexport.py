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

import mapnik

def toMapnik(shapefile, destfile):
    symbolizer = mapnik.PolygonSymbolizer(mapnik.Color("darkgreen"))
    rule = mapnik.Rule()
    rule.symbols.append(symbolizer)
    style = mapnik.Style()
    style.rules.append(rule)
    layer = mapnik.Layer("mapLayer")
    layer.datasource = mapnik.Shapefile(file=shapefile)
    layer.styles.append("mapStyle")
    mapk = mapnik.Map(800, 400)
    mapk.background = mapnik.Color("steelblue")
    mapk.append_style("mapStyle", style)
    mapk.layers.append(layer)
    mapk.zoom_all()
    mapnik.render_to_file(mapk, destfile, "png")
