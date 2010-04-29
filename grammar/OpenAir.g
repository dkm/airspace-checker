grammar OpenAir;

options {
  language=Python;
}

tokens {
    AC='AC';
    R='R';
    Q='Q';
    P='P';
    A='A';
    B='B';
    C='C';
    D='D';
    GP='GP';
    CTR='CTR';
    W='W';
    AN='AN';
    AH='AH';
    AL='AL';
    AT='AT';
    V='V';
    PLUS='+';
    MINUS='-';
    EQ='=';
    X='X';
    W='W';
    Z='Z';
    DP='DP';
    DA='DA';
    DB='DB';
    DC='DC';
    DY='DY';

    COLON=':';
    COMMA=',';
    FEET='F';
    AGL='AGL';
    AMSL='AMSL';
    FL='FL';
    SFC='SFC';
    UNL='UNL';
}

aclass : AC (R|Q|P|A|B|C|D|GP|CTR|W) EOL;

aceil	:	AH altitude EOL;
afloor	:	AL altitude EOL;

arc_coord	:	DB coords COMMA coords EOL;

// never used for french AS
arc_angle
	:	DA INTEGER COMMA INTEGER COMMA INTEGER EOL;
	
poly_point
	:	DP coords EOL;
	
// never used for french AS
label_coord
	:	AT coords EOL;
	
circle	:	DC FLOAT EOL;

var_set	:	V (direction|center|width|zoom) EOL;

direction
	:	D EQ (PLUS|MINUS);
center	:	X EQ coords;
width	:	W EQ FLOAT;
zoom	:	Z EQ FLOAT;

//never used for french AS
airway	:	DY coords EOL;

altitude:	(ALTI)? (AGL|AMSL|FL|SFC|UNL);

coords	:	coord 'N' coord 'E';

coord	:	INTEGER COLON INTEGER COLON INTEGER;

ALTI	:	(INTEGER 'F');
	
DIGIT   
	:  ( '0'..'9' ) ;
LETTER	
	:  ('a'..'z')|('A'..'Z') ;

FLOAT	:	
	(DIGIT)+ '.' (DIGIT)+;
	
INTEGER 
	:  (DIGIT)+ ;

EOL :  '\r'? '\n';

WS  : (' ' |'\t' )+ {$channel = HIDDEN;} ;

