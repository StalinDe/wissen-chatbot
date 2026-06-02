import os
from fastapi import FastAPI, Form, Response
from dotenv import load_dotenv
from supabase import create_client, Client
import uvicorn

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(
    title="Chatbot Wissen Webhook",
    description="Backend para la guía y asesoría de trámites institucionales en Wissen",
    version="2.0.0"
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "project": "Chatbot Institucional Wissen",
        "stage": "Pilot V2 - Flujos Completos"
    }

@app.post("/webhook")
async def twilio_webhook(Body: str = Form(...), From: str = Form(...)):
    message_body = Body.strip().lower()
    numero_remitente = From.replace("whatsapp:", "") 
    
    # ==========================================
    # REGISTRO EN SUPABASE 
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

    # ==========================================
    # LÓGICA DE MENÚ Y RESPUESTAS
    # ==========================================
    if "hola" in message_body or "inicio" in message_body or "menu" in message_body or "menú" in message_body:
        response_text = (
            "¡Hola! Bienvenido al asistente virtual del Instituto Wissen. 🤖📚\n\n"
            "¿En qué te puedo ayudar hoy? Escribe el *número* de la opción que necesitas:\n\n"
            "1️⃣ Conocer la oferta académica completa\n"
            "2️⃣ Información sobre una carrera específica\n"
            "3️⃣ Cursos de Educación Continua\n"
            "4️⃣ Iniciar mi proceso de matrícula\n"
            "5️⃣ Hablar con un asesor humano\n\n"
            "*(También puedes escribirme palabras como 'Certificados' o 'Retiro')*"
        )
        
    elif "1" in message_body or "oferta" in message_body:
        response_text = (
            "📚 *Nuestra Oferta Académica 100% Virtual:*\n\n"
            "• *Producción Industrial* (2 años y medio)\n"
            "• *Contabilidad y Asesoría Tributaria* (2 años)\n"
            "• *Administración* (2 años)\n"
            "• *Administración Deportiva* (2 años)\n\n"
            "👉 Escribe *2* si deseas información detallada sobre alguna de estas carreras, o *Inicio* para volver al menú."
        )

    elif "2" in message_body or "carrera" in message_body:
        response_text = (
            "🎓 *Información de Carrera:*\n\n"
            "Cada una de nuestras carreras está diseñada para el mercado laboral actual con una modalidad 100% online.\n\n"
            "Pronto podré enviarte la malla curricular exacta de cada una. Por ahora, si deseas conocer los costos, escribe *4* o escribe *Inicio* para regresar."
        )

    elif "3" in message_body or "cursos" in message_body:
        response_text = (
            "🚀 *Cursos de Educación Continua:*\n\n"
            "Actualmente estamos actualizando nuestra parrilla de cursos cortos. Si deseas hablar con un asesor para conocer los disponibles esta semana, escribe *5*."
        )
        
    elif "4" in message_body or "matri" in message_body:
        response_text = (
            "💰 *Inversión y Proceso de Matrícula:*\n\n"
            "• *Matrícula:* $90\n"
            "• *Inscripción:* $9\n"
            "• *Colegiatura:* $900 (Contamos con opciones de diferimiento)\n\n"
            "🏦 *Cuentas Bancarias Oficiales:*\n"
            "Banco Guayaquil | CTA CORRIENTE: 4900 1685\n\n"
            "🚨 *Paso Final:* Una vez realizado el pago, envía tu comprobante por este medio para validar y enviarte tu formulario de registro (SGA).\n"
            "Escribe *Inicio* para volver al menú."
        )
        
        media_url = "https://github.com/StalinDe/wissen-chatbot/blob/main/img/cuentas-wissen.jpeg?raw=true"

    elif "5" in message_body or "asesor" in message_body or "humano" in message_body:
        response_text = (
            "👨‍💻 *Transferencia a Asesor Humano:*\n\n"
            "He notificado a nuestro equipo de admisiones. Un asesor humano leerá tu historial y se contactará contigo por este mismo chat en breve.\n\n"
            "*(Horario de atención: Lunes a Viernes, 08:00 a 17:00)*"
        )

    elif "certificado" in message_body or "certificados" in message_body:
        response_text = (
            "📜 *Proceso para Petición de Emisión de Certificados:*\n\n"
            "Sigue estos pasos en tu portal:\n"
            "1. Ingresa al sistema *SGA*.\n"
            "2. Busca la opción *'Solicitudes Institucionales'* y escoge el tipo de solicitud.\n"
            "3. Realiza el pago (si aplica), sube el comprobante en 'Seleccione un archivo' y da clic en Guardar.\n"
            "4. Descarga la plantilla de formato del certificado deseado.\n"
            "5. Llena todos los datos, fírmala y súbela en 'Seleccione archivo'.\n\n"
            "👉 *Nota:* En la misma pantalla del SGA podrás revisar el estado de tu solicitud."
        )

    elif "retiro" in message_body or "retirar" in message_body:
        response_text = (
            "⚠️ *Proceso para Retiro de Asignatura:*\n\n"
            "Sigue estos pasos cuidadosamente:\n"
            "1. Ingresa al sistema *SGA*.\n"
            "2. Busca la opción *'Solicitudes Institucionales'* y elige tu solicitud.\n"
            "3. Realiza el pago correspondiente, sube el comprobante en 'Seleccione un archivo' y da clic en Guardar.\n"
            "4. Descarga la *plantilla de formato* para retiro.\n"
            "5. Llena todos tus datos, fírmala y súbela en 'Seleccione archivo'.\n\n"
            "👉 *Nota:* En la misma pantalla del SGA podrás revisar si tu retiro fue aprobado."
        )

    else:
        response_text = (
            "Lo siento, aún estoy aprendiendo y no comprendí ese comando. 😅\n\n"
            "Por favor, escribe *Inicio* para regresar al menú principal y ver las opciones disponibles."
        )

    # ==========================================
    # CONSTRUCCIÓN DE RESPUESTA XML
    # ==========================================
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