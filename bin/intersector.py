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
import airspace.altiresolver
import argparse

def main():
    parser = argparse.ArgumentParser(description='Check airspace.')
    parser.add_argument('--track', metavar='GPX', type=str, 
                        help='a track to check', required=True)

    parser.add_argument('--shapefile', metavar='SHP', type=str, 
                        help='airspace data as ESRI Shapefile',
                        required=True)

    parser.add_argument('--altiresolver', metavar='MODE', type=str, 
                        help='Altitude resolver mode (ossim, geonames, random)',
                        required=True)

    parser.add_argument('--altiresolver-ossim-config', metavar='FILE', type=str, 
                        help='Config file path for ossim mode',
                        required=False)

    args = parser.parse_args()

    zones = airspace.shp.loadFromShp(args.shapefile)
    
    altir = None

    if args.altiresolver == "ossim":
        if args.altiresolver_ossim_config:
            # "/home/marc/SRTM/unzipe/ossim_preferences_template"
            altir = airspace.altiresolver.OssimResolverWrapper(args.altiresolver_ossim_config)
        else:
            print "Missing config file for ossim"
            return -1
    elif args.altiresolver == "geonames":
        altir = airspace.altiresolver.GeoNamesResolver()
    elif args.altiresolver == "random":
        altir = airspace.altiresolver.RandomResolver()
    else:
        print "Incorrect altitude resolver mode ", args.altiresolver 
        return -1

    for z in zones:
        if not z.geometry.is_valid:
            print "NOT VALID:", z.meta

    if zones:
        print "Loaded %s zones" % len(zones)
    else:
        print "No zone loaded, exiting..."
        return -1

    tracks = airspace.track.loadFromGpxToShapely(args.track)

    if not tracks:
        print "Could not load any track, exiting"
        return -1
    else:
        print "Loaded %d track(s)" % len(tracks)

    spatial_index = rtree.Rtree()

    # build spatial index for airspaces
    for idx,zone in enumerate(zones):
        bbox = zone.geometry.bounds
        spatial_index.add(idx, bbox)
    
    # first filtering wrt. spatial index
    potential_zones = []
    for track in tracks:
        potential_zones += [(zones[i], track) for i in spatial_index.intersection(track.bounds)]
    
    print "Potential zones after first filter:", len(potential_zones)
    for pot_zone in potential_zones:
        print "-", pot_zone[0].meta['name']

    potential_zones2 = []

    for pot_zone,track in potential_zones:
        if track.intersects(pot_zone.geometry):
            inter_track = track.intersection(pot_zone.geometry)
            potential_zones2.append((pot_zone, track, inter_track))
    
    print "Found %d potential zone(s):" % len(potential_zones2)
    
    confirmed_zones = []

    for pot_z,t,it in potential_zones2:
        confirmed = False
        import shapely.geometry.multilinestring
        import shapely.geometry.linestring

        if isinstance(it, shapely.geometry.multilinestring.MultiLineString):
            for it_ls in list(it):
                for p in it_ls.coords:
                    floor = airspace.util.getFloorAtPoint(altir, pot_z.meta, p[0], p[1])
                    ceil = airspace.util.getCeilAtPoint(altir, pot_z.meta, p[0], p[1])
                    if p[2] > floor and p[2] < ceil:
                        ## print floor, "<", p[2], "<", ceil
                        if not confirmed:
                            confirmed_zones.append(pot_z)
                            confirmed = True
                        
        elif isinstance(it, shapely.geometry.linestring.LineString):
            for p in it.coords:
                floor = airspace.util.getFloorAtPoint(altir, pot_z.meta, p[0], p[1])
                ceil = airspace.util.getCeilAtPoint(altir, pot_z.meta, p[0], p[1])
                if p[2] > floor and p[2] < ceil:
                    ## print floor, "<", p[2], "<", ceil
                    if not confirmed:
                        confirmed_zones.append(pot_z)
                        confirmed = True

    print "Confirmed zone(s) :", len(confirmed_zones)
    for conf_zone in confirmed_zones:
        print "-", conf_zone.meta['name']

    return 0
    

if __name__ == "__main__":
    main()


