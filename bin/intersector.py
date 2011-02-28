#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   airspace checker
#   Copyright (C) 2011  Marc Poulhiès
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

import sys
import airspace
import airspace.shp
import airspace.track
import rtree

import argparse


def main():
    parser = argparse.ArgumentParser(description='Check airspace.')
    parser.add_argument('--track', metavar='GPX', type=str, 
                        help='a track to check', required=True)

    parser.add_argument('--shapefile', metavar='SHP', type=str, 
                        help='airspace data as ESRI Shapefile',
                        required=True)

    args = parser.parse_args()

    zones = airspace.shp.loadFromShp(args.shapefile)

    for m,z in zones:
        if not z.is_valid:
            print "NOT VALID:", m

    if zones:
        print "Loaded %s zones" % len(zones)
    else:
        print "No zone loaded, exiting..."
        return -1

    tracks = airspace.track.loadFromGpxToShapely(args.track)

    if not tracks:
        print "Could not load any track, exiting"
        return -1

    spatial_index = rtree.Rtree()

    # build spatial index for airspaces
    for idx,zone in enumerate(zones):
        bbox = zone[1].bounds
        spatial_index.add(idx, bbox)
    
    # first filtering wrt. spatial index
    potential_zones = []
    for track in tracks:
        potential_zones += [(zones[i], track) for i in spatial_index.intersection(track.bounds)]
    
    print "Potential zones after first filter:", len(potential_zones)
    for pot_zone in potential_zones:
        print "-", pot_zone[0][0]['name']

    potential_zones2 = []

    for pot_zone,track in potential_zones:
        if track.intersects(pot_zone[1]):
            inter_track = track.intersection(pot_zone[1])
            potential_zones2.append((pot_zone, track, inter_track))
    
    print "Found %d potential zone(s):" % len(potential_zones2)

    for pot_z,t,it in potential_zones2:
        import shapely.geometry.multilinestring
        import shapely.geometry.linestring
        print " - %s" % pot_z[0]['name']

        if isinstance(it, shapely.geometry.multilinestring.MultiLineString):
            for it_ls in list(it):
                for p in it_ls.coords:
                    floor = airspace.util.getFloorAtPoint(pot_z[0], p[0], p[1])
                    ceil = airspace.util.getCeilAtPoint(pot_z[0], p[0], p[1])
                    if p[2] > floor and p[2] < ceil:
                        print floor, "<", p[2], "<", ceil
        elif isinstance(it, shapely.geometry.linestring.LineString):
            for p in it.coords:
                floor = airspace.util.getFloorAtPoint(pot_z[0], p[0], p[1])
                ceil = airspace.util.getCeilAtPoint(pot_z[0], p[0], p[1])
                if p[2] > floor and p[2] < ceil:
                    print floor, "<", p[2], "<", ceil
                
    return 0
    

if __name__ == "__main__":
    main()


