#!/usr/bin/env python

import re
import osgeo.ogr as ogr
import osgeo.osr

import sys

aclass = re.compile('^AC (?P<aclass>R|Q|P|A|B|C|D|GP|CTR|W)$')

coords = '(?P<north%s>\d+:\d+:\d+) N (?P<east%s>\d+:\d+:\d+) E'
alti = '(?P<height>\d+F )?(?P<ref>AGL|AMSL|FL|SFC|UNL)$'

aceil = re.compile('^AH ' + alti)
afloor = re.compile('^AL ' + alti)
aname = re.compile('^AN (?P<name>.*)$')

poly_point = re.compile('^DP ' + coords % ("", "") + '$')

arc_coord = re.compile('^DB ' + coords % ("1","1") +','+ coords  % ("2","2") + '$')

set_direction = re.compile('^V D=(?P<direction>\+|-)$')
set_center = re.compile('^V X=' + coords % ("", "") + '$')
set_width = re.compile('^V W=(?P<width>\d+\.\d+)$')
set_zoom = re.compile('^V Z=(?P<zoom>\d+\.\d+)$')

airway = re.compile('^DY ' + coords % ("", "") + '$')

re_lines = [aclass, 
            aceil, 
            afloor, 
            aname, 
            arc_coord, 
            poly_point, 
            set_direction, 
            set_center,
            set_width,
            set_zoom,
            airway]



class Zone:
    def __init__(self, name=None, aclass=None):
        self.name = name
        self.poly = ogr.Geometry(ogr.wkbPolygon)
        self.ring = None
        self.aclass = None
        self.ceil = None
        self.floor = None

    def addPoint(self, x, y):
        if self.ring == None:
            self.ring = ogr.Geometry(ogr.wkbLinearRing)
            self.poly.AddGeometry(self.ring)
        self.ring.AddPoint(x,y)

class Parser:

    zones = []
    current_zone = None

    def __init__(self, fname):
        self.fname = fname
        self.parse_actions = { aclass: self.aclass_action,
                               aceil: self.aceil_action,
                               afloor: self.afloor_action,
                               aname : self.aname_action,
                               arc_coord : self.arc_coord_action,
                               poly_point: self.poly_point_action,
                               set_direction: self.set_direction_action,
                               set_center: self.set_center_action,
                               set_zoom: self.set_zoom_action,
                               set_width: self.set_width_action,
                               airway : self.airway_action}

    def aname_action(self, line, m):
        if self.current_zone != None:
            if self.current_zone.ring != None: ## this is a new zone
                self.zones.append(self.current_zone)
                print "Appended zone '%s' to zone line (%d)" % (self.current_zone.name, 
                                                                len(self.current_zone))
                self.current_zone = Zone(name=m.group('name'))
                print "New zone with name:", m.group('name')
            else: ## ring is empty, this is the begining of a zone
                self.current_zone.name = m.group('name')
        else:
            self.current_zone = Zone(name=m.group('name'))
            print "New zone with name:", m.group('name')

    def aclass_action(self, line, m):
        if self.current_zone != None:
            if self.current_zone.ring != None: ## this is a new zone
                self.zones.append(self.current_zone)
                print "Appended zone '%s' to zone line (%d)" % (self.current_zone.name, 
                                                                len(self.current_zone))
                self.current_zone = Zone(aclass=m.group('aclass'))
                print "New zone with class:", m.group('aclass')
            else: ## ring is empty, this is the begining of a zone
                self.current_zone.aclass = m.group('aclass')
        else:
            self.current_zone = Zone(name=m.group('aclass'))
            print "New zone with class:", m.group('aclass')

    def aceil_action(self, line, m):
        print "aceil", m.group('height'), m.group('ref')
        if m.group('height'):
            self.current_zone.ceil = " ".join((m.group('height'), m.group('ref')))
        else:
            self.current_zone.ceil = m.group('ref')

    def afloor_action(self, line, m):
        print "afloor", m.group('height'), m.group('ref')
        if m.group('height'):
            self.current_zone.floor = " ".join(m.group('height'), m.group('ref'))
        else:
            self.current_zone.floor = m.group('ref')

    def arc_coord_action(self, line, m):
        print "arc coord", m.group('north1'), m.group('east1'), m.group('north2'), m.group('east2')
        
        for i in range(1,3):
            dn,mn,sn = [float(x) for x in m.group('north%d' % i).split(':')]
            de,me,se = [float(x) for x in m.group('east%d' % i).split(':')]
        
            n = dn + mn/60.0 + sn/3600.
            e = de + me/60.0 + se/3600.

            print "add point to ring", m.group('north%d' % i), m.group('east%d' % i)

            print "  -> %f / %f" %(n,e)
            self.current_zone.addPoint(e,n)


    def poly_point_action(self, line, m):
        dn,mn,sn = [float(x) for x in m.group('north').split(':')]
        de,me,se = [float(x) for x in m.group('east').split(':')]
        
        n = dn + mn/60.0 + sn/3600.
        e = de + me/60.0 + se/3600.

        print "add point to ring", m.group('north'), m.group('east')
        print "  -> %f / %f" %(n,e)
        self.current_zone.addPoint(e,n)

    def set_direction_action(self, line, m):
        print "set direction", m.group('direction')

    def set_center_action(self, line, m):
        print "set center", m.group('north'), m.group('east')

    def set_zoom_action(self, line, m):
        print "set zoom", m.group('zoom')

    def set_width_action(self, line, m):
        print "set width", m.group('width')

    def airway_action(self, line, m):
        print "airway", m.group('north'), m.group('east')

            
    def parse(self):
        fin = open(self.fname)
        for l in fin.xreadlines():
            for r in re_lines:
                m = r.match(l)
                if m != None:
                    self.parse_actions[r](l,m)
        
        if self.current_zone != None:
            self.zones.append(self.current_zone)
            print "Appended zone '%s' to zone list (%d)" % (self.current_zone.name, 
                                                            len(self.zones))


p = Parser(sys.argv[1])

p.parse()

for zone in p.zones:
    print zone.ring

driver=ogr.GetDriverByName('ESRI Shapefile')
shp=driver.CreateDataSource(sys.argv[2])
spatialReference = osgeo.osr.SpatialReference()
spatialReference.ImportFromProj4('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')

layer = shp.CreateLayer('layer1', spatialReference, osgeo.ogr.wkbUnknown)
layerDefinition = layer.GetLayerDefn()

i=0
for zone in p.zones:
    feature = osgeo.ogr.Feature(layerDefinition)
    feature.SetGeometry(zone.poly)
    feature.SetFID(i)

    print "added poly in feature ", i,
    i+=1
    layer.CreateFeature(feature)
    print ", created feture and added to layer "

shp.Destroy()
print "finished, wrote in ", sys.argv[2]
