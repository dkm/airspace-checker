grammar OpenAir;

options {
    output=AST;
    //language=Python;
}

FLEVEL	:	'FL' '0'..'9'+
	;
	
ID  :	('a'..'z'|'A'..'Z'|'_') ('a'..'z'|'A'..'Z'|'0'..'9'|'_')*
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
	:	zone+
	;
	
zone	: 	
	aclass
	name
	  ((ceiling floor)|(floor ceiling))
	geometry
	;

aclass	:	'AC' ('A'|'C'|'CTR'|'D'|'E'|'GP'|'P'|'Q'|'R'|'W')
	;
	
name	:	AN_NAME
	;

ceiling :	'AH' altitude_specif
	;

floor	:	'AL' altitude_specif
	;
	
altitude_specif
	:
	  ((INT ('M'|'F'))? ('AGL'|'AMSL'|'SFC'))
	| FLEVEL
	| 'UNL'
	;
	
geometry
	: 
          (single_point | circle_arc)*
	| circle
	;
	
single_point
	:	'DP' coords
	;

circle_direction
	: 'V' 'D' '=' ('+'|'-')
	;
	
circle_center 
	: 'V' 'X' '=' coords
	;
	
circle_arc
	: circle_direction?
	  circle_center
	  'DB' coords ',' coords
	;
	
circle	
	: circle_direction?
	  circle_center
	  'DC' INT
	;

coords
	: INT ':' INT ':' INT ('N'|'S') INT ':' INT ':' INT ('E'|'W')
	;


