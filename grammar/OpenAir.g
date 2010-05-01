//
//   airspace checker
//   Copyright (C) 2010  Marc Poulhiès
//
//   This program is free software: you can redistribute it and/or modify
//   it under the terms of the GNU General Public License as published by
//   the Free Software Foundation, either version 3 of the License, or
//   (at your option) any later version.
//
//   This program is distributed in the hope that it will be useful,
//   but WITHOUT ANY WARRANTY; without even the implied warranty of
//   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//   GNU General Public License for more details.
//
//   You should have received a copy of the GNU General Public License
//   along with this program.  If not, see <http://www.gnu.org/licenses/>.


//
// BEWARE, THIS GRAMMAR IS BROKEN. USE IT ONLY AS A BASIS
//

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

zone	:	aclass aname aceil afloor geometry;

aname 	:	ANAME EOL;
                       
aclass : 'AC'  ('R'|'Q'|'P'|'A'|'B'|'C'|'D'|'GP'|'CTR'|'W') EOL;

aceil	:	'AH' altitude EOL -> altitude;
afloor	:	'AL' altitude EOL -> altitude;

geometry:	(poly_point|circle|arc_coord|var_set|direction)+;

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
: 'AN ' (('A'..'Z')|('a'..'z')| ('0'..'9')|' '|'.'|'_')+;

INTEGER 
	:  ('0'..'9')+;

EOL :  '\r'? '\n';

//WS  : (' '){$channel=HIDDEN;};

LINE_COMMENT
  :  '*' ~( '\r' | '\n' )* {$channel=HIDDEN;}
  ;
