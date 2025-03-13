#include <WiFi.h>
#include <HTTPClient.h>
#include <ESP32Servo.h>
#include <WebServer.h>
#include <ArduinoJson.h>

// Configuración WiFi
const char *ssid = "Alumnes";
const char *password = "edu71243080";
const char *serverUrl = "http://172.16.5.21:81/actualizarplaza"; // URL de la API para actualizar la plaza

// Pines del sensor HC-SR04
const int trigPin = 18; // Pin de trigger del sensor
const int echoPin = 19; // Pin de echo del sensor

// Pines del servo
const int servoPin = 13; // Pin del servo

Servo servo; // Crear objeto servo

// Estado previo para evitar envíos innecesarios
bool ultimoEstado = true; // Estado inicial (libre)

// Crear un servidor web en el puerto 80
WebServer server(80);

void setup()
{
    Serial.begin(115200);
    WiFi.begin(ssid, password);

    // Configurar pines del sensor HC-SR04
    pinMode(trigPin, OUTPUT);
    pinMode(echoPin, INPUT);

    // Configuración del servo
    servo.attach(servoPin);
    servo.write(0); // Posición inicial del servo (cerrado)

    Serial.print("Conectando a WiFi...");
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(1000);
        Serial.print(".");
    }
    Serial.println("\n✅ Conectado a WiFi!");
    Serial.print("📡 Dirección IP de la ESP32: ");
    Serial.println(WiFi.localIP());

    // Configurar el endpoint para manejar la petición POST
    server.on("/abrir_barrera", HTTP_POST, manejarAbrirBarrera);

    // Iniciar el servidor
    server.begin();
    Serial.println("Servidor HTTP iniciado");
}

void loop()
{
    server.handleClient(); // Manejar las peticiones HTTP

    verificarWiFi(); // Verificar conexión WiFi

    float distance = medirDistancia();

    Serial.print("📏 Distancia medida: ");
    Serial.print(distance);
    Serial.println(" cm");

    if (distance < 10)
    {
        actualizarPlaza(false); // Plaza ocupada
    }
    else
    {
        actualizarPlaza(true); // Plaza libre
    }

    delay(5000);
}

// Función para medir la distancia con el HC-SR04
float medirDistancia()
{
    float suma = 0;
    int medicionesValidas = 0;
    int intentos = 5; // Número de intentos para promediar

    for (int i = 0; i < intentos; i++)
    {
        digitalWrite(trigPin, LOW);
        delayMicroseconds(2);
        digitalWrite(trigPin, HIGH);
        delayMicroseconds(10);
        digitalWrite(trigPin, LOW);

        long duration = pulseIn(echoPin, HIGH, 30000); // Timeout de 30ms para evitar bloqueos

        if (duration == 0)
        {
            Serial.println("⚠ Advertencia: No se detectó eco en intento " + String(i + 1));
            continue; // Saltar esta lectura si no hubo eco
        }

        float distance = (duration / 2.0) / 29.1;

        if (distance > 0 && distance < 400)
        { // Filtrar valores fuera de rango
            suma += distance;
            medicionesValidas++;
        }
        else
        {
            Serial.println("⚠ Lectura inválida: " + String(distance) + " cm");
        }
        delay(50);
    }

    if (medicionesValidas == 0)
    {
        return -1; // Devolver error si no hubo lecturas válidas
    }

    return suma / medicionesValidas; // Retornar promedio
}

// Función para actualizar el estado de la plaza en la base de datos
void actualizarPlaza(bool estado)
{
    if (estado == ultimoEstado)
    {
        Serial.println("ℹ El estado no ha cambiado, no se enviará petición.");
        return; // Evitar peticiones innecesarias
    }

    if (WiFi.status() == WL_CONNECTED)
    {
        HTTPClient http;
        http.begin(serverUrl);
        http.addHeader("Content-Type", "application/json");

        String jsonPayload = "{\"parking_id\": 1, \"estado\": " + String(estado ? "1" : "0") + "}";
        Serial.print("📤 Enviando JSON: ");
        Serial.println(jsonPayload);

        int httpResponseCode = http.POST(jsonPayload);

        if (httpResponseCode > 0)
        {
            Serial.print("✅ Respuesta del servidor: ");
            Serial.println(http.getString());
            ultimoEstado = estado; // Actualizar el estado almacenado
        }
        else
        {
            Serial.print("⚠ Error en la petición (código ");
            Serial.print(httpResponseCode);
            Serial.println(")");
        }

        http.end();
    }
    else
    {
        Serial.println("❌ No conectado a WiFi.");
    }
}

// Función para verificar y reconectar WiFi si es necesario
void verificarWiFi()
{
    if (WiFi.status() != WL_CONNECTED)
    {
        Serial.println("🔄 Reconectando a WiFi...");
        WiFi.disconnect();
        WiFi.reconnect();
        delay(5000);
    }
}

// Función para abrir y cerrar la barrera con el servo
void controlarBarrera(bool abrir)
{
    if (abrir)
    {
        servo.write(90); // Mover el servo a 90 grados (abrir)
        Serial.println("🚗 Barrera abierta");
        delay(5000);    // Mantener la barrera abierta por 5 segundos
        servo.write(0); // Mover el servo a 0 grados (cerrar)
        Serial.println("🚪 Barrera cerrada");
    }
    else
    {
        servo.write(0); // Mantener la barrera cerrada
        Serial.println("🚪 Barrera cerrada");
    }
}

// Función para manejar la petición POST para abrir la barrera
void manejarAbrirBarrera()
{
    if (server.hasArg("plain") == false)
    {
        server.send(400, "text/plain", "Cuerpo de la petición no encontrado");
        return;
    }

    String body = server.arg("plain");
    Serial.println("📥 Petición recibida: " + body);

    // Parsear el JSON recibido
    DynamicJsonDocument doc(1024);
    DeserializationError error = deserializeJson(doc, body);

    if (error)
    {
        server.send(400, "text/plain", "Error al parsear JSON");
        return;
    }

    String accion = doc["accion"];

    if (accion == "abrir")
    {
        controlarBarrera(true);
        server.send(200, "text/plain", "Barrera abierta");
    }
    else
    {
        server.send(400, "text/plain", "Acción no válida");
    }
}