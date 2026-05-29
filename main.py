import os
from fastapi import FastAPI, Form, Response
from dotenv import load_dotenv
from supabase import create_client, Client
import uvicorn

# 1. Cargar variables de entorno
load_dotenv()

# 2. Inicializar cliente de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(
    title="Chatbot Wissen Webhook",
    description="Backend inicial para la guía y asesoría de trámites institucionales en Wissen",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "project": "Chatbot Institucional Wissen",
        "stage": "Pilot - Matriculación (Con Supabase)"
    }

@app.post("/webhook")
async def twilio_webhook(Body: str = Form(...), From: str = Form(...)):
    message_body = Body.strip().lower()
    # Limpiamos el formato de Twilio para obtener solo el número
    numero_remitente = From.replace("whatsapp:", "") 
    
    # ==========================================
    # 3. BLOQUE DE REGISTRO EN SUPABASE (LOGS)
    # ==========================================
    try:
        supabase.table("logs").insert({
            "telefono": numero_remitente,
            "mensaje_recibido": message_body
        }).execute()
    except Exception as e:
        print(f"Error al guardar log en Supabase: {e}")
    # ==========================================

    response_text = ""
    media_url = None 

    if "hola" in message_body or "inicio" in message_body or "buenos dias" in message_body:
        response_text = (
            "¡Hola! Bienvenido al asistente virtual del Instituto Wissen. 🤖📚\n\n"
            "Estoy aquí para guiarte en tus trámites. ¿En qué te puedo asesorar hoy?\n\n"
            "Escribe el número de la opción que necesitas:\n"
            "1️⃣ *Información de Matriculación* 📝\n"
            "2️⃣ *Solicitud de Certificados* 📜"
        )
        
    elif "1" in message_body or "matri" in message_body:
        response_text = (
            "Perfecto, hablemos del proceso de *Matriculación*. \n\n"
            "Para darte los requisitos correctos, por favor indícame tu perfil escribiendo una palabra:\n\n"
            "👉 Escribe *NUEVO* (Si eres aspirante por primera vez)\n"
            "👉 Escribe *ANTIGUO* (Si eres estudiante regular del instituto)"
        )
        
    elif "nuevo" in message_body:
        response_text = (
            "📝 *Guía para Aspirantes Nuevos:*\n\n"
            "Para matricularte por primera vez en Wissen, debes reunir los siguientes requisitos:\n"
            "1. Copia de tu cédula de identidad a color.\n"
            "2. Título de bachiller o acta de grado debidamente refrendada.\n"
            "3. Dos fotografías tamaño carnet.\n\n"
            "💰 *Costos y Pagos:*\n"
            "El valor del arancel vigente te será detallado al elegir tu carrera.\n\n"
            "¿Deseas conocer los números de cuenta oficiales? Responde con la palabra *CUENTAS*."
        )
        
    elif "antiguo" in message_body:
        response_text = (
            "🎒 *Guía para Estudiantes Antiguos:*\n\n"
            "Si ya eres parte de la comunidad Wissen, tu proceso es muy ágil:\n"
            "1. No debes registrar valores pendientes del ciclo anterior.\n"
            "2. Ingresa a la plataforma y actualiza tu ficha de datos.\n\n"
            "¿Deseas conocer los números de cuenta oficiales? Responde con la palabra *CUENTAS*."
        )
        
    elif "cuenta" in message_body or "banco" in message_body:
        response_text = (
            "🏦 *Cuentas Bancarias Oficiales - Instituto Wissen:*\n\n"
            "Aquí te comparto la imagen con todos los detalles para tu depósito o transferencia. 👆\n\n"
            "🚨 *Paso Final:* Una vez realizado el pago, envía la foto del comprobante y tus nombres completos al WhatsApp que aparece en la imagen."
        )
        media_url = "https://github.com/StalinDe/wissen-chatbot/blob/main/img/cuentas-wissen.jpeg?raw=true" 
        
    elif "2" in message_body or "certi" in message_body:
        response_text = (
            "📜 *Asesoría para Solicitud de Certificados:*\n\n"
            "Para obtener tu Certificado de Alumno Regular:\n"
            "1. Debes estar legalmente matriculado.\n"
            "2. No registrar deudas vigentes.\n\n"
            "👉 *Cómo solicitarlo:* Ingresa al SGA con tus credenciales institucionales, posterior a eso dirigete a la seccion de solicitudes y completa el formulario correspondiente."
        )
        
    else:
        response_text = (
            "Lo siento, aún estoy aprendiendo y no comprendí ese comando.\n\n"
            "Por favor, escribe *Inicio* para regresar al menú principal."
        )

    if media_url:
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>
        <Body>{response_text}</Body>
        <Media>{media_url}</Media>
    </Message>
</Response>"""
    else:
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{response_text}</Message>
</Response>"""
    
    return Response(content=twiml_response, media_type="application/xml")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)