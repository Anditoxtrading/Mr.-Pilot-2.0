

# Trading Bot de Bybit con Recompras Automáticas

Este es un bot de trading diseñado para operar en la plataforma Bybit utilizando su API. El bot realiza operaciones de compra o venta, establece stop loss y take profit, y ejecuta recompras automáticas en función de la evolución del precio. Además, se integra con Telegram para enviar notificaciones en tiempo real.

## Características

- **Órdenes de mercado**: El bot puede abrir posiciones de compra (long) o venta (short) usando órdenes de mercado.
- **Recompras automáticas**: El bot realiza recompras (compra adicional o venta) en función del porcentaje de distancia desde el precio de la operación inicial.
- **Take Profit y Stop Loss**: Configuración automática de niveles de Take Profit (TP) y Stop Loss (SL).
- **Posiciones simultáneas**: Controla el número de posiciones abiertas al mismo tiempo.
- **Integración con Telegram**: Notificaciones en tiempo real sobre el estado de las operaciones y las ganancias obtenidas.

## Requisitos

Para ejecutar este bot, necesitas:

- Python 3.6+.
- Las siguientes librerías de Python:
  - `pybit`: Librería para interactuar con la API de Bybit.
  - `telebot`: Librería para enviar mensajes a Telegram.
  - `decimal`: Para manejar cálculos de precisión con monedas y precios.

Instala las dependencias con el siguiente comando:
pip install pybit pyTelegramBotAPI

Configuración
1. Obtener la API Key y API Secret de Bybit
Crea una cuenta en Bybit.
Ve a API en la configuración de tu cuenta y genera una nueva clave de API con permisos de trading (sin permisos de retiro).
2. Configurar el archivo config.py
Crea un archivo config.py en el mismo directorio donde tienes el script y coloca tus credenciales de API de Bybit y tu token de Telegram:


api_key = 'tu_api_key'
api_secret = 'tu_api_secret'
token_telegram = 'tu_telegram_bot_token'
chat_id = 'tu_chat_id_telegram'
api_key: La clave de API de Bybit.
api_secret: El secreto de tu clave de API de Bybit.
token_telegram: El token de tu bot de Telegram.
chat_id: El ID del chat de Telegram donde recibirás las notificaciones.

3. Ajustes de parámetros
Dentro del script, puedes ajustar varios parámetros para personalizar el comportamiento del bot:

amount_usdt: El monto inicial en USDT para cada operación.
factor_multiplicador_cantidad: El porcentaje de incremento en la cantidad de monedas para las recompras.
numero_recompras: El número de recompras que realizará el bot.
posiciones_simultaneas: El número máximo de posiciones abiertas simultáneamente.
factor_multiplicador_distancia: El porcentaje de distancia entre recompras.
distancia_porcentaje_tp: El porcentaje de distancia para el Take Profit.
distancia_porcentaje_sl: El porcentaje de distancia para el Stop Loss.
