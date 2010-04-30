grammar OpenAir;

options {
    output=AST;
    language=Python;
}

tokens {
   
    PLUS='+';
    MINUS='-';
    EQ='=';
 
    COLON=':';
    COMMA=',';
}

zone	:	aclass ANAME aceil afloor;

                       
aclass : 'AC'  ('R'|'Q'|'P'|'A'|'B'|'C'|'D'|'GP'|'CTR'|'W') EOL;

aceil	:	'AH'  altitude EOL;
afloor	:	'AL'  altitude EOL;

arc_coord	:	'DB'  coords COMMA coords EOL;

// never used for french AS
arc_angle
	:	'DA'  INTEGER COMMA INTEGER COMMA INTEGER EOL;
	
poly_point
	:	'DP'  coords EOL;
	
// never used for french AS
label_coord
	:	'AT'  coords EOL;
	
circle	:	'DC'  (INTEGER '.' INTEGER) EOL;

var_set	:	'V'  (direction|center|width|zoom) EOL;

direction
	:	'D' EQ (PLUS|MINUS);
center	:	'X' EQ coords;
width	:	'W' EQ (INTEGER '.' INTEGER);
zoom	:	'Z' EQ (INTEGER '.' INTEGER);

//never used for french AS
airway	:	'DY'  coords EOL;

altitude:	(alti)? ('AGL'|'AMSL'|'FL'|'SFC'|'UNL');

coords	:	coord  'N'  coord  'E';

coord	:	INTEGER COLON INTEGER COLON INTEGER;

alti	:	(INTEGER 'F');


ANAME
: 'AN ' (('A'..'Z')|('a'..'z')| ('0'..'9')|' '|'.'|'_')+ ~( '\r' | '\n' );

INTEGER 
	:  ('0'..'9')+;

EOL :  '\r'? '\n';

//WS  : (' '){$channel=HIDDEN;};

LINE_COMMENT
  :  '*' ~( '\r' | '\n' )* {$channel=HIDDEN;}
  ;
