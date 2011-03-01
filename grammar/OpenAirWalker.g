tree grammar OpenAirWalker;


options {
    tokenVocab=OpenAir;
    ASTLabelType=CommonTree;
//    backtrack=true;
    memoize=true;
  //  output=AST;
    language=Python;
}

@header {
import shapely.geometry
import airspace.util
}

@members {
def debug_print(self, s):
    if self.debug:
        print s
}

oair_file returns [zones]
@init{
    zones = []
}
	: ^(ZONES (zone{zones.append($zone.zone_desc)})+)
	;
	
zone returns [zone_desc]
scope{
    direction;
    name
}
@init {
 $zone::direction = "cw"
}
	: ^(ZONE aclass name{$zone::name=$name.name} ceiling floor ^(GEOMETRY geometry))
        {
            meta={'class': $aclass.aclass, 
                  'name': $name.name,
                  'ceiling': $ceiling.ceiling,
                  'floor': $floor.floor
                  }
            self.debug_print($name.name)
            $zone_desc = (meta, $geometry.polygon)
        }
	;

aclass	returns [aclass]
    : ^(CLASS  ('A'{$aclass='A'}|'C'{$aclass='C'}|'CTR'{$aclass='CTR'}|'D'{$aclass='D'}|'E'{$aclass='E'}|'GP'{$aclass='GP'}|'P'{$aclass='P'}|'Q'{$aclass='Q'}|'R'{$aclass='R'}|'W'{$aclass='W'}))
	;
	
name returns [name]	: ^(NAME AN_NAME) {$name = $AN_NAME.text[3:].strip()}
	;

ceiling returns [ceiling]
@init {
    $ceiling = []
}
 	: ^(ALTIS (altitude_specif {$ceiling.append($altitude_specif.altispecif)})+)
	;

floor returns [floor]
@init{
    $floor = []
}
    : ^(ALTIS (altitude_specif {$floor.append($altitude_specif.altispecif)})+)
	;

frag_alti returns [absalti]
	: ^(BASE_ALTI INT{$absalti=float($INT.text)} ('F'{$absalti=$absalti*0.3048}|'M'))
 	;
 	
altitude_specif returns [altispecif]
@init {
    $altispecif = {}
}
	:
	  ^(ALTI frag_alti (r='AGL'|r='AMSL'|r='ASFC') 
        {
        $altispecif['basealti']=$frag_alti.absalti
        $altispecif['ref'] = $r.text
        })
	| ^(ALTI (frag_alti{$altispecif['basealti']=$frag_alti.absalti})? ('SFC') {$altispecif['ref'] = 'SFC'}) 
	| ^(ALTI FLEVEL {$altispecif['flevel']=int($FLEVEL.text[2:])})
	| ^(ALTI 'UNL' {$altispecif['nolimit']=True})
	| ^(ALTI 'GND' {$altispecif['fromground']=True})
	;
	
geometry returns [polygon]
@init{
 points = []
}
	: 
    (
      ( single_point {points.append($single_point.point)}
      | circle_arc {points += $circle_arc.points})+
    ) {
         $polygon = shapely.geometry.Polygon(points)}

	|  circle {$polygon = $circle.polygon}
	;
	
single_point returns [point]
	: COORDS {
         $point = airspace.util.rawLatLonConvToLonLat($COORDS.text)
	  }
	;

circle_direction
	:  ('+' {$zone::direction = "cw"}|'-' {$zone::direction = "ccw"})
	;
	
circle_center  returns [spoint]
	:  COORDS {
	      $spoint = shapely.geometry.Point(airspace.util.rawLatLonConvToLonLat($COORDS.text))
	   }
	;
	
circle_arc returns [points]
	:  ^(CIRCLE_ARC circle_center c1=COORDS c2=COORDS 
	       (circle_direction)?)
{
 point1 = shapely.geometry.Point(airspace.util.rawLatLonConvToLonLat($c1.text))
 point2 = shapely.geometry.Point(airspace.util.rawLatLonConvToLonLat($c2.text))
 center = $circle_center.spoint
 try:
     $points = airspace.util.getArc2(center, point1, point2, $zone::direction)
 except airspace.util.InvalidDataException,e:
     print e.message
     print "in ", $zone::name
     raise e
}
	;
	
circle returns [polygon]
@init{
r=None
}
	: 
	   ^(CIRCLE circle_center (INT{r = float($INT.text)} | FLOAT {r = float($FLOAT.text)})){
	     $polygon = airspace.util.getCircle2($circle_center.spoint, r*1000)
	   }
	;
