grammar OpenAir;

options {
   language=Python;
}

tokens {
    INCLUDE='INCLUDE';
    TYPE='TYPE';
    TITLE='TITLE';
    TOPS='TOPS';
    BASE='BASE';
    POINT='POINT';
    ANTICLOCKWISE='ANTI-CLOCKWISE';
    CLOCKWISE='CLOCKWISE';
    RADIUS='RADIUS';
    CENTRE='CENTRE';
    TO='TO';

    EQ='=';
    
    FEET='F';
    AGL='AGL';
    AMSL='AMSL';
    FL='FL';
    SFC='SFC';
    UNL='UNL';
    
    NORTH='N';
    EAST='E';
    
    CTACTR='CTA/CTR';
    OTHER='OTHER';
    PROHIBITED='PROHIBITED';
    RESTRICTED='RESTRICTED';
    YES='YES';
    NO='NO';
}



zone
    : (include|title|type|tops|base)* geometry EOF   ;

title	:	(TITLE EQ (LETTER)+ EOL);

include	:	(INCLUDE EQ (YES|NO) EOL);
	
type	:	(TYPE EQ (CTACTR|OTHER|PROHIBITED|RESTRICTED) EOL);

tops	:	(TOPS EQ altitude EOL);
base	:	(BASE EQ altitude EOL);

altitude:	(ALTI)? (AGL|AMSL|FL|SFC|UNL);

geometry:	(point (point|arc)+) ;

point	:	(POINT EQ coords EOL);
arc	:	((CLOCKWISE|ANTICLOCKWISE) RADIUS EQ FLOAT CENTRE EQ coords TO EQ coords EOL);

coords	:	('N' INTEGER) ('E' INTEGER);

ALTI	:	(INTEGER 'F');
	
DIGIT   
	:  ( '0'..'9' ) ;
LETTER	
	:  ('a'..'z')|('A'..'Z') ;

FLOAT	:	
	(DIGIT)+ '.' (DIGIT)+;
	
INTEGER 
	:  (DIGIT)+ ;

//TITLE_NAME
//	:	 ('a'..'z'|'A'..'Z') ('a'..'z'|'A'..'Z'|'0'..'9'|'_'|'.'|' ')*;

EOL :  '\r'? '\n';

WS  : (' ' |'\t' )+ {$channel = HIDDEN;} ;

