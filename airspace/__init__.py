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


class Zone:
    def __init__(self, meta, geometry):
        self.meta = meta
        self.geometry = geometry

    @property
    def __geo_interface__(self):
        f = {'type': 'Feature',
             'properties': self.meta, 
             'geometry': self.geometry}
        return f

class Intersection:
    def __init__(self, zone, tracks):
        self.zone = zone
        self.tracks = tracks

    @property
    def __geo_interface__(self):
        f= {'type' : 'GeometryCollection',
            'geometries' : [self.zone, self.tracks]
            }
        return f
