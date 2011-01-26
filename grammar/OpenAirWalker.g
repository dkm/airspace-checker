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

}

oair_file 
	: ^(ZONES zone+)
	;
	
zone	 	
	: ^(ZONE aclass name ceiling floor ^(GEOMETRY geometry))
	;

aclass	: ^(CLASS  ('A'|'C'|'CTR'|'D'|'E'|'GP'|'P'|'Q'|'R'|'W'))
	;
	
name	: ^(NAME AN_NAME)
	;

ceiling 	: altitude_specif
	;

floor	: altitude_specif
	;

frag_alti
	: ^(BASE_ALTI INT ('F'|'M'))
 	;
 	
altitude_specif
	:
	  ^(ALTI frag_alti ('AGL'|'AMSL'))
	| ^(ALTI frag_alti? ('SFC')) 
	| ^(ALTI FLEVEL)
	| ^(ALTI 'UNL')
	;
	
geometry returns [polygon]
@init{
 points = []
}
	: 
                        ((single_point {points.append($single_point.point)}| circle_arc {points += $circle_arc.points})*)
                        {$polygon = shapely.geometry.Polygon(points)}
	|  circle {$polygon = $circle.polygon}
	;
	
single_point returns [point]
	: COORDS {
	     $point = airspace.util.rawLatLonConv($COORDS.text)
	  }
	;

circle_direction returns [direction]
	:  ('+' {$direction = "cw"}|'-' {$direction = "ccw"})
	;
	
circle_center  returns [spoint]
	:  COORDS {
	      $spoint = shapely.geometry.Point(airspace.util.rawLatLonConv($COORDS.text))
	   }
	;
	
circle_arc returns [points]
@init{
 direction = "ccw"
}
	:  ^(CIRCLE_ARC circle_center c1=COORDS c2=COORDS 
	       (circle_direction{direction=$circle_direction.direction})?)
{
 point1 = shapely.geometry.Point(airspace.util.rawLatLonConv($c1.text))
 point2 = shapely.geometry.Point(airspace.util.rawLatLonConv($c2.text))
 center = $circle_center.spoint
 $points = airspace.util.getArc2(center, point1, point2, direction)
}
	;
	
circle returns [polygon]
@init{
r=None
}
	: 
	   ^(CIRCLE circle_center (INT{r = float($INT.text)} | FLOAT {r = float($FLOAT.text)})){
	     $polygon = airspace.util.getCircle2($circle_center.spoint, r)
	   }
	;
