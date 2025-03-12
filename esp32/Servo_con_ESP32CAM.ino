#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <Servo.h>

// Configuración del WiFi
const char* ssid = "Alumnes";      // Cambia esto por tu red WiFi
const char* password = "edu71243080";

// Configuración del Servo
Servo barrera;
const int SERVO_PIN = 4; // Pin GPIO donde está conectado el servo

// Crear servidor en el puerto 80
AsyncWebServer server(80);

void setup() {
    Serial.begin(115200);

    // Conectar a WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nConectado a WiFi.");
    Serial.print("IP local: ");
    Serial.println(WiFi.localIP());

    // Iniciar el servo
    barrera.attach(SERVO_PIN);
    barrera.write(0); // Posición inicial (barrera cerrada)

    // Ruta para abrir la barrera
    server.on("/abrir_barrera", HTTP_POST, [](AsyncWebServerRequest *request){
        Serial.println("Solicitud recibida: ¡Abriendo barrera!");

        // Mover el servo a 90 grados (abrir barrera)
        barrera.write(90);
        delay(3000); // Mantenerla abierta por 3 segundos
        barrera.write(0); // Cerrar la barrera

        request->send(200, "application/json", "{\"message\":\"Barrera abierta\"}");
    });

    // Iniciar servidor
    server.begin();
}

void loop() {
    // No es necesario código en loop(), todo se maneja con el servidor
}
