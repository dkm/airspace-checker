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
import geojson
import pprint
import argparse


def main():
    parser = argparse.ArgumentParser(description='Dumps GeoJSON.')

    parser.add_argument('--shapefile', metavar='SHP', type=str, 
                        help='airspace data as ESRI Shapefile',
                        required=True)
    parser.add_argument('--split-class', action="store_true", default=True, 
                        help='Split zones wrt. class.')
    parser.add_argument('--output', metavar='GeoJSON', type=str, 
                        help='Output GeoJSON',
                        required=True)

    args = parser.parse_args()

    zones = airspace.shp.loadFromShp(args.shapefile)

    for z in zones:
        if not z.geometry.is_valid:
            print "NOT VALID:", z.meta

    if zones:
        print "Loaded %s zones" % len(zones)
    else:
        print "No zone loaded, exiting..."
        return -1


    fout = open(args.output, "w")

    if not args.split_class:
        zs = geojson.FeatureCollection(zones)
        print >> fout, "var spaces = " + geojson.dumps(zs)
    else:
        pass
            

    fout.close()
    return 0
    

if __name__ == "__main__":
    main()


