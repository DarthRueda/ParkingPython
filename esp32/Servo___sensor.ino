#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <Servo.h>

// Configuración del WiFi
const char *ssid = "TuSSID"; // Cambia esto por tu red WiFi
const char *password = "TuPassword";

// Configuración del Servo
Servo barrera;
const int SERVO_PIN = 4; // Pin GPIO donde está conectado el servo

// Configuración del Sensor HC-SR04
const int trigPin = 12; // Pin TRIG
const int echoPin = 13; // Pin ECHO
long duration, distance;

// Crear servidor en el puerto 80
AsyncWebServer server(80);

// Función para medir la distancia
long medirDistancia()
{
  // Enviar pulso al TRIG
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // Leer el pulso en el ECHO
  duration = pulseIn(echoPin, HIGH);
  // Calcular la distancia (en cm)
  distance = duration * 0.034 / 2;
  return distance;
}

void setup()
{
  Serial.begin(115200);

  // Conectar a WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConectado a WiFi.");
  Serial.print("IP local: ");
  Serial.println(WiFi.localIP());

  // Iniciar el servo
  barrera.attach(SERVO_PIN);
  barrera.write(0); // Posición inicial (barrera cerrada)

  // Configurar los pines del sensor HC-SR04
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  // Ruta para abrir la barrera
  server.on("/abrir_barrera", HTTP_POST, [](AsyncWebServerRequest *request)
            {
    Serial.println("Solicitud recibida: ¡Abriendo barrera!");

    // Mover el servo a 90 grados (abrir barrera)
    barrera.write(90);
    delay(3000);
    barrera.write(0); // Cerrar la barrera

    request->send(200, "application/json", "{\"message\":\"Barrera abierta\"}"); });

  // Iniciar servidor
  server.begin();
}

void loop()
{
  // Medir la distancia continuamente
  long distancia = medirDistancia();

  Serial.print("Distancia: ");
  Serial.println(distancia);

  // Si la distancia es menor a 10 cm (vehículo detectado)
  if (distancia < 10)
  {
    // Enviar una solicitud POST a Flask para actualizar la base de datos
    Serial.println("Vehículo detectado, enviando solicitud a Flask...");

    // Dirección de tu servidor Flask (asegúrate de que Flask esté corriendo)
    String url = "http://192.168.x.x/actualizarplaza"; // Cambia por la IP real de tu Flask

    // Enviar solicitud POST a Flask
    WiFiClient client;
    HTTPClient http;
    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");

    String payload = "{\"parking_id\": \"1\", \"estado\": \"0\"}"; // Cambia el parking_id según sea necesario
    int httpCode = http.POST(payload);

    if (httpCode > 0)
    {
      String response = http.getString();
      Serial.println("Respuesta de Flask: " + response);
    }
    else
    {
      Serial.println("Error en la solicitud POST a Flask");
    }

    http.end(); // Finalizar la solicitud HTTP
  }

  delay(500); // Espera entre mediciones del sensor
}
