import os
import re
import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# --- CONFIGURACIÓN DE LOGGING ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- SERVIDOR WEB PARA RENDER (HEALTH CHECK) ---
# Render requiere que un "Web Service" escuche en un puerto, de lo contrario falla el despliegue.
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running!", 200

def run_flask():
    # Render asigna automáticamente un puerto en la variable de entorno PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- LÓGICA DE CONVERSIÓN ---
def convert_whatsapp_to_telegram(text):
    """WhatsApp (*bold*, _italic_) -> Telegram (**bold**, __italic__)"""
    if not text: return ""
    text = re.sub(r'\*(?!\s)([^*]+)(?<!\s)\*', r'**\1**', text)
    text = re.sub(r'\_(?!\s)([^_]+)(?<!\s)\_', r'__\1__', text)
    return text

def convert_telegram_to_whatsapp(text):
    """Telegram (**bold**, __italic__) -> WhatsApp (*bold*, _italic_)"""
    if not text: return ""
    text = re.sub(r'\*\*(?!\s)([^*]+)(?<!\s)\*\*', r'*\1*', text)
    text = re.sub(r'\_\_(?!\s)([^_]+)(?<!\s)\_\_', r'_\1_', text)
    return text

# --- MANEJADORES DEL BOT ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 ¡Hola! Soy el Bot de Formato Bidireccional WhatsApp <-> Telegram.\n\n"
        "Puedo convertir formatos automáticamente:\n"
        "1. **De WhatsApp a Telegram:** `*negrita*` -> `**negrita**`\n"
        "2. **De Telegram a WhatsApp:** `**negrita**` -> `*negrita*` \n\n"
        "Simplemente envía tu texto."
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text: return
    original_text = update.message.text
    
    if "**" in original_text or "__" in original_text:
        formatted_text = convert_telegram_to_whatsapp(original_text)
        direction = "🔄 De Telegram a WhatsApp"
    elif "*" in original_text or "_" in original_text:
        formatted_text = convert_whatsapp_to_telegram(original_text)
        direction = "🔄 De WhatsApp a Telegram"
    else:
        formatted_text = original_text
        direction = None

    if direction and formatted_text != original_text:
        response = f"{direction}:\n\n{formatted_text}"
        if "WhatsApp a Telegram" in direction:
            await update.message.reply_text(response, parse_mode='MarkdownV2')
        else:
            await update.message.reply_text(response)
    else:
        await update.message.reply_text("No detecté formato para convertir:\n\n" + original_text)

# --- INICIO DEL BOT ---
if __name__ == '__main__':
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not TOKEN:
        print("Error: No se encontró la variable de entorno TELEGRAM_BOT_TOKEN")
    else:
        # 1. Iniciar Flask en un hilo separado para el Health Check de Render
        threading.Thread(target=run_flask, daemon=True).start()
        
        # 2. Iniciar el Bot de Telegram
        application = ApplicationBuilder().token(TOKEN).build()
        application.add_handler(CommandHandler('start', start))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        
        print("Bot y Servidor Web iniciados...")
        application.run_polling()
