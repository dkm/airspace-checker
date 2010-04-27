mkdir -p python/generated 
cd grammar && antlr3 -o ../python/generated/ OpenAir.g && cd -
