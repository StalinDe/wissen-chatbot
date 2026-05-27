from fastapi import FastAPI, Form, Response
import uvicorn

app = FastAPI(
    title="Chatbot Wissen Webhook",
    description="Backend inicial para la guía y asesoría de trámites institucionales en Wissen",
    version="1.0.0"
)

@app.get("/")
def read_root():
    """
    Ruta de salud (Health Check) útil para que Render verifique que el servidor está encendido.
    """
    return {
        "status": "online",
        "project": "Chatbot Institucional Wissen",
        "stage": "Pilot - Matriculación"
    }

@app.post("/webhook")
async def twilio_webhook(Body: str = Form(...), From: str = Form(...)):
    """
    Webhook que recibe los mensajes desde el Sandbox de Twilio (WhatsApp).
    Procesa el texto y responde con la estructura TwiML (XML).
    """
    message_body = Body.strip().lower()
    
    response_text = ""

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
            "El valor del arancel vigente te será detallado al elegir tu carrera. El pago se realiza mediante depósito o transferencia bancaria.\n\n"
            "¿Deseas conocer los números de cuenta oficiales? Responde con la palabra *CUENTAS*."
        )
        
    elif "antiguo" in message_body:
        response_text = (
            "🎒 *Guía para Estudiantes Antiguos:*\n\n"
            "Si ya eres parte de la comunidad Wissen, tu proceso es muy ágil:\n"
            "1. No debes registrar valores pendientes (pensiones) del ciclo anterior.\n"
            "2. Debes ingresar a la plataforma interna y actualizar tu ficha de datos.\n\n"
            "¿Deseas conocer las fechas límite y los datos para el depósito? Responde con la palabra *CUENTAS*."
        )
        
    elif "cuenta" in message_body or "banco" in message_body:
        response_text = (
            "🏦 *Cuentas Bancarias Oficiales - Instituto Wissen:*\n\n"
            "Puedes realizar tu pago a través de transferencia o depósito en:\n"
            "• *Banco Pichincha* | Cuenta Corriente: XXXXXXXX\n"
            "• *Cooperativa Jardín Azuayo* | Cuenta de Ahorros: XXXXXXXX\n"
            "• A nombre de: Instituto Superior Tecnológico Wissen\n\n"
            "🚨 *Paso Final Importante:* Una vez realizado el pago, debes enviar la foto digitalizada del comprobante junto con tus nombres completos al correo institucional o al WhatsApp de Tesorería para que procedan con el registro oficial en el sistema."
        )
        
    elif "2" in message_body or "certi" in message_body:
        response_text = (
            "📜 *Asesoría para Solicitud de Certificados:*\n\n"
            "Para obtener tu Certificado de Alumno Regular, ten en cuenta lo siguiente:\n"
            "1. Debes estar legalmente matriculado en el periodo académico vigente.\n"
            "2. No debes registrar deudas vigentes en tesorería.\n\n"
            "👉 *Cómo solicitarlo:* Envía un correo electrónico formal a Secretaría General detallando tus nombres completos, número de cédula y el motivo de tu solicitud. El documento firmado digitalmente será emitido en un lapso de 48 horas laborables."
        )
        
    else:
        response_text = (
            "Lo siento, aún estoy aprendiendo y no comprendí ese comando. 😅\n\n"
            "Por favor, escribe *Inicio* para regresar al menú principal y ver las opciones de guía disponibles."
        )

    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{response_text}</Message>
</Response>"""
    
    return Response(content=twiml_response, media_type="application/xml")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)