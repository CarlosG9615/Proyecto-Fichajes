"""
Script de prueba rápida para verificar la configuración de Telegram
"""
import os
from dotenv import load_dotenv
from pathlib import Path
from telegram import Bot
import asyncio

ROOT_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ROOT_ENV_FILE)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


async def test_bot():
    """Prueba la conexión con el bot de Telegram"""
    print("🧪 Probando conexión con Telegram Bot...\n")
    
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "tu_token_de_telegram":
        print("❌ ERROR: Token de Telegram no configurado en .env")
        print("📝 Por favor, configura TELEGRAM_TOKEN en el archivo .env")
        return False
    
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        bot_info = await bot.get_me()
        
        print("✅ Conexión exitosa!")
        print(f"\n📱 Información del Bot:")
        print(f"   • Nombre: {bot_info.first_name}")
        print(f"   • Username: @{bot_info.username}")
        print(f"   • ID: {bot_info.id}")
        print(f"   • Puede leer mensajes: {bot_info.can_read_all_group_messages}")
        
        print(f"\n💡 Para usar el bot:")
        print(f"   1. Abre Telegram")
        print(f"   2. Busca: @{bot_info.username}")
        print(f"   3. Envía: /start")
        print(f"\n🚀 Inicia el sistema con: .\\INICIO.cmd")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("\n🔍 Posibles causas:")
        print("   • Token inválido")
        print("   • Sin conexión a internet")
        print("   • Bot bloqueado por Telegram")
        return False


if __name__ == "__main__":
    asyncio.run(test_bot())
