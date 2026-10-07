// Prepared firmware: physical execution is pending actual board access.
// ESP32 + DHT22 DATA on GPIO4, 3.3V, GND; 10k pull-up DATA to 3.3V
// for a bare sensor. Use Adafruit DHT sensor library + Unified Sensor.
#include <DHT.h>
DHT sensor(4, DHT22);
unsigned long sequence = 0;
void setup() { Serial.begin(115200); sensor.begin(); }
void loop() {
  delay(2100); // DHT22 sampling interval, not the 20Hz synthetic workload.
  float t = sensor.readTemperature();
  float h = sensor.readHumidity();
  if (isnan(t) || isnan(h)) return;
  Serial.printf("{\"sequence\":%lu,\"device_millis\":%lu,\"temperature_c\":%.3f,\"humidity_percent\":%.3f}\n", ++sequence, millis(), t, h);
}
