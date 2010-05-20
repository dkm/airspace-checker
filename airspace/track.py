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
import util

def loadGpx(gpxname):
    """
    Match lines like:
    <trkpt lat="45.129961" lon="5.883522">
    in the GPX file. Very weak.
    """
    fin = open(gpxname, "r")
    ls = util.createLineString()
    cur_point = None

    for line in fin.xreadlines():
        m = re.search('<trkpt lat="(?P<lat>\d+\.\d+)" lon="(?P<lon>\d+\.\d+)">', line)
        if m != None:
            lat = m.group('lat')
            lon = m.group('lon')
            cur_coord = [lat, lon]

        m = re.search('<ele>(?P<elevation>\d+\.\d+)</ele>', line)
        if m != None:
            ele = m.group('elevation')
            cur_coord.append(ele)

            ls.AddPoint(float(cur_coord[1]), 
                        float(cur_coord[0]),
                        float(ele))
    return ls
