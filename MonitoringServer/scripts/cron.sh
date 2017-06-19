#!/bin/sh
export DISPLAY=:0
xhost + 127.0.0.1
cd /home/casatta/optiminer-zcash/
/usr/bin/amdconfig --odgt --adapter=all 	| /home/casatta/optiminer-zcash/MinMon.py amd_temperature
/usr/bin/amdconfig --od-getclocks --adapter=all | /home/casatta/optiminer-zcash/MinMon.py amd_get_speed
/home/casatta/optiminer-zcash/MinMon.py sgminer_parser
