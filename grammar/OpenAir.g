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


file
    : zone NEWLINE EOF
    ;

zone
    : INCLUDE WS* EQ WS* (YES|NO) WS*
    ;

NEWLINE
    : '\r'? '\n'
    ;

WS
    : (' '|'\t'|'\n'|'\r')+ {skip();}
    ;

ZONE_TITLE
    : ('a'..'z'|'A'..'Z'|'0'..'9'|'.'|' ')+'\r'? '\n'
    ;
