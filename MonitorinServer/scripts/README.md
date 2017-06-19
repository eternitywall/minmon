# MinMon - scripts
Python script for parse informations from video cards and miners using MQTT broker.
> Usage: MinMon.py [OPTIONS] COMMAND [ARGS]...

## Configuration
The MinMon.py script can be configured using the minmon.cfg file that has to contain the following lines:
>[MQTT]
>hostname: broker.mqtt.url
>port: 1883

## amd commands
Command useful for get and set data from videocard.

### amd_get_speed     
Parse log for amd speed command.

### amd_set_speed     
Set speed for amd boards.Receive commands from MQTT queue and change the speeds in accord with the JSON received.
>./MinMon.py amd_set_speed

### amd_temperature   
Parse log for amd temperature command.

## Optiminer commands
Get data from optiminer logs.

### optiminer_parser  
Parse command on optiminer logs.

## Sgminer commands
Get data from sgminer API.

### sgminer_parser    
Get info from sgminer.
