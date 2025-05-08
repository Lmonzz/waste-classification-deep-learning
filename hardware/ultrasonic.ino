#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

//cho sensor voi camera
#define OUT D2
#define trigPin D5
#define echoPin D6 

//cho lcd
#define I2C_SDA D4  
#define I2C_SCL D1

LiquidCrystal_I2C lcd(0x27, 16, 2);

const char *ssid = "realme C51";
const char *password = "vanloc123";

ESP8266WebServer server(80);

long duration;
int distance;

void handleRoot() {
  const char* htmlContent = R"html(
    <!DOCTYPE html>
    <html>
      <head>
        <title>ESP8266 Web Server</title>
      </head>
      <body>
        <h1>Hello from ESP8266!</h1>
        <form action='/prediction' method='POST'>
          <label for='image_name'>Image Name:</label>
          <input type='text' id='image_name' name='image_name'>
          <br><br>
          <label for='predictions'>Predictions:</label>
          <input type='text' id='predictions' name='predictions'><br><br>
          <input type='submit' value='Submit'>
        </form>
      </body>
  )html";

  server.send(200, "text/html", htmlContent);
}

void handlePrediction() {
  String json_data = server.arg("plain");
  Serial.println("Received JSON data: " + json_data);

  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, json_data);

  if (error) {
    Serial.print("JSON parsing failed: ");
    Serial.println(error.c_str());
    server.send(400, "text/plain", "Bad JSON");
    return;
  }

  String result = doc["result"];
  Serial.print("Result: ");
  Serial.println(result);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(result);  // Show trash type
  
  server.send(200, "text/plain", "Prediction received");
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(OUT, OUTPUT);
  digitalWrite(OUT, LOW);

  delay(2000);
  Wire.begin(I2C_SDA, I2C_SCL);
  lcd.begin();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Trash system ready");

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  
  server.on("/", HTTP_GET, handleRoot);
  server.on("/prediction", HTTP_POST, handlePrediction);

  server.begin();
  Serial.println("HTTP server started");
}

void loop() {
  // put your main code here, to run repeatedly:
  server.handleClient();
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH);
  distance = duration*0.034/2;
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" cm");
  if (distance >= 5 && distance <= 15) {
    Serial.println("check out");
    digitalWrite(OUT, HIGH);      
    delay(500);                   
    digitalWrite(OUT, LOW);       
    delay(15000);
  }
  delay(1000);
}
