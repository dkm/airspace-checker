grammar OpenAir;

options {
    output=AST;
    language=Python;
    backtrack=true;
    memoize=true;
}


tokens {
        ZONES;
        ZONE;
        CLASS;
        ALTI;
        POLYGON;
        BASE_ALTI;
        CIRCLE;
        CIRCLE_ARC;
        NAME;
}

FLEVEL	:	'FL' '0'..'9'+
	;
	
ID  :	('a'..'z'|'A'..'Z'|'_') ('a'..'z'|'A'..'Z'|'0'..'9'|'_')*
    ;


COORDS
	: '0'..'9'+ ' '* ':'  ' '* '0'..'9'+ ' '* (':'|'.') ' '* '0'..'9'+ ' '* ('N'|'S'|'n'|'s') 
      ' '* '0'..'9'+ ' '* ':' ' '* '0'..'9'+ ' '* (':'|'.') ' '* '0'..'9'+ ' '* ('E'|'W'|'e'|'w')
	;
	
INT :	'0'..'9'+
    ;

FLOAT
    :   ('0'..'9')+ '.' ('0'..'9')* EXPONENT?
    |   '.' ('0'..'9')+ EXPONENT?
    |   ('0'..'9')+ EXPONENT
    ;

AN_NAME
	: 'AN' ~('\n'|'\r')* '\r'? '\n'
	;
	
COMMENT
    :   '//' ~('\n'|'\r')* '\r'? '\n' {$channel=HIDDEN;}
    |   '*' ~('\n'|'\r')* '\r'? '\n' {$channel=HIDDEN;}
    |   '/*' ( options {greedy=false;} : . )* '*/' {$channel=HIDDEN;}
    ;

WS  :   ( ' '
        | '\t'
        | '\r'
        | '\n'
        ) {$channel=HIDDEN;}
    ;

fragment
EXPONENT : ('e'|'E') ('+'|'-')? ('0'..'9')+ ;


oair_file 
	:	zone+ -> ^(ZONES zone+)
	;
	
zone	: 	
	aclass
	name
	  ((ceiling floor)|(floor ceiling))
	geometry
	 -> ^(ZONE aclass name ceiling floor geometry)
	;

aclass	:	'AC' (c='A'|c='C'|c='CTR'|c='D'|c='E'|c='GP'|c='P'|c='Q'|c='R'|c='W')
                                      -> ^(CLASS $c)
	;
	
name	:	AN_NAME -> ^(NAME AN_NAME)
	;

ceiling :	'AH'! altitude_specif
	;

floor	:	'AL'! altitude_specif
	;

frag_alti
	: INT (s='M'|s='F') -> ^(BASE_ALTI INT $s)
 	;
 	
altitude_specif
	:
	  (frag_alti (r='AGL'|r='AMSL'|r='SFC')) -> ^(ALTI frag_alti $r)
	| (frag_alti? 'SFC') -> ^(ALTI frag_alti? 'SFC')
	| FLEVEL -> ^(ALTI FLEVEL)
	| 'UNL' -> ^(ALTI 'UNL')
	;
	
geometry
	: 
          (single_point | circle_arc)* 
	| circle
	;
	
single_point
	:	'DP'! COORDS 
	;

circle_direction
	: 'V'! 'D'! '='! ('+'|'-')
	;
	
circle_center 
	: 'V'! 'X'! '='! COORDS
	;
	
circle_arc
	: circle_direction?
	  circle_center
	  'DB' c1=COORDS ',' c2=COORDS -> ^(CIRCLE_ARC circle_center $c1 $c2 circle_direction?)
	;
	
circle	
	: 
	  circle_center
	  'DC' (r=INT | r=FLOAT) -> ^(CIRCLE circle_center $r)
	;



