@rem Automatically generated by nMigen 0.3.dev203+g74fce87. Do not edit.
@echo off
if defined NMIGEN_ENV_IceStorm call %NMIGEN_ENV_IceStorm%
if [%YOSYS%] equ [""] set YOSYS=
if [%YOSYS%] equ [] set YOSYS=yosys
if [%NEXTPNR_ICE40%] equ [""] set NEXTPNR_ICE40=
if [%NEXTPNR_ICE40%] equ [] set NEXTPNR_ICE40=nextpnr-ice40
if [%ICEPACK%] equ [""] set ICEPACK=
if [%ICEPACK%] equ [] set ICEPACK=icepack
%YOSYS% -q -l top.rpt top.ys || exit /b
%NEXTPNR_ICE40% --quiet --log top.tim --lp8k --package cm81 --json top.json --pcf top.pcf --asc top.asc || exit /b
%ICEPACK% top.asc top.bin || exit /b