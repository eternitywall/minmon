#!/usr/bin/python
from time import sleep
import sys
import click # used for the command line interface 
import ConfigParser # used for configuration file 
import paho.mqtt.client as mqtt # used for comunication in MQTT
import json # used for create the payload for the MQTT messages
import os # used for call scripts
import socket

def linesplit(socket):
    buffer = socket.recv(4096)
    done = False
    while not done:
        more = socket.recv(4096)
        if not more:
            done = True
        else:
            buffer = buffer+more
    if buffer:
        return buffer

# Group for commands on optiminer
@click.group()
def optiminer():
    pass

@optiminer.command() # 
def optiminer_parser():
    """Parse command on optiminer logs"""
    for line in sys.stdin:
        if ('[GPU0]' in line) or ('[GPU1]' in line):
            if ('Share accepted!' in line):
                #[2017-02-13 12:04:03.012] [info] [GPU0] Share accepted! (93 / 93)
                data = line.split(' ')
                msg = '{"timestamp":"'+data[0][1:-1]+'","share":"accepted"}'
                #(result,mid)=mqttc.publish('iot/T/MinMon/I/000001/D/tempfan/F/json',msg,0)
                sleep(0.001)
            else:
                #[2017-02-13 12:04:00.139] [info] [GPU0]  71.2 I/s 134.2 S/s (5s) 71.6 I/s 133.7 S/s (1m)
                data = line.split(' ')
                msg = '{"timestamp":"'+data[0][1:]+' '+data[1][:-5]+'","GPU":'+data[3][4:-1]+',"hashrate":'+data[7]+',"miner":"optiminer"}'
                (result,mid) = mqttc.publish('iot/T/MinMon/I/000002/D/hashrate/F/json',msg,0)
                print(msg)
                sleep(0.001)

# Group for commands on sgminer
#@click.group()
#def sgminer():
#    pass

#@sgminer.command() #
@optiminer.command()
def sgminer_parser():
    """Get info from sgminer"""
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect(('127.0.0.1',int(4028)))
    s.send(json.dumps({"command":"gpu","parameter":"0"}))
    # s.send(json.dumps({"command":api_command[0]}))
    response = linesplit(s)
    response = response.replace('\x00','')
    response = json.loads(response)
    s.close()
    msg = '{"GPU":0,"hashrate":'+str(response["GPU"][0]["KHS 5s"]*1000)+',"miner":"sgminer"}'
    (result,mid) = mqttc.publish('iot/T/MinMon/I/000002/D/hashrate/F/json',msg,0)
    print(msg)
    sleep(0.001)
   
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect(('127.0.0.1',int(4028)))
    s.send(json.dumps({"command":"gpu","parameter":"1"}))
    # s.send(json.dumps({"command":api_command[0]}))
    response = linesplit(s)
    response = response.replace('\x00','')
    response = json.loads(response)
    s.close()
    msg = '{"GPU":1,"hashrate":'+str(response["GPU"][0]["KHS 5s"]*1000)+',"miner":"sgminer"}'
    (result,mid) = mqttc.publish('iot/T/MinMon/I/000002/D/hashrate/F/json',msg,0)
    print(msg)
    sleep(0.001)

# Group for commands on GPU boards
@click.group()
def amd():
    pass

@amd.command() #
def amd_temperature():
    """Parse log for amd temperature command"""
    GPU = ""
    for line in sys.stdin:
        if ('Sensor' in line):
            data = line.split('-')[1].split(' ')
            msg = '{"temperature":'+data[1]+',"GPU":'+GPU+',"fan":0,"miner":"optiminer"}'
            print(msg)
            (result,mid) = mqttc.publish('iot/T/MinMon/I/000002/D/tempfan/F/json',msg,0)
            sleep(0.001)
        elif ('Adapter' in line):
            data = line.split('-')[0].split(' ')
            GPU = data[1]
            print ("GPU "+GPU)

@amd.command() #
def amd_get_speed():
    """Parse log for amd speed command"""
    GPU = ""
    for line in sys.stdin:
        if ('Current Clocks' in line):
            data = line.split(':')[1].split(' ')
            msg = '{"core":'+data[4]+',"GPU":'+GPU+',"memory":'+data[15]+',"miner":"optiminer"}'
            (result,mid) = mqttc.publish('iot/T/MinMon/I/000002/D/speed/F/json',msg,0)
            sleep(0.001)
        elif ('Adapter' in line):
            data = line.split('-')[0].split(' ')
            GPU = data[1]
            print ("GPU "+GPU)

def on_connect(client, userdata, flags, rc): # handle manage successful connection on MQTT server 
    print("Connected with result code "+str(rc))
    client.subscribe('iot/T/MinMon/I/000002/C/speed/F/json') # register on command queue 

def on_message(client, userdata, msg): # handle for manage message receive
    print(msg.payload)
    parsed_json = json.loads(msg.payload)
    os.system("export DISPLAY=:0")
    os.system("xhost + 127.0.0.1")
    for i in parsed_json["d"]:
        os.system("amdconfig --od-setclocks="+str(i["core"])+","+str(i["mem"])+" --adapter="+str(i["gpu"]))

@amd.command() #
def amd_set_speed():
    """Set speed for amd boards"""
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.loop_forever()


cli = click.CommandCollection(sources=[optiminer, amd])

if __name__ == '__main__':
    # import from configuration file
    config = ConfigParser.RawConfigParser()
    config.read('minmon.cfg')
    MQTT_PORT = config.getint('MQTT', 'port')
    MQTT_HOSTNAME = config.get('MQTT', 'hostname')
    print("MQTT server "+MQTT_HOSTNAME+":"+str(MQTT_PORT))
    # connect to mqtt 
    mqttc = mqtt.Client()
    mqttc.connect(MQTT_HOSTNAME, MQTT_PORT, 60)
    mqttc.loop_start()
    # execute the command
    cli()
    # close mqtt connection
    mqttc.loop_stop()
    mqttc.disconnect()
