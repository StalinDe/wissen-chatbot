import os
from fastapi import FastAPI, Form, Response, Request
from dotenv import load_dotenv
from supabase import create_client, Client
from google.cloud import dialogflow
import uvicorn
import re

# --- 1. CONFIGURACIÓN INICIAL Y ENTORNO ---
load_dotenv()

# Inicializar Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuración de Dialogflow
DIALOGFLOW_PROJECT_ID = os.getenv("DIALOGFLOW_PROJECT_ID")
session_client = dialogflow.SessionsClient()

# Instancia de FastAPI
app = FastAPI(
    title="Chatbot Wissen Webhook",
    description="Backend con IA para la guía de trámites institucionales",
    version="3.0.0"
)

# --- 2. MOTOR COGNITIVO DE DIALOGFLOW ---
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

# --- 3. ENDPOINT PRINCIPAL - TWILIO WEBHOOK ---
@app.post("/webhook")
async def twilio_webhook(Body: str = Form(...), From: str = Form(...)):
    texto = Body.strip()
    numero_usuario = From.replace("whatsapp:", "") 
    
    response_text = ""
    media_url = None 

    usuario = supabase.table("usuarios").select("*").eq("telefono", numero_usuario).execute()
    
    if not usuario.data:
        supabase.table("usuarios").insert({
            "telefono": numero_usuario,
            "estado_embudo": "Pendiente_Datos"
        }).execute()
        
        response_text = (
            "¡Hola! Bienvenido al asistente virtual del Instituto Wissen. 🤖📚\n\n"
            "⚖️ *Aviso Legal:* Al continuar, autorizas al Instituto Wissen el tratamiento de tus datos personales según la LOPDP.\n\n"
            "Para brindarte una atención personalizada, por favor escribe tu *Nombre Completo y Número de Cédula* (Ej. Juan Pérez 0102030405).\n\n"
        )
        
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response><Message>{response_text}</Message></Response>"""
        return Response(content=twiml_response, media_type="application/xml")

    elif usuario.data[0].get("estado_embudo") == "Pendiente_Datos":
        if texto.upper() == "OMITIR":
            supabase.table("usuarios").update({
                "nombre_completo": "Omitido",
                "cedula": "Omitido",
                "estado_embudo": "Prospecto"
            }).eq("telefono", numero_usuario).execute()
        else:
            numeros = re.findall(r'\d+', texto)
            cedula_extraida = "".join(numeros) if numeros else "No especificada"
            
            letras = re.sub(r'\d+', '', texto).strip()
            nombre_extraido = letras if letras else "No especificado"

            supabase.table("usuarios").update({
                "nombre_completo": nombre_extraido,
                "cedula": cedula_extraida,
                "nombre_cedula": texto, 
                "estado_embudo": "Prospecto"
            }).eq("telefono", numero_usuario).execute()
            
        response_text = (
            "¡Gracias! Registro completado con éxito. ✅\n\n"
            "¿En qué te puedo ayudar hoy? Escribe el número de tu opción o dímelo con tus palabras:\n\n"
            "1️⃣ Conocer la oferta académica\n"
            "2️⃣ Información sobre una carrera\n"
            "3️⃣ Cursos de Educación Continua\n"
            "4️⃣ Iniciar mi proceso de matrícula\n"
            "5️⃣ Hablar con un asesor humano\n"
            "6️⃣ Solicitar un Certificado o Retiro"
        )
        
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response><Message>{response_text}</Message></Response>"""
        return Response(content=twiml_response, media_type="application/xml")

    intencion = detectar_intencion(DIALOGFLOW_PROJECT_ID, numero_usuario, texto)
    print(f"La IA detectó la intención: {intencion}")
    
    try:
        supabase.table("interacciones").insert({
            "telefono": numero_usuario,
            "mensaje": texto,
            "intencion": intencion
        }).execute()
    except Exception as e:
        print(f"Error al guardar log: {e}")

    # --- 4. ÁRBOL DE DECISIONES Y LÓGICA ---
    
    if intencion == "Default Welcome Intent":
        response_text = (
            "¡Hola! Bienvenido al asistente virtual del Instituto Wissen. 🤖📚\n\n"
            "⚖️ *Aviso de Privacidad:* Al continuar interactuando con este chat, autorizas al Instituto Wissen el tratamiento de tus datos personales según la LOPDP.\n\n"
            "¿En qué te puedo ayudar hoy? Escribe el número de tu opción o dímelo con tus propias palabras:\n\n"
            "1️⃣ Conocer la oferta académica completa\n"
            "2️⃣ Información sobre una carrera específica\n"
            "3️⃣ Cursos de Educación Continua\n"
            "4️⃣ Iniciar mi proceso de matrícula\n"
            "5️⃣ Hablar con un asesor humano\n"
            "6️⃣ Solicitar un Certificado o Retiro"
        )

    elif intencion == "Menu.Oferta" or texto == "1":
        response_text = (
            "📚 *Nuestra Oferta Académica 100% Virtual:*\n\n"
            "* Producción Industrial (2 años y medio)\n"
            "* Contabilidad y Asesoría Tributaria (2 años)\n"
            "* Administración (2 años)\n"
            "* Administración Deportiva (2 años)\n\n"
            "👉 Escribe *2* si deseas información detallada sobre alguna de estas carreras, o *Inicio* para volver al menú."
        )

    elif intencion == "Menu.Carrera" or texto == "2":
        response_text = (
            "🎓 *Inversión y Proceso de Matrícula:*\n\n"
            "* Matrícula: $90\n"
            "* Inscripción: $9\n"
            "* Colegiatura: $900 (Contamos con opciones de diferimiento)\n\n"
            "Si deseas iniciar tu inscripción, escribe *4* o la palabra *Matrícula*."
        )
        
    elif intencion == "Menu.Cursos" or texto == "3":
        response_text = (
            "📚 *Cursos de Educación Continua:*\n\n"
            "Actualmente estamos actualizando nuestro catálogo de cursos cortos. "
            "Por favor, escribe *5* para que un asesor te brinde la información más reciente."
        )

    elif intencion == "Menu.Matricula" or texto == "4":
        response_text = (
            "Perfecto, hablemos del proceso de Matriculación. 📋\n\n"
            "Para darte los requisitos correctos, por favor indícame tu perfil escribiendo una palabra:\n\n"
            "👉 Escribe *NUEVO* (Si eres aspirante por primera vez)\n"
            "👉 Escribe *ANTIGUO* (Si eres estudiante regular del instituto)"
        )

    elif intencion == "Matricula.Nuevo" or texto.upper() == "NUEVO":
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

    elif intencion == "Matricula.Antiguo" or texto.upper() == "ANTIGUO":
        response_text = (
            "📝 *Guía para Estudiantes Antiguos:*\n\n"
            "Para renovar tu matrícula, asegúrate de no tener valores pendientes y solicita la orden de pago actualizada.\n"
            "¿Deseas los números de cuenta para realizar tu depósito? Escribe *CUENTAS*."
        )

    elif intencion == "Tramite.Cuentas" or texto.upper() == "CUENTAS":
        response_text = (
            "🏦 *Cuentas Bancarias Oficiales - Instituto Wissen:*\n\n"
            "Te adjunto la imagen con todos nuestros datos bancarios.\n\n"
            "🚨 *Importante:* Una vez realizado tu pago, por favor envía la foto o captura de tu comprobante por este medio para registrarlo."
        )
        media_url = "https://raw.githubusercontent.com/StalinDe/wissen-chatbot/main/img/cuentas-wissen.jpeg"

    elif intencion == "Menu.Asesor" or texto == "5":
        response_text = (
            "👨‍💻 *Transferencia a Asesor Humano:*\n\n"
            "He notificado a nuestro equipo de admisiones. Un asesor humano leerá tu historial y se contactará contigo por este mismo chat en breve.\n\n"
            "(Horario de atención: Lunes a Viernes, 08:00 a 17:00)"
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
            "3. Realiza el pago correspondiente, sube el comprobante y da clic en Guardar.\n"
            "4. Descarga la *plantilla de formato* para retiro.\n"
            "5. Llena tus datos, fírmala y súbela en 'Seleccione archivo'.\n\n"
            "👉 *Nota:* En la misma pantalla del SGA podrás revisar si tu retiro fue aprobado."
        )

    else:
        response_text = (
            "Lo siento, aún estoy aprendiendo y no comprendí del todo tu solicitud. 😅\n\n"
            "Por favor, intenta decirlo de otra forma o escribe *'Inicio'* para ver el menú principal."
        )

    # --- 5. RESPUESTA XML PARA TWILIO ---
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

# --- 6. ARRANQUE DEL SERVIDOR ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)