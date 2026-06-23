import os
from fastapi import FastAPI, Form, Response, Request
from dotenv import load_dotenv
from supabase import create_client, Client
from google.cloud import dialogflow
import uvicorn

# 1. Cargar variables de entorno
load_dotenv()

# 2. Inicializar cliente de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 3. Configuración de Dialogflow
DIALOGFLOW_PROJECT_ID = os.getenv("DIALOGFLOW_PROJECT_ID")
session_client = dialogflow.SessionsClient()

app = FastAPI(
    title="Chatbot Wissen Webhook",
    description="Backend con IA para la guía de trámites institucionales",
    version="3.0.0"
)

# --- FUNCIÓN PARA CONSULTAR A LA IA ---
def detectar_intencion(project_id, session_id, texto, language_code="es"):
    try:
        session = session_client.session_path(project_id, session_id)
        text_input = dialogflow.TextInput(text=texto, language_code=language_code)
        query_input = dialogflow.QueryInput(text=text_input)
        
        response = session_client.detect_intent(
            request={"session": session, "query_input": query_input}
        )
        return response.query_result.intent.display_name
    except Exception as e:
        print(f"Error conectando con Dialogflow: {e}")
        return "Error"

@app.post("/webhook")
async def twilio_webhook(request: Request):
    form_data = await request.form()
    texto = form_data.get("Body", "").strip()
    numero_usuario = form_data.get("From", "")
    
    intencion = detectar_intencion(DIALOGFLOW_PROJECT_ID, numero_usuario, texto)
    print(f"La IA detectó la intención: {intencion}")

    try:
        usuario = supabase.table("usuarios").select("telefono").eq("telefono", numero_usuario).execute()
        if not usuario.data:
            supabase.table("usuarios").insert({"telefono": numero_usuario}).execute()
            print("Nuevo lead registrado en la tabla usuarios.")

        supabase.table("interacciones").insert({
            "telefono": numero_usuario,
            "mensaje": texto,
            "intencion": intencion
        }).execute()
        
    except Exception as e:
        print(f"Error al guardar en Supabase: {e}")

    response_text = ""
    media_url = None

    # --- LÓGICA BASADA EN INTENCIONES (IA) ---
    if intencion == "Default Welcome Intent":
        response_text = (
            "¡Hola! Bienvenido al asistente virtual del Instituto Wissen. 🤖📚\n\n"
            "⚖️ *Aviso de Privacidad:* Al continuar interactuando con este chat, autorizas al Instituto Wissen el tratamiento de tus datos personales (número de teléfono e historial de consultas) de acuerdo con la Ley Orgánica de Protección de Datos Personales (LOPDP), con fines estrictamente informativos y de admisión.\n\n"
            "¿En qué te puedo ayudar hoy? Escribe con tus propias palabras, por ejemplo:\n"
            "👉 _'Quiero información para matricularme'_\n"
            "👉 _'Necesito sacar un certificado'_\n"
            "👉 _'Quiero retirar una materia'_"
        )
        
    elif intencion == "Tramite.Matriculacion":
        response_text = (
            "💰 *Inversión y Proceso de Matrícula:*\n\n"
            "• *Matrícula:* $90\n"
            "• *Inscripción:* $9\n"
            "• *Colegiatura:* $900 (Contamos con opciones de diferimiento)\n\n"
            "🏦 *Cuentas Bancarias Oficiales:*\n"
            "Banco Guayaquil | CTA CORRIENTE: 4900 1685\n\n"
            "🚨 *Paso Final:* Una vez realizado el pago, envía tu comprobante por este medio para validar y enviarte tu formulario de registro (SGA).\n"
        )

    elif intencion == "Tramite.Certificados":
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

    elif intencion == "Tramite.Retiros":
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
        # Default Fallback Intent
        response_text = (
            "Lo siento, aún estoy aprendiendo y no comprendí del todo tu solicitud. 😅\n\n"
            "Por favor, intenta decirlo de otra forma o escribe *'Inicio'* para ver las opciones principales."
        )

    # --- CONSTRUCCIÓN DE RESPUESTA XML ---
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