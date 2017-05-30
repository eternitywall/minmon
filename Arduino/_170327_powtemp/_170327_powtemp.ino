#include <Ethernet.h>
#include <PubSubClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <avr/wdt.h>

const byte mac[] PROGMEM = {  0xDE, 0xED, 0xBA, 0xFE, 0xFE, 0xAA };
char buff[50];
EthernetClient ethClient;
PubSubClient client(ethClient);
long lastReconnectAttempt = 0;
float power, temp;
// Data wire is plugged into port 2 on the Arduino
#define ONE_WIRE_BUS 6
// Setup a oneWire instance to communicate with any OneWire devices (not just Maxim/Dallas temperature ICs)
OneWire oneWire(ONE_WIRE_BUS);
// Pass our oneWire reference to Dallas Temperature.
DallasTemperature sensors(&oneWire);
// light value
int light;
// Measuring AC Current Using ACS712
const int sensorIn = A4;
int mVperAmp = 100; // 185, use 100 for 20A Module and 66 for 30A Module
double Voltage = 0;
double VRMS = 0;
double AmpsRMS = 0;

float getVPP() {
  float result;
  int readValue;             //value read from the sensor
  int maxValue = 0;          // store max value here
  int minValue = 1024;          // store min value here
  uint32_t start_time = millis();
  while ((millis() - start_time) < 5000) { //sample for 5 sec
    readValue = analogRead(sensorIn);
    // see if you have a new maxValue
    if (readValue > maxValue) {
      /*record the maximum sensor value*/
      maxValue = readValue;
    }
    if (readValue < minValue) {
      /*record the maximum sensor value*/
      minValue = readValue;
    }
  }
  // Subtract min from max
  result = ((maxValue - minValue) * 5.0) / 1024.0;
  return result;
}

/*void callback(char* topic, byte* payload, unsigned int length) {
  // handle message arrived
  }*/

boolean reconnect() {
  Serial.println(F("MQTT reconnecting ... "));
  if (client.connect("arduinoClient", "guest", "guest")) {
    Serial.println(F("MQTT Connected!"));
    // Once connected, publish an announcement...
    //client.publish("outTopic","hello world");
    // ... and resubscribe
    //client.subscribe("inTopic");
  } else {
    Serial.println(F("MQTT not connected!"));
  }
  return client.connected();
}

void setup() {
  // watchdog 8 sec
  wdt_enable(WDTO_8S);
  Serial.begin(115200);
  Serial.println(F("Starting MinMon"));
  // start the Ethernet connection:
  Serial.print(F("Configuring ETH ... "));
  if (Ethernet.begin(mac) == 0) {
    Serial.println(F("Failed to configure Ethernet using DHCP!!!"));
    while (1) ;
  }
  wdt_reset();
  Serial.print(F("done with IP "));
  Serial.println(Ethernet.localIP());
  client.setServer("wpc.uk.to", 1883);
  //client.setCallback(callback);
  lastReconnectAttempt = 0;
  wdt_reset();
  pinMode(5, OUTPUT);
  pinMode(7, OUTPUT);
  pinMode(A0, OUTPUT);
  pinMode(A1, INPUT);
  pinMode(A2, OUTPUT);
  pinMode(A3, OUTPUT);
  pinMode(A4, INPUT);
  pinMode(A5, OUTPUT);

  digitalWrite(5, LOW);
  digitalWrite(7, HIGH);
  digitalWrite(A0, HIGH);
  digitalWrite(A2, LOW);
  digitalWrite(A3, HIGH);
  digitalWrite(A5, LOW);

  // Start up the library
  sensors.begin();
  wdt_reset();
}


void loop() {
  if (!client.connected()) {
    long now = millis();
    if (now - lastReconnectAttempt > 5000) {
      lastReconnectAttempt = now;
      // Attempt to reconnect
      if (reconnect()) {
        lastReconnectAttempt = 0;
      }
    }
    wdt_reset();
  } else {
    // Client connected
    client.loop();
  }

  // get power
  //inputStats.input(analogRead(A4));  // log to Stats function
  Voltage = getVPP();
  VRMS = (Voltage/2.0) *0.707; 
  AmpsRMS = (VRMS * 1000)/mVperAmp;
  power = AmpsRMS * 220;
  Serial.println(power);
  
  // get temperature
  sensors.requestTemperatures(); // Send the command to get temperatures
  temp = sensors.getTempCByIndex(0);
  if ((temp < 0) || (temp > 60)) temp = 0;

  // get light
  light = analogRead(A1);

  // send messages
  sprintf(buff, "{\"board\":1, \"power\":%d, \"temperature\":%d.%02d, \"light\":%d}", (int)power, (int)temp, (int)(temp * 100) % 100, light);
  Serial.println(buff);
 
  if (client.publish("iot/T/MinMon/I/000001/D/power/F/json", buff))
    //watchog reset
    wdt_reset();
}

