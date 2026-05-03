"""
Bot de Telegram para Sistema de Fichajes
Permite a los empleados fichar desde Telegram
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
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

from fichajes_common.location import evaluar_ubicacion_usuario, get_company_location
from fichajes_backpy.app.services.fichaje_service import crear_fichaje_geolocalizado

ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
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


def obtener_fichajes_semana(usuario_id: str):
    """Obtiene los fichajes de los últimos 7 días de un usuario"""
    from datetime import timedelta
    hace_7_dias = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    hace_7_dias = hace_7_dias - timedelta(days=7)
    return list(fichajes_col.find({
        "usuario_id": usuario_id,
        "timestamp": {"$gte": hace_7_dias}
    }).sort("timestamp", 1))


def calcular_horas_semana(usuario_id: str) -> float:
    """Calcula las horas totales trabajadas en la última semana"""
    fichajes = obtener_fichajes_semana(usuario_id)
    entradas = [f for f in fichajes if f.get('tipo') == 'entrada']
    salidas = [f for f in fichajes if f.get('tipo') == 'salida']
    
    total_horas = 0
    for i in range(min(len(entradas), len(salidas))):
        entrada_time = entradas[i].get('timestamp')
        salida_time = salidas[i].get('timestamp')
        if entrada_time and salida_time:
            total_horas += (salida_time - entrada_time).total_seconds() / 3600
    
    return total_horas


def construir_teclado_ubicacion(accion: str) -> ReplyKeyboardMarkup:
    """Pide al usuario compartir la ubicación real del dispositivo."""
    texto_accion = "ENTRADA" if accion == "entrada" else "SALIDA"
    teclado = [[KeyboardButton(f"📍 Enviar ubicación para {texto_accion}", request_location=True)]]
    return ReplyKeyboardMarkup(teclado, resize_keyboard=True, one_time_keyboard=True)


def preparar_accion_pendiente(context: ContextTypes.DEFAULT_TYPE, accion: str) -> None:
    context.user_data["accion_pendiente"] = accion


def obtener_accion_pendiente(context: ContextTypes.DEFAULT_TYPE) -> str | None:
    return context.user_data.get("accion_pendiente")


def limpiar_accion_pendiente(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("accion_pendiente", None)


def validar_ubicacion_empresa(latitude: float, longitude: float) -> dict:
    """Valida la ubicación contra el radio permitido de la empresa."""
    return evaluar_ubicacion_usuario(latitude, longitude)


async def solicitar_ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE, accion: str):
    """Solicita ubicación real antes de procesar un fichaje."""
    texto_accion = "ENTRADA" if accion == "entrada" else "SALIDA"
    preparar_accion_pendiente(context, accion)
    await update.message.reply_text(
        f"📍 Para registrar la {texto_accion}, comparte tu ubicación real desde el teléfono.\n\n"
        f"La empresa autorizada es {get_company_location().name} y el radio permitido es de {get_company_location().radius_km:.0f} km.",
        reply_markup=construir_teclado_ubicacion(accion)
    )


async def procesar_fichaje_con_ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE, latitude: float, longitude: float):
    """Procesa el fichaje usando la ubicación real del usuario."""
    accion = obtener_accion_pendiente(context)
    if accion not in {"entrada", "salida"}:
        await update.message.reply_text(
            "ℹ️ Primero indica si quieres fichar entrada o salida con /entrada o /salida.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    telegram_id = update.effective_user.id
    telegram_username = update.effective_user.username or "Sin username"
    usuario = obtener_usuario_por_telegram_id(telegram_id)

    if not usuario:
        limpiar_accion_pendiente(context)
        await update.message.reply_text(
            "❌ Tu cuenta no está vinculada al sistema. Usa /start para más información.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    evaluacion = validar_ubicacion_empresa(latitude, longitude)
    company = evaluacion["company"]

    if not evaluacion["within_radius"]:
        limpiar_accion_pendiente(context)
        await update.message.reply_text(
            f"❌ No puedes fichar desde esta ubicación.\n\n"
            f"🏢 Empresa: {company.name}\n"
            f"📍 Distancia: {evaluacion['distance_km']:.2f} km\n"
            f"🚫 Límite autorizado: {company.radius_km:.0f} km",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    ultimo_fichaje = obtener_ultimo_fichaje(str(usuario["_id"]))
    if ultimo_fichaje and ultimo_fichaje.get("tipo") == accion:
        limpiar_accion_pendiente(context)
        await update.message.reply_text(
            f"⚠️ Ya registraste una {accion.upper()}. Debes registrar una {'SALIDA' if accion == 'entrada' else 'ENTRADA'} primero.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    if accion == "salida" and (not ultimo_fichaje or ultimo_fichaje.get("tipo") != "entrada"):
        limpiar_accion_pendiente(context)
        await update.message.reply_text(
            "⚠️ Debes registrar una ENTRADA primero.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    try:
        await crear_fichaje_geolocalizado(
            user_id=str(usuario["_id"]),
            username=usuario["username"],
            nombre_completo=usuario.get("nombre_completo", usuario["username"]),
            tipo=accion,
            latitude=latitude,
            longitude=longitude,
            precision_gps_m=None,
        )
    except ValueError as exc:
        limpiar_accion_pendiente(context)
        await update.message.reply_text(
            f"❌ {exc}",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    hora = datetime.now().strftime("%H:%M:%S")
    limpiar_accion_pendiente(context)

    # Calcular horas de la semana
    horas_semana = calcular_horas_semana(str(usuario["_id"]))
    
    # Calcular horas del día
    fichajes_hoy = obtener_fichajes_hoy(str(usuario["_id"]))
    entradas_hoy = [f for f in fichajes_hoy if f.get('tipo') == 'entrada']
    salidas_hoy = [f for f in fichajes_hoy if f.get('tipo') == 'salida']
    horas_hoy = 0
    if entradas_hoy and salidas_hoy:
        for i in range(min(len(entradas_hoy), len(salidas_hoy))):
            entrada_time = entradas_hoy[i].get('timestamp')
            salida_time = salidas_hoy[i].get('timestamp')
            if entrada_time and salida_time:
                horas_hoy += (salida_time - entrada_time).total_seconds() / 3600

    await update.message.reply_text(
        f"✅ *{accion.upper()} registrada exitosamente*\n\n"
        f"🏢 {company.name}\n"
        f"📍 Distancia: {evaluacion['distance_km']:.2f} km\n"
        f"🕐 Hora: {hora}\n"
        f"👤 Usuario: {usuario.get('nombre_completo')}\n"
        f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y')}\n\n"
        f"⏱️ *Horas hoy:* {horas_hoy:.2f}h\n"
        f"📊 *Horas semana:* {horas_semana:.2f}h",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )


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
        [InlineKeyboardButton("📊 Ver fichajes semana", callback_data='ver_fichajes_semana')],
        [InlineKeyboardButton("ℹ️ Mi información", callback_data='mi_info')],
        [InlineKeyboardButton("📍 Empresa y ubicación", callback_data='mi_empresa')]
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
        "/entrada - Solicita tu ubicación y registra una entrada\n"
        "/salida - Solicita tu ubicación y registra una salida\n"
        "/hoy - Muestra tus fichajes de hoy\n"
        "/semana - Muestra tus fichajes de la última semana y horas acumuladas\n"
        "/info - Muestra tu información\n"
        "/ubicacion - Muestra la empresa y verifica tu geolocalización\n"
        "/ayuda - Muestra esta ayuda",
        parse_mode="Markdown"
    )


async def ubicacion_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ubicacion - solicita ubicación y muestra el criterio de empresa."""
    teclado = construir_teclado_ubicacion("entrada")
    company = get_company_location()
    await update.message.reply_text(
        f"🏢 *{company.name}*\n\n"
        f"📍 Dirección: {company.address}\n"
        f"🧭 Radio permitido: {company.radius_km:.0f} km\n\n"
        f"Para validar tu acceso al fichaje, comparte tu ubicación real desde el móvil.",
        parse_mode="Markdown",
        reply_markup=teclado,
    )


async def location_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe la ubicación del usuario y ejecuta el fichaje pendiente."""
    if not update.message or not update.message.location:
        return

    await procesar_fichaje_con_ubicacion(
        update,
        context,
        latitude=update.message.location.latitude,
        longitude=update.message.location.longitude,
    )


async def fichar_entrada_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /entrada - Registra una entrada"""
    await solicitar_ubicacion(update, context, "entrada")


async def fichar_salida_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /salida - Registra una salida"""
    await solicitar_ubicacion(update, context, "salida")


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


async def ver_fichajes_semana_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /semana - Muestra fichajes de la última semana y horas acumuladas"""
    telegram_id = update.effective_user.id
    
    usuario = obtener_usuario_por_telegram_id(telegram_id)
    
    if not usuario:
        await update.message.reply_text(
            "❌ Tu cuenta no está vinculada al sistema. Usa /start para más información."
        )
        return
    
    fichajes_semana = obtener_fichajes_semana(str(usuario['_id']))
    
    if not fichajes_semana:
        await update.message.reply_text(
            "ℹ️ No hay fichajes registrados en la última semana."
        )
        return
    
    mensaje = f"📊 *Tus fichajes de la última semana:*\n\n"
    
    # Agrupar fichajes por día
    fichajes_por_dia = {}
    for fichaje in fichajes_semana:
        fecha = fichaje.get('timestamp').strftime('%d/%m')
        if fecha not in fichajes_por_dia:
            fichajes_por_dia[fecha] = []
        fichajes_por_dia[fecha].append(fichaje)
    
    # Mostrar fichajes agrupados por día
    for fecha in sorted(fichajes_por_dia.keys()):
        mensaje += f"📅 *{fecha}*\n"
        for fichaje in fichajes_por_dia[fecha]:
            tipo = fichaje.get('tipo').upper()
            hora = fichaje.get('timestamp').strftime('%H:%M:%S')
            emoji = "🟢" if tipo == "ENTRADA" else "🔴"
            mensaje += f"  {emoji} {tipo}: {hora}\n"
        mensaje += "\n"
    
    # Calcular y mostrar horas totales de la semana
    horas_semana = calcular_horas_semana(str(usuario['_id']))
    mensaje += f"\n📈 *Total horas semana:* {horas_semana:.2f}h"
    
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
        preparar_accion_pendiente(context, "entrada")
        await query.message.reply_text(
            f"📍 Para registrar la ENTRADA, comparte tu ubicación real.\n\n"
            f"La empresa autorizada es {get_company_location().name} y el radio permitido es de {get_company_location().radius_km:.0f} km.",
            reply_markup=construir_teclado_ubicacion("entrada")
        )
        await query.edit_message_text("📍 Solicitud de ubicación enviada. Usa el botón para compartir tu posición real.")
    
    elif query.data == 'fichar_salida':
        preparar_accion_pendiente(context, "salida")
        await query.message.reply_text(
            f"📍 Para registrar la SALIDA, comparte tu ubicación real.\n\n"
            f"La empresa autorizada es {get_company_location().name} y el radio permitido es de {get_company_location().radius_km:.0f} km.",
            reply_markup=construir_teclado_ubicacion("salida")
        )
        await query.edit_message_text("📍 Solicitud de ubicación enviada. Usa el botón para compartir tu posición real.")
    
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
    
    elif query.data == 'ver_fichajes_semana':
        fichajes_semana = obtener_fichajes_semana(str(usuario['_id']))
        
        if not fichajes_semana:
            await query.edit_message_text("ℹ️ No hay fichajes registrados en la última semana.")
            return
        
        mensaje = f"📊 *Fichajes de la última semana:*\n\n"
        
        # Agrupar fichajes por día
        fichajes_por_dia = {}
        for fichaje in fichajes_semana:
            fecha = fichaje.get('timestamp').strftime('%d/%m')
            if fecha not in fichajes_por_dia:
                fichajes_por_dia[fecha] = []
            fichajes_por_dia[fecha].append(fichaje)
        
        # Mostrar fichajes agrupados por día
        for fecha in sorted(fichajes_por_dia.keys()):
            mensaje += f"📅 *{fecha}*\n"
            for fichaje in fichajes_por_dia[fecha]:
                tipo = fichaje.get('tipo').upper()
                hora = fichaje.get('timestamp').strftime('%H:%M:%S')
                emoji = "🟢" if tipo == "ENTRADA" else "🔴"
                mensaje += f"  {emoji} {tipo}: {hora}\n"
            mensaje += "\n"
        
        # Calcular y mostrar horas totales de la semana
        horas_semana = calcular_horas_semana(str(usuario['_id']))
        mensaje += f"\n📈 *Total horas semana:* {horas_semana:.2f}h"
        
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

    elif query.data == 'mi_empresa':
        company = get_company_location()
        await query.edit_message_text(
            f"🏢 *{company.name}*\n\n"
            f"📍 Dirección: {company.address}\n"
            f"🧭 Coordenadas: {company.latitude:.6f}, {company.longitude:.6f}\n"
            f"📏 Radio permitido: {company.radius_km:.0f} km\n\n"
            f"Para fichar, usa /entrada o /salida y comparte tu ubicación real.",
            parse_mode="Markdown"
        )


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
    app.add_handler(CommandHandler("semana", ver_fichajes_semana_comando))
    app.add_handler(CommandHandler("info", mi_info_comando))
    app.add_handler(CommandHandler("ubicacion", ubicacion_comando))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.LOCATION, location_message_handler))
    
    print("✅ Bot iniciado correctamente")
    print("📡 Esperando mensajes... (Ctrl+C para detener)")
    
    # Iniciar el bot
    app.run_polling()


if __name__ == "__main__":
    main()
