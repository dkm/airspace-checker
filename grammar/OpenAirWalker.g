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
import geojson
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
	
geometry
	: 
                         (single_point | circle_arc)* 
	|  circle
	;
	
single_point returns [point]
	: COORDS {
	     $point = geojson.Point([airspace.util.rawLatLonConv($COORDS.text)])
	  }
	;

circle_direction
	:  ('+'|'-')
	;
	
circle_center 
	:  COORDS
	;
	
circle_arc
	:  ^(CIRCLE_ARC circle_center COORDS COORDS circle_direction?)
	;
	
circle	
	: 
	   ^(CIRCLE circle_center (INT | FLOAT))
	;
