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

import airspace.parser
import airspace.shp

import sys

import argparse
import os

def main():
    parser = argparse.ArgumentParser(description='Compile OpenAIR file into ESRI Shapefile.')
    parser.add_argument('--openair', metavar='OpenAir', type=str, 
                        help='The OpenAIR file to compile')
    parser.add_argument('--shapefile', metavar='ShapefileName', type=str, 
                        help='the output ESRI Shapefile base prefix')
    parser.add_argument('--force', action="store_true", default=False, 
                        help='overwrite output if it exists')
    parser.add_argument('--fix', action="store_true", default=False, 
                        help='try to fix incorrect geometries USE WITH CARE!!!')
    parser.add_argument('--skip-invalid', action="store_true", default=False, 
                        help='Skip invalid geometries.')

    args = parser.parse_args()

    already_warned = False
    for ext in [".shp", ".shx", ".dbf"]:
        if os.path.exists(args.shapefile + ext):
            if args.force:
                if not already_warned:
                    print "Overwriting existing zones"
                    already_warned = True
                os.remove(args.shapefile + ext)
            else:
                print "exiting. Use --force to overwrite"
                return

    res = airspace.parser.parse(args.openair)

    valid_res = []
    skipped = []
    print "Checking for validity"
    for r in res:
        meta,geometry = r.meta, r.geometry
        if not geometry.is_valid:
            print "NOT VALID:", meta

            if args.skip_invalid:
                skipped.append(r)
            else:
                import shapely.wkt
                test_geo = geometry.buffer(0.0000001)

                if args.fix and test_geo.is_valid:
                    print "replaced, ok"
                    valid_res.append(airspace.Zone(meta, test_geo))
                else:
                    valid_res.append(r)
                    print "Invalid kept."
        else:
            valid_res.append(r)

    if not valid_res:
        print "Parser returned 0 zones, not writing anything."
    else:
        print "Found %d zones" %len(valid_res),
        if skipped:
            print", and skipped %d zones" %len(skipped)
        
        ok = True
        for r in valid_res:
            meta,zone = r.meta,r.geometry
            if not zone.is_valid:
                print meta['name'], " is not valid"
                ok = False

        airspace.shp.writeToShp(args.shapefile, valid_res)

if __name__ == "__main__":
    main()
