"""
Bot de Telegram para Sistema de Fichajes
Permite a los empleados fichar desde Telegram
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

# Añadir el directorio del backend al path
backend_dir = Path(__file__).parent.parent / "fichajes_backpy"
sys.path.insert(0, str(backend_dir))

ROOT_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ROOT_ENV_FILE)

# Configuración
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "CVKE")

# Conexión a MongoDB
client = MongoClient(MONGO_URL)
db = client[DATABASE_NAME]
usuarios_col = db.usuarios
fichajes_col = db.fichajes


def obtener_usuario_por_telegram_id(telegram_id: int):
    """Obtiene un usuario por su Telegram ID"""
    return usuarios_col.find_one({"telegram_id": telegram_id, "activo": True})


def registrar_fichaje(usuario_id: str, tipo: str, telegram_username: str):
    """Registra un fichaje en la base de datos"""
    fichaje = {
        "usuario_id": usuario_id,
        "tipo": tipo,
        "timestamp": datetime.now(),
        "origen": "telegram",
        "telegram_username": telegram_username,
        "latitud": None,
        "longitud": None
    }
    
    result = fichajes_col.insert_one(fichaje)
    return result.inserted_id


def obtener_ultimo_fichaje(usuario_id: str):
    """Obtiene el último fichaje de un usuario"""
    return fichajes_col.find_one(
        {"usuario_id": usuario_id},
        sort=[("timestamp", -1)]
    )


def obtener_fichajes_hoy(usuario_id: str):
    """Obtiene los fichajes de hoy de un usuario"""
    hoy_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return list(fichajes_col.find({
        "usuario_id": usuario_id,
        "timestamp": {"$gte": hoy_inicio}
    }).sort("timestamp", 1))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Inicia el bot"""
    telegram_id = update.effective_user.id
    telegram_username = update.effective_user.username or "Sin username"
    
    usuario = obtener_usuario_por_telegram_id(telegram_id)
    
    if not usuario:
        await update.message.reply_text(
            f"👋 ¡Hola!\n\n"
            f"⚠️ Tu cuenta de Telegram no está vinculada al sistema.\n\n"
            f"📱 Tu Telegram ID es: `{telegram_id}`\n\n"
            f"Por favor, contacta con Recursos Humanos para que vinculen tu cuenta.",
            parse_mode="Markdown"
        )
        return
    
    keyboard = [
        [InlineKeyboardButton("🟢 Fichar ENTRADA", callback_data='fichar_entrada')],
        [InlineKeyboardButton("🔴 Fichar SALIDA", callback_data='fichar_salida')],
        [InlineKeyboardButton("📋 Ver fichajes de hoy", callback_data='ver_fichajes_hoy')],
        [InlineKeyboardButton("ℹ️ Mi información", callback_data='mi_info')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 ¡Hola {usuario.get('nombre_completo')}!\n\n"
        f"Bienvenido al sistema de fichajes.\n"
        f"¿Qué deseas hacer?",
        reply_markup=reply_markup
    )


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ayuda - Muestra ayuda"""
    await update.message.reply_text(
        "📚 *Comandos disponibles:*\n\n"
        "/start - Inicia el bot y muestra el menú principal\n"
        "/entrada - Registra una entrada\n"
        "/salida - Registra una salida\n"
        "/hoy - Muestra tus fichajes de hoy\n"
        "/info - Muestra tu información\n"
        "/ayuda - Muestra esta ayuda",
        parse_mode="Markdown"
    )


async def fichar_entrada_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /entrada - Registra una entrada"""
    telegram_id = update.effective_user.id
    telegram_username = update.effective_user.username or "Sin username"
    
    usuario = obtener_usuario_por_telegram_id(telegram_id)
    
    if not usuario:
        await update.message.reply_text(
            "❌ Tu cuenta no está vinculada al sistema. Usa /start para más información."
        )
        return
    
    # Verificar último fichaje
    ultimo_fichaje = obtener_ultimo_fichaje(str(usuario['_id']))
    
    if ultimo_fichaje and ultimo_fichaje.get('tipo') == 'entrada':
        await update.message.reply_text(
            "⚠️ Ya registraste una ENTRADA. Debes registrar una SALIDA primero.\n\n"
            "Usa /salida para registrar tu salida."
        )
        return
    
    # Registrar entrada
    fichaje_id = registrar_fichaje(str(usuario['_id']), 'entrada', telegram_username)
    hora = datetime.now().strftime('%H:%M:%S')
    
    await update.message.reply_text(
        f"✅ *ENTRADA registrada exitosamente*\n\n"
        f"🕐 Hora: {hora}\n"
        f"👤 Usuario: {usuario.get('nombre_completo')}\n"
        f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y')}",
        parse_mode="Markdown"
    )


async def fichar_salida_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /salida - Registra una salida"""
    telegram_id = update.effective_user.id
    telegram_username = update.effective_user.username or "Sin username"
    
    usuario = obtener_usuario_por_telegram_id(telegram_id)
    
    if not usuario:
        await update.message.reply_text(
            "❌ Tu cuenta no está vinculada al sistema. Usa /start para más información."
        )
        return
    
    # Verificar último fichaje
    ultimo_fichaje = obtener_ultimo_fichaje(str(usuario['_id']))
    
    if ultimo_fichaje and ultimo_fichaje.get('tipo') == 'salida':
        await update.message.reply_text(
            "⚠️ Ya registraste una SALIDA. Debes registrar una ENTRADA primero.\n\n"
            "Usa /entrada para registrar tu entrada."
        )
        return
    
    if not ultimo_fichaje or ultimo_fichaje.get('tipo') != 'entrada':
        await update.message.reply_text(
            "⚠️ Debes registrar una ENTRADA primero.\n\n"
            "Usa /entrada para registrar tu entrada."
        )
        return
    
    # Registrar salida
    fichaje_id = registrar_fichaje(str(usuario['_id']), 'salida', telegram_username)
    hora = datetime.now().strftime('%H:%M:%S')
    
    # Calcular horas trabajadas
    entrada_time = ultimo_fichaje.get('timestamp')
    salida_time = datetime.now()
    horas = (salida_time - entrada_time).total_seconds() / 3600
    
    await update.message.reply_text(
        f"✅ *SALIDA registrada exitosamente*\n\n"
        f"🕐 Hora: {hora}\n"
        f"👤 Usuario: {usuario.get('nombre_completo')}\n"
        f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y')}\n"
        f"⏱️ Horas trabajadas: {horas:.2f}h",
        parse_mode="Markdown"
    )


async def ver_fichajes_hoy_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /hoy - Muestra fichajes de hoy"""
    telegram_id = update.effective_user.id
    
    usuario = obtener_usuario_por_telegram_id(telegram_id)
    
    if not usuario:
        await update.message.reply_text(
            "❌ Tu cuenta no está vinculada al sistema. Usa /start para más información."
        )
        return
    
    fichajes_hoy = obtener_fichajes_hoy(str(usuario['_id']))
    
    if not fichajes_hoy:
        await update.message.reply_text(
            "ℹ️ No has registrado fichajes hoy."
        )
        return
    
    mensaje = f"📋 *Tus fichajes de hoy:*\n\n"
    
    for fichaje in fichajes_hoy:
        tipo = fichaje.get('tipo').upper()
        hora = fichaje.get('timestamp').strftime('%H:%M:%S')
        emoji = "🟢" if tipo == "ENTRADA" else "🔴"
        mensaje += f"{emoji} {tipo}: {hora}\n"
    
    # Calcular horas trabajadas
    entradas = [f for f in fichajes_hoy if f.get('tipo') == 'entrada']
    salidas = [f for f in fichajes_hoy if f.get('tipo') == 'salida']
    
    if entradas and salidas:
        total_horas = 0
        for i in range(min(len(entradas), len(salidas))):
            entrada_time = entradas[i].get('timestamp')
            salida_time = salidas[i].get('timestamp')
            total_horas += (salida_time - entrada_time).total_seconds() / 3600
        
        mensaje += f"\n⏱️ *Horas trabajadas:* {total_horas:.2f}h"
    
    await update.message.reply_text(mensaje, parse_mode="Markdown")


async def mi_info_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /info - Muestra información del usuario"""
    telegram_id = update.effective_user.id
    
    usuario = obtener_usuario_por_telegram_id(telegram_id)
    
    if not usuario:
        await update.message.reply_text(
            "❌ Tu cuenta no está vinculada al sistema. Usa /start para más información."
        )
        return
    
    # Contar fichajes totales
    total_fichajes = fichajes_col.count_documents({"usuario_id": str(usuario['_id'])})
    
    mensaje = (
        f"👤 *Mi Información*\n\n"
        f"📝 Nombre: {usuario.get('nombre_completo')}\n"
        f"👤 Username: {usuario.get('username')}\n"
        f"📧 Email: {usuario.get('email')}\n"
        f"🏢 Departamento: {usuario.get('departamento')}\n"
        f"📱 Telegram ID: {usuario.get('telegram_id')}\n"
        f"📋 Fichajes totales: {total_fichajes}\n"
        f"✅ Estado: {'Activo' if usuario.get('activo') else 'Inactivo'}"
    )
    
    await update.message.reply_text(mensaje, parse_mode="Markdown")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los botones inline"""
    query = update.callback_query
    await query.answer()
    
    telegram_id = update.effective_user.id
    telegram_username = update.effective_user.username or "Sin username"
    
    usuario = obtener_usuario_por_telegram_id(telegram_id)
    
    if not usuario:
        await query.edit_message_text(
            "❌ Tu cuenta no está vinculada al sistema."
        )
        return
    
    if query.data == 'fichar_entrada':
        # Verificar último fichaje
        ultimo_fichaje = obtener_ultimo_fichaje(str(usuario['_id']))
        
        if ultimo_fichaje and ultimo_fichaje.get('tipo') == 'entrada':
            await query.edit_message_text(
                "⚠️ Ya registraste una ENTRADA. Debes registrar una SALIDA primero."
            )
            return
        
        # Registrar entrada
        registrar_fichaje(str(usuario['_id']), 'entrada', telegram_username)
        hora = datetime.now().strftime('%H:%M:%S')
        
        await query.edit_message_text(
            f"✅ *ENTRADA registrada*\n\n"
            f"🕐 Hora: {hora}\n"
            f"👤 {usuario.get('nombre_completo')}",
            parse_mode="Markdown"
        )
    
    elif query.data == 'fichar_salida':
        # Verificar último fichaje
        ultimo_fichaje = obtener_ultimo_fichaje(str(usuario['_id']))
        
        if ultimo_fichaje and ultimo_fichaje.get('tipo') == 'salida':
            await query.edit_message_text(
                "⚠️ Ya registraste una SALIDA. Debes registrar una ENTRADA primero."
            )
            return
        
        if not ultimo_fichaje or ultimo_fichaje.get('tipo') != 'entrada':
            await query.edit_message_text(
                "⚠️ Debes registrar una ENTRADA primero."
            )
            return
        
        # Registrar salida
        registrar_fichaje(str(usuario['_id']), 'salida', telegram_username)
        hora = datetime.now().strftime('%H:%M:%S')
        
        # Calcular horas
        entrada_time = ultimo_fichaje.get('timestamp')
        salida_time = datetime.now()
        horas = (salida_time - entrada_time).total_seconds() / 3600
        
        await query.edit_message_text(
            f"✅ *SALIDA registrada*\n\n"
            f"🕐 Hora: {hora}\n"
            f"👤 {usuario.get('nombre_completo')}\n"
            f"⏱️ Horas: {horas:.2f}h",
            parse_mode="Markdown"
        )
    
    elif query.data == 'ver_fichajes_hoy':
        fichajes_hoy = obtener_fichajes_hoy(str(usuario['_id']))
        
        if not fichajes_hoy:
            await query.edit_message_text("ℹ️ No has registrado fichajes hoy.")
            return
        
        mensaje = f"📋 *Fichajes de hoy:*\n\n"
        
        for fichaje in fichajes_hoy:
            tipo = fichaje.get('tipo').upper()
            hora = fichaje.get('timestamp').strftime('%H:%M:%S')
            emoji = "🟢" if tipo == "ENTRADA" else "🔴"
            mensaje += f"{emoji} {tipo}: {hora}\n"
        
        await query.edit_message_text(mensaje, parse_mode="Markdown")
    
    elif query.data == 'mi_info':
        total_fichajes = fichajes_col.count_documents({"usuario_id": str(usuario['_id'])})
        
        mensaje = (
            f"👤 *Tu Información*\n\n"
            f"📝 {usuario.get('nombre_completo')}\n"
            f"🏢 {usuario.get('departamento')}\n"
            f"📧 {usuario.get('email')}\n"
            f"📋 Fichajes: {total_fichajes}"
        )
        
        await query.edit_message_text(mensaje, parse_mode="Markdown")


def main():
    """Función principal del bot"""
    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN no está configurado en el archivo .env")

    print("🤖 Iniciando bot de Telegram para Sistema de Fichajes...")
    print("📱 Token: configurado por entorno")
    print(f"🗄️ MongoDB: {MONGO_URL}")
    print(f"📊 Base de datos: {DATABASE_NAME}")
    
    # Crear la aplicación
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Agregar handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CommandHandler("entrada", fichar_entrada_comando))
    app.add_handler(CommandHandler("salida", fichar_salida_comando))
    app.add_handler(CommandHandler("hoy", ver_fichajes_hoy_comando))
    app.add_handler(CommandHandler("info", mi_info_comando))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ Bot iniciado correctamente")
    print("📡 Esperando mensajes... (Ctrl+C para detener)")
    
    # Iniciar el bot
    app.run_polling()


if __name__ == "__main__":
    main()
