import cv2
import numpy as np
import pytesseract

def process_license_plate(image):
    try:
        npimg = np.frombuffer(image, np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        
        # Preprocesamiento de la imagen
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        # Aplicar OCR
        plate_text = pytesseract.image_to_string(thresh, config='--psm 8')
        plate_text = ''.join(filter(str.isalnum, plate_text))  # Limpiar caracteres especiales
        return plate_text
    except Exception as e:
        print(f"Error en el procesamiento de la imagen: {e}")
        return None
