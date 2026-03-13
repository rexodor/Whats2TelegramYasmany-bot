import os
import re
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def convert_whatsapp_to_telegram(text):
    """WhatsApp (*bold*, _italic_) -> Telegram (**bold**, __italic__)"""
    if not text: return ""
    # Negrita
    text = re.sub(r'\*(?!\s)([^*]+)(?<!\s)\*', r'**\1**', text)
    # Cursiva
    text = re.sub(r'\_(?!\s)([^_]+)(?<!\s)\_', r'__\1__', text)
    return text

def convert_telegram_to_whatsapp(text):
    """Telegram (**bold**, __italic__) -> WhatsApp (*bold*, _italic_)"""
    if not text: return ""
    # Negrita (doble asterisco a uno)
    text = re.sub(r'\*\*(?!\s)([^*]+)(?<!\s)\*\*', r'*\1*', text)
    # Cursiva (doble guion bajo a uno)
    text = re.sub(r'\_\_(?!\s)([^_]+)(?<!\s)\_\_', r'_\1_', text)
    return text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /start."""
    welcome_text = (
        "👋 ¡Hola! Soy el Bot de Formato Bidireccional WhatsApp <-> Telegram.\n\n"
        "Puedo convertir formatos automáticamente:\n"
        "1. **De WhatsApp a Telegram:**\n"
        "   - `*negrita*` -> `**negrita**`\n"
        "   - `_cursiva_` -> `__cursiva__` \n\n"
        "2. **De Telegram a WhatsApp:**\n"
        "   - `**negrita**` -> `*negrita*` \n"
        "   - `__cursiva__` -> `_cursiva_` \n\n"
        "Simplemente envía tu texto y yo detectaré qué convertir."
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los mensajes de texto entrantes."""
    if not update.message.text:
        return

    original_text = update.message.text
    
    # Intentamos detectar qué tipo de conversión aplicar
    # Si contiene doble formato, probablemente es de Telegram
    if "**" in original_text or "__" in original_text:
        formatted_text = convert_telegram_to_whatsapp(original_text)
        direction = "🔄 De Telegram a WhatsApp"
    # Si contiene formato simple, probablemente es de WhatsApp
    elif "*" in original_text or "_" in original_text:
        formatted_text = convert_whatsapp_to_telegram(original_text)
        direction = "🔄 De WhatsApp a Telegram"
    else:
        formatted_text = original_text
        direction = None

    if direction and formatted_text != original_text:
        response = f"{direction}:\n\n{formatted_text}"
        # Para WhatsApp -> Telegram, queremos que Telegram renderice el formato
        # Para Telegram -> WhatsApp, queremos que el usuario copie el texto plano
        if "WhatsApp a Telegram" in direction:
            await update.message.reply_text(response, parse_mode='MarkdownV2')
        else:
            await update.message.reply_text(response)
    else:
        await update.message.reply_text(
            "No detecté ningún formato para convertir, pero aquí tienes tu texto original:\n\n" + original_text
        )

if __name__ == '__main__':
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not TOKEN:
        print("Error: No se encontró la variable de entorno TELEGRAM_BOT_TOKEN")
    else:
        application = ApplicationBuilder().token(TOKEN).build()
        
        application.add_handler(CommandHandler('start', start))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        
        print("Bot iniciado... Presiona Ctrl+C para detener.")
        application.run_polling()
