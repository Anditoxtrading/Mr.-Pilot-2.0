

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

# **Configuración del Bot de Trading en Bybit**

## 1. Obtener la API Key y API Secret de Bybit
1. Crea una cuenta en **Bybit** si aún no tienes una.
2. Accede a **Configuración** de tu cuenta y dirígete a la sección de **API**.
3. Genera una nueva clave de **API** con permisos de **trading** (sin permisos de retiro).

---

## 2. Configuración del archivo `config.py`
Crea un archivo llamado **`config.py`** en el mismo directorio donde tienes tu script y agrega las siguientes credenciales:

```python
api_key = 'tu_api_key'
api_secret = 'tu_api_secret'

token_telegram = 'tu_telegram_bot_token'
chat_id = 'tu_chat_id_telegram'
---
## 3. Ajustes de Parámetros Personalizados
Dentro del script, puedes ajustar los siguientes parámetros para personalizar el comportamiento de tu bot de acuerdo a tus necesidades:

amount_usdt: El monto inicial en USDT para cada operación.
factor_multiplicador_cantidad: El porcentaje de incremento en la cantidad de monedas para las recompras.
numero_recompras: El número de recompras que realizará el bot.
posiciones_simultaneas: El número máximo de posiciones abiertas simultáneamente.
factor_multiplicador_distancia: El porcentaje de distancia entre las recompras.
distancia_porcentaje_tp: El porcentaje de distancia para el Take Profit.
distancia_porcentaje_sl: El porcentaje de distancia para el Stop Loss.
