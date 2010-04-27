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

    AGL='AGL';
    AMSL='AMSL';
    FL='FL';
    SFC='SFC';
    UNL='UNL';
    
    CTACTR='CTA/CTR';
    OTHER='OTHER';
    PROHIBITED='PROHIBITED';
    RESTRICTED='RESTRICTED';
    YES='YES';
    NO='NO';
}



zone
    : include title EOF
    ;

title	:	(TITLE EQ YES EOL)
	;

include	:	(INCLUDE EQ YES EOL)
	;


EOL :  '\r'? '\n';

WS  : (' ' |'\t' )+ {$channel = HIDDEN;} ;

