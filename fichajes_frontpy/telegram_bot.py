from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from passlib.context import CryptContext

ROOT_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ROOT_ENV_FILE)

# Configuración
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")
USUARIOS_COLLECTION = os.getenv("USUARIOS_COLLECTION", "usuarios")
FICHAJES_COLLECTION = os.getenv("FICHAJES_COLLECTION", "fichajes")

# MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
usuarios_col = db[USUARIOS_COLLECTION]
fichajes_col = db[FICHAJES_COLLECTION]

# Bcrypt
pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Mensaje de bienvenida"""
    user = update.effective_user
    telegram_id = user.id
    
    # Buscar usuario en la base de datos
    usuario = usuarios_col.find_one({"telegram_id": telegram_id, "activo": True})
    
    if usuario:
        mensaje = f"👋 ¡Hola {usuario['nombre_completo']}!\n\n"
        mensaje += "Bienvenido al Sistema de Fichajes de CVKE.\n\n"
        mensaje += "Comandos disponibles:\n"
        mensaje += "/fichar - Registrar entrada o salida\n"
        mensaje += "/horas - Ver horas trabajadas hoy\n"
        mensaje += "/historial - Ver últimos fichajes\n"
        mensaje += "/ayuda - Mostrar ayuda\n"
    else:
        mensaje = "❌ Tu cuenta de Telegram no está vinculada.\n\n"
        mensaje += f"📝 Tu Telegram ID: `{telegram_id}`\n\n"
        mensaje += "Contacta con RRHH para vincular tu cuenta."
    
    await update.message.reply_text(mensaje)


async def fichar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /fichar - Mostrar botones para fichar"""
    telegram_id = update.effective_user.id
    
    # Verificar usuario
    usuario = usuarios_col.find_one({"telegram_id": telegram_id, "activo": True})
    
    if not usuario:
        await update.message.reply_text(
            "❌ Tu cuenta no está vinculada.\n"
            f"Tu Telegram ID: `{telegram_id}`\n"
            "Contacta con RRHH."
        )
        return
    
    # Botones de fichaje
    keyboard = [
        [
            InlineKeyboardButton("🟢 ENTRADA", callback_data="entrada"),
            InlineKeyboardButton("🔴 SALIDA", callback_data="salida")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👤 {usuario['nombre_completo']}\n"
        f"📅 {datetime.now().strftime('%d/%m/%Y')}\n"
        f"🕐 {datetime.now().strftime('%H:%M:%S')}\n\n"
        "Selecciona el tipo de fichaje:",
        reply_markup=reply_markup
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los clicks en los botones"""
    query = update.callback_query
    await query.answer()
    
    telegram_id = query.from_user.id
    tipo_fichaje = query.data
    
    # Verificar usuario
    usuario = usuarios_col.find_one({"telegram_id": telegram_id, "activo": True})
    
    if not usuario:
        await query.edit_message_text("❌ Usuario no encontrado.")
        return
    
    # Registrar fichaje
    now = datetime.now()
    fichaje = {
        "user_id": str(usuario["_id"]),
        "username": usuario["username"],
        "nombre_completo": usuario["nombre_completo"],
        "tipo": tipo_fichaje,
        "timestamp": now,
        "fecha": now.strftime("%Y-%m-%d"),
        "hora": now.strftime("%H:%M:%S"),
        "dia_semana": now.strftime("%A")
    }
    
    fichajes_col.insert_one(fichaje)
    
    # Calcular horas si es salida
    mensaje = ""
    if tipo_fichaje == "entrada":
        emoji = "🟢"
        mensaje = f"{emoji} **ENTRADA REGISTRADA**\n\n"
    else:
        emoji = "🔴"
        mensaje = f"{emoji} **SALIDA REGISTRADA**\n\n"
        
        # Calcular horas trabajadas
        fecha_hoy = now.strftime("%Y-%m-%d")
        fichajes_hoy = list(fichajes_col.find({
            "username": usuario["username"],
            "fecha": fecha_hoy
        }).sort("timestamp", 1))
        
        entradas = [f for f in fichajes_hoy if f['tipo'] == 'entrada']
        salidas = [f for f in fichajes_hoy if f['tipo'] == 'salida']
        
        if entradas and salidas:
            tiempo_total = 0.0
            for i in range(min(len(entradas), len(salidas))):
                entrada_time = entradas[i]['timestamp']
                salida_time = salidas[i]['timestamp']
                diferencia = (salida_time - entrada_time).total_seconds() / 3600
                tiempo_total += diferencia
            
            mensaje += f"⏱️ **Horas trabajadas hoy:** {round(tiempo_total, 2)}h\n\n"
    
    mensaje += f"👤 {usuario['nombre_completo']}\n"
    mensaje += f"📅 {fichaje['fecha']}\n"
    mensaje += f"🕐 {fichaje['hora']}\n"
    mensaje += f"📍 Departamento: {usuario.get('departamento', 'N/A')}"
    
    await query.edit_message_text(mensaje)


async def horas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /horas - Mostrar horas trabajadas hoy"""
    telegram_id = update.effective_user.id
    
    usuario = usuarios_col.find_one({"telegram_id": telegram_id, "activo": True})
    
    if not usuario:
        await update.message.reply_text("❌ Usuario no encontrado.")
        return
    
    # Calcular horas trabajadas hoy
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    fichajes_hoy = list(fichajes_col.find({
        "username": usuario["username"],
        "fecha": fecha_hoy
    }).sort("timestamp", 1))
    
    if len(fichajes_hoy) < 2:
        await update.message.reply_text(
            "ℹ️ Aún no hay suficientes fichajes para calcular horas.\n"
            f"Fichajes registrados hoy: {len(fichajes_hoy)}"
        )
        return
    
    entradas = [f for f in fichajes_hoy if f['tipo'] == 'entrada']
    salidas = [f for f in fichajes_hoy if f['tipo'] == 'salida']
    
    if not entradas or not salidas:
        await update.message.reply_text(
            "ℹ️ Necesitas al menos una entrada y una salida para calcular horas."
        )
        return
    
    tiempo_total = 0.0
    for i in range(min(len(entradas), len(salidas))):
        entrada_time = entradas[i]['timestamp']
        salida_time = salidas[i]['timestamp']
        diferencia = (salida_time - entrada_time).total_seconds() / 3600
        tiempo_total += diferencia
    
    mensaje = f"📊 **RESUMEN DE HOY**\n\n"
    mensaje += f"👤 {usuario['nombre_completo']}\n"
    mensaje += f"📅 {fecha_hoy}\n\n"
    mensaje += f"🟢 Entradas: {len(entradas)}\n"
    mensaje += f"🔴 Salidas: {len(salidas)}\n"
    mensaje += f"⏱️ **Horas trabajadas: {round(tiempo_total, 2)}h**"
    
    await update.message.reply_text(mensaje)


async def historial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /historial - Mostrar últimos fichajes"""
    telegram_id = update.effective_user.id
    
    usuario = usuarios_col.find_one({"telegram_id": telegram_id, "activo": True})
    
    if not usuario:
        await update.message.reply_text("❌ Usuario no encontrado.")
        return
    
    # Obtener últimos 10 fichajes
    fichajes = list(fichajes_col.find({
        "username": usuario["username"]
    }).sort("timestamp", -1).limit(10))
    
    if not fichajes:
        await update.message.reply_text("ℹ️ No tienes fichajes registrados.")
        return
    
    mensaje = f"📋 **HISTORIAL DE FICHAJES**\n\n"
    mensaje += f"👤 {usuario['nombre_completo']}\n\n"
    
    for i, f in enumerate(fichajes, 1):
        emoji = "🟢" if f['tipo'] == 'entrada' else "🔴"
        mensaje += f"{i}. {emoji} {f['tipo'].upper()}\n"
        mensaje += f"   📅 {f['fecha']} - 🕐 {f['hora']}\n\n"
    
    await update.message.reply_text(mensaje)


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ayuda - Mostrar ayuda"""
    mensaje = "🤖 **SISTEMA DE FICHAJES CVKE**\n\n"
    mensaje += "**Comandos disponibles:**\n\n"
    mensaje += "/start - Iniciar el bot\n"
    mensaje += "/fichar - Registrar entrada o salida\n"
    mensaje += "/horas - Ver horas trabajadas hoy\n"
    mensaje += "/historial - Ver últimos 10 fichajes\n"
    mensaje += "/ayuda - Mostrar esta ayuda\n\n"
    mensaje += "**¿Cómo funciona?**\n\n"
    mensaje += "1️⃣ Usa /fichar para registrar\n"
    mensaje += "2️⃣ Selecciona ENTRADA o SALIDA\n"
    mensaje += "3️⃣ Recibe confirmación inmediata\n"
    mensaje += "4️⃣ Consulta tus horas con /horas\n\n"
    mensaje += "💡 **Nota:** Tu cuenta debe estar vinculada por RRHH."
    
    await update.message.reply_text(mensaje)


def main():
    """Función principal del bot"""
    print("🤖 Iniciando Bot de Telegram...")
    
    # Crear aplicación
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Registrar handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("fichar", fichar))
    application.add_handler(CommandHandler("horas", horas))
    application.add_handler(CommandHandler("historial", historial))
    application.add_handler(CommandHandler("ayuda", ayuda))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print("✅ Bot iniciado correctamente")
    print("📱 Esperando mensajes...")
    
    # Iniciar bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
