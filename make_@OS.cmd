@echo off
setlocal
echo ---------------------------------------------------
echo Generieren von CP/A ... @OS.COM
echo ---------------------------------------------------
DEL @OS.com
cpm m80 =bios/L
CPM m80 BIOS.ERL=BIOS
@set /p var=linkmt.com @os=cpabas,ccp,bdos,bios/p:
CPM linkmt @OS=CPABAS,CCP,BDOS,BIOS/p:%var%
del *.syp
del bios.erl
del bios.rel
echo ...................................................
echo Fertig !!!!!!
echo.
pause 
goto :eof
 
