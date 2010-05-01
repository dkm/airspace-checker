airspace checker
================

airspace-checker aims at being able to check that a given flight did respect the
different airspaces.

Its development is focused on French airspaces + paragliding/hanggliding.

URL:
http://wiki.kataplop.net/wiki/doku.php?id=geek:integrated_paragliding_portal

DOWNLOAD: http://github.com/dkm/airspace-checker

usage
=====

Currently, only the converter from OpenAir format to ESRI Shapefile is (partly)
working:

$ ./oair2shp.py france.txt france.shp

converts the OpenAir file 'france.txt' to 'franche.shp' shapefile.

This shapefile can be converted to KML using ogr2ogr tool:

$ ogr2ogr -f KML france.kml france.shp france


dependencies
============

The GDAL/OGR bindings for python ('python-gdal' package in Debian based distros).

The 'gdal-bin' package can be useful (it contains the 'ogr2ogr' tool).