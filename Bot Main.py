import config
import time
from pybit.unified_trading import HTTP
from decimal import Decimal, ROUND_DOWN, ROUND_FLOOR
import threading
import telebot

session = HTTP(
    testnet=False,
    api_key=config.api_key,
    api_secret=config.api_secret,
)

# DEFINIR PARAMETROS PARA OPERAR
amount_usdt = Decimal(10) # Monto de USDT
factor_multiplicador_cantidad = Decimal(40) / Decimal('100') # % Incremento en la cantidad de monedas
numero_recompras = int(6) # Cantidad de recompras que quieres que tenga la operacion
posiciones_simultaneas= int(1) # Cantidad de posiciones que deseas tener abiertas a la vez.
factor_multiplicador_distancia = Decimal(2) # % Porcentaje en la distancia en cada recompra
distancia_porcentaje_tp = Decimal(1.1) / Decimal('100') # % Porcentaje en la distancia para colocar el Take Profit
distancia_porcentaje_sl = Decimal(numero_recompras * factor_multiplicador_distancia / 100) + Decimal("0.007")  # % Porcentaje en la distancia para colocar el SL a un 6% de la ultima recompra

bot_token = config.token_telegram
bot = telebot.TeleBot(bot_token)
chat_id = config.chat_id

# Diccionario para rastrear el número de veces que se ha colocado el TP por símbolo
tp_counter = {}

def enviar_mensaje_telegram(chat_id, mensaje):
    try:
        bot.send_message(chat_id, mensaje, parse_mode='HTML')
    except Exception as e:
        print(f"No se pudo enviar el mensaje a Telegram: {e}")

def get_current_position(symbol):
    try:
        response_positions = session.get_positions(category="linear", symbol=symbol)
        if response_positions['retCode'] == 0:
            return response_positions['result']['list']
        else:
            print(f"Error al obtener la posición: {response_positions}")
            return None
    except Exception as e:
        print(f"Error al obtener la posición: {e}")
        return None


def get_open_positions_count():
    try:
        response_positions = session.get_positions(category="linear", settleCoin="USDT")
        if response_positions['retCode'] == 0:
            positions = response_positions['result']['list']
            open_positions = [position for position in positions if Decimal(position['size']) != 0]
            return len(open_positions)
        else:
            print(f"Error al obtener el conteo de posiciones abiertas: {response_positions}")
            return 0
    except Exception as e:
        print(f"Error al obtener el conteo de posiciones abiertas: {e}")
        return 0

def get_pnl(symbol):
    closed_orders_response = session.get_closed_pnl(category="linear", symbol=symbol, limit=1)
    closed_orders_list = closed_orders_response['result']['list']

    for order in closed_orders_list:
        pnl_cerrada = float(order['closedPnl'])
        emoji = "🎉" if pnl_cerrada > 0 else "⚠️"
        estado = "GANANCIA" if pnl_cerrada > 0 else "PÉRDIDA"

        # Obtener el número de recompras ejecutadas antes de resetear
        recompras_ejecutadas = tp_counter.get(symbol, 1) - 1  # Restamos 1 porque el primer TP no es recompra

        mensaje_pnl = f"""
{emoji} <b>═══════════════════════</b> {emoji}
<b>  POSICIÓN CERRADA - {symbol}</b>
<b>═══════════════════════</b>

💰 <b>PNL Realizado:</b> <code>{pnl_cerrada:.2f} USDT</code>
📊 <b>Estado:</b> {estado}
🔢 <b>Recompras ejecutadas:</b> {recompras_ejecutadas}

━━━━━━━━━━━━━━━━━━━━━
"""
        enviar_mensaje_telegram(chat_id=chat_id, mensaje=mensaje_pnl)
        print(mensaje_pnl)

        # Resetear el contador de TP para este símbolo
        if symbol in tp_counter:
            del tp_counter[symbol]

def take_profit(symbol):
    try:
        # Obtener la lista de posiciones actuales
        positions_list = get_current_position(symbol)
        if not positions_list or len(positions_list) == 0:
            print(f"No hay posiciones abiertas para {symbol}.")
            return

        # Extraer información de la posición
        current_price = Decimal(positions_list[0]['avgPrice'])
        side = positions_list[0]['side']
        if side == "Buy":
            side_tp= "Sell"
        else:
            side_tp= "Buy"

        # Calcular el precio del stop loss según el lado de la posición
        distancia_porcentaje_tp_decimal = Decimal(str(distancia_porcentaje_tp))
        if side == "Buy":
            price_tp = adjust_price(symbol, current_price * (Decimal(1) + distancia_porcentaje_tp_decimal))
        elif side == "Sell":
            price_tp = adjust_price(symbol, current_price * (Decimal(1) - distancia_porcentaje_tp_decimal))
        else:
            print(f"No se detecta el lado de la posicion {side}")
            return

        response_limit_tp = session.place_order(
            category="linear",
            symbol=symbol,
            side=side_tp,
            orderType="Limit",
            qty="0",
            price=str(price_tp),
            reduceOnly=True,
        )

        # Verificar si la orden se colocó exitosamente
        if response_limit_tp['retCode'] != 0:
            error_msg = f"❌ Error al colocar Take Profit en {symbol}: {response_limit_tp.get('retMsg', 'Error desconocido')}"
            enviar_mensaje_telegram(chat_id=chat_id, mensaje=error_msg)
            print(error_msg)
            return

        # Incrementar el contador de TP para este símbolo
        if symbol not in tp_counter:
            tp_counter[symbol] = 1
        else:
            tp_counter[symbol] += 1

        distancia_tp = ((price_tp - float(current_price)) / float(current_price)) * 100 if side == "Buy" else ((float(current_price) - price_tp) / float(current_price)) * 100

        mensaje_tp = f"✅ <b>TP configurado</b> | {symbol} | <code>{price_tp:.6f}</code> ({abs(distancia_tp):.2f}%) | #{tp_counter[symbol]}"
        enviar_mensaje_telegram(chat_id=chat_id, mensaje=mensaje_tp)
        print(mensaje_tp)
    except Exception as e:
        print(f"Error en Take_profit para {symbol}: {str(e)}")

def abrir_posicion_largo(symbol, base_asset_qty_final, distancia_porcentaje_sl):
    try:
        if get_open_positions_count() >= posiciones_simultaneas:
            mensaje_count = """
⛔ <b>LÍMITE ALCANZADO</b>

❌ Se alcanzó el máximo de posiciones abiertas
📊 No se abrirá una nueva posición

━━━━━━━━━━━━━━━━━━━━━
"""
            enviar_mensaje_telegram(chat_id=chat_id, mensaje=mensaje_count)
            print (mensaje_count)
            return

        positions_list = get_current_position(symbol)
        if positions_list and any(Decimal(position['size']) != 0 for position in positions_list):
            print("Ya hay una posición abierta. No se abrirá otra posición.")
            return

        response_market_order = session.place_order(
            category="linear",
            symbol=symbol,
            side="Buy",
            orderType="Market",
            qty=base_asset_qty_final,
        )

        mensaje_market = f"""
🚀 <b>POSICIÓN LONG ABIERTA</b>

📈 <b>Par:</b> <code>{symbol}</code>
💰 <b>Cantidad:</b> <code>{base_asset_qty_final}</code>
📊 <b>Tipo:</b> Market Order
🔵 <b>Lado:</b> BUY (LONG)

━━━━━━━━━━━━━━━━━━━━━
"""
        enviar_mensaje_telegram(chat_id=chat_id, mensaje=mensaje_market)
        print(mensaje_market)

        time.sleep(5)
        take_profit(symbol)
        if response_market_order['retCode'] != 0:
            print("Error al abrir la posición: La orden de mercado no se completó correctamente.")
            return

        positions_list = get_current_position(symbol)
        current_price = Decimal(positions_list[0]['avgPrice'])

        price_sl = adjust_price(symbol, current_price * Decimal(1 - distancia_porcentaje_sl))
        stop_loss_order = session.set_trading_stop(
            category="linear",
            symbol=symbol,
            stopLoss=price_sl,
            slTriggerB="IndexPrice",
            tpslMode="Full",
            slOrderType="Market",
        )

        distancia_sl = ((float(current_price) - price_sl) / float(current_price)) * 100

        # Construir mensaje consolidado de Stop Loss y órdenes límite
        mensaje_ordenes = f"""
🛡️ <b>STOP LOSS & ÓRDENES LÍMITE - LONG</b>

📈 <b>Par:</b> <code>{symbol}</code>
💵 <b>Precio entrada:</b> <code>{float(current_price):.6f} USDT</code>

🔴 <b>Stop Loss:</b> <code>{price_sl:.6f}</code> ({distancia_sl:.2f}%)

📥 <b>Órdenes Límite:</b>
"""

        size_nuevo = base_asset_qty_final
        for i in range(1, numero_recompras + 1):
            porcentaje_distancia = Decimal('0.01') * i * factor_multiplicador_distancia
            cantidad_orden = size_nuevo * (1 + factor_multiplicador_cantidad)

            if isinstance(size_nuevo, int):
                cantidad_orden = int(cantidad_orden)
            else:
                cantidad_orden = round(cantidad_orden, len(str(size_nuevo).split('.')[1]))

            size_nuevo = cantidad_orden
            precio_orden_limite = adjust_price(symbol, current_price - (current_price * porcentaje_distancia))

            response_limit_order = session.place_order(
                category="linear",
                symbol=symbol,
                side="Buy",
                orderType="Limit",
                qty=str(cantidad_orden),
                price=str(precio_orden_limite),
            )

            # Calcular distancia real desde el precio de entrada
            distancia_real = ((float(current_price) - precio_orden_limite) / float(current_price)) * 100

            mensaje_ordenes += f"  #{i}: <code>{precio_orden_limite:.6f}</code> ({distancia_real:.2f}%) | Qty: <code>{cantidad_orden}</code>\n"

        mensaje_ordenes += "\n━━━━━━━━━━━━━━━━━━━━━"
        enviar_mensaje_telegram(chat_id=chat_id, mensaje=mensaje_ordenes)
        print(mensaje_ordenes)

    except Exception as e:
        print(f"Error al abrir la posición: {e}")

def abrir_posicion_corto(symbol, base_asset_qty_final, distancia_porcentaje_sl):
    try:
        if get_open_positions_count() >= posiciones_simultaneas:
            mensaje_count = """
⛔ <b>LÍMITE ALCANZADO</b>

❌ Se alcanzó el máximo de posiciones abiertas
📊 No se abrirá una nueva posición

━━━━━━━━━━━━━━━━━━━━━
"""
            enviar_mensaje_telegram(chat_id=chat_id, mensaje=mensaje_count)
            print (mensaje_count)
            return

        positions_list = get_current_position(symbol)
        if positions_list and any(Decimal(position['size']) != 0 for position in positions_list):
            print("Ya hay una posición abierta. No se abrirá otra posición.")
            return

        response_market_order = session.place_order(
            category="linear",
            symbol=symbol,
            side="Sell",
            orderType="Market",
            qty=base_asset_qty_final,
        )

        mensaje_market = f"""
🔴 <b>POSICIÓN SHORT ABIERTA</b>

📉 <b>Par:</b> <code>{symbol}</code>
💰 <b>Cantidad:</b> <code>{base_asset_qty_final}</code>
📊 <b>Tipo:</b> Market Order
🔴 <b>Lado:</b> SELL (SHORT)

━━━━━━━━━━━━━━━━━━━━━
"""
        enviar_mensaje_telegram(chat_id=chat_id, mensaje=mensaje_market)
        print(mensaje_market)

        time.sleep(5)
        take_profit(symbol)
        if response_market_order['retCode'] != 0:
            print("Error al abrir la posición: La orden de mercado no se completó correctamente.")
            return

        positions_list = get_current_position(symbol)
        current_price = Decimal(positions_list[0]['avgPrice'])

        price_sl = adjust_price(symbol, current_price * Decimal(1 + distancia_porcentaje_sl))
        stop_loss_order = session.set_trading_stop(
            category="linear",
            symbol=symbol,
            stopLoss=price_sl,
            slTriggerB="IndexPrice",
            tpslMode="Full",
            slOrderType="Market",
        )

        distancia_sl = ((price_sl - float(current_price)) / float(current_price)) * 100

        # Construir mensaje consolidado de Stop Loss y órdenes límite
        mensaje_ordenes = f"""
🛡️ <b>STOP LOSS & ÓRDENES LÍMITE - SHORT</b>

📉 <b>Par:</b> <code>{symbol}</code>
💵 <b>Precio entrada:</b> <code>{float(current_price):.6f} USDT</code>

🔴 <b>Stop Loss:</b> <code>{price_sl:.6f}</code> ({distancia_sl:.2f}%)

📥 <b>Órdenes Límite:</b>
"""

        size_nuevo = base_asset_qty_final
        for i in range(1, numero_recompras + 1):
            porcentaje_distancia = Decimal('0.01') * i * factor_multiplicador_distancia
            cantidad_orden = size_nuevo * (1 + factor_multiplicador_cantidad)

            if isinstance(size_nuevo, int):
                cantidad_orden = int(cantidad_orden)
            else:
                cantidad_orden = round(cantidad_orden, len(str(size_nuevo).split('.')[1]))

            size_nuevo = cantidad_orden
            precio_orden_limite = adjust_price(symbol, current_price + (current_price * porcentaje_distancia))

            response_limit_order = session.place_order(
                category="linear",
                symbol=symbol,
                side="Sell",
                orderType="Limit",
                qty=str(cantidad_orden),
                price=str(precio_orden_limite),
            )

            # Calcular distancia real desde el precio de entrada
            distancia_real = ((precio_orden_limite - float(current_price)) / float(current_price)) * 100

            mensaje_ordenes += f"  #{i}: <code>{precio_orden_limite:.6f}</code> ({distancia_real:.2f}%) | Qty: <code>{cantidad_orden}</code>\n"

        mensaje_ordenes += "\n━━━━━━━━━━━━━━━━━━━━━"
        enviar_mensaje_telegram(chat_id=chat_id, mensaje=mensaje_ordenes)
        print(mensaje_ordenes)

    except Exception as e:
        print(f"Error al abrir la posición: {e}")

def qty_step(symbol, amount_usdt):
    try:
        tickers = session.get_tickers(symbol=symbol, category="linear")
        for ticker_data in tickers["result"]["list"]:
            last_price = float(ticker_data["lastPrice"])

        last_price_decimal = Decimal(last_price)

        step_info = session.get_instruments_info(category="linear", symbol=symbol)
        qty_step = Decimal(step_info['result']['list'][0]['lotSizeFilter']['qtyStep'])

        base_asset_qty = amount_usdt / last_price_decimal

        qty_step_str = str(qty_step)
        if '.' in qty_step_str:
            decimals = len(qty_step_str.split('.')[1])
            base_asset_qty_final = round(base_asset_qty, decimals)
        else:
            base_asset_qty_final = int(base_asset_qty)

        return base_asset_qty_final
    except Exception as e:
        print(f"Error al calcular la cantidad del activo base: {e}")
        return None

def adjust_price(symbol, price):
    try:
        instrument_info = session.get_instruments_info(category="linear", symbol=symbol)
        tick_size = float(instrument_info['result']['list'][0]['priceFilter']['tickSize'])
        price_scale = int(instrument_info['result']['list'][0]['priceScale'])

        tick_dec = Decimal(f"{tick_size}")
        precision = Decimal(f"{10**price_scale}")
        price_decimal = Decimal(f"{price}")
        adjusted_price = (price_decimal * precision) / precision
        adjusted_price = (adjusted_price / tick_dec).quantize(Decimal('1'), rounding=ROUND_FLOOR) * tick_dec

        return float(adjusted_price)
    except Exception as e:
        print(f"Error al ajustar el precio: {e}")
        return None

def read_symbols_targets(file_path):
    symbols_targets = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) == 3:
                    symbol = parts[0]
                    target_price_lg = Decimal(parts[1])
                    target_price_st = Decimal(parts[2])

                    symbols_targets[symbol] = (target_price_lg, target_price_st)
    except Exception as e:
        print(f"Error al leer el archivo de símbolos y targets: {e}")
    return symbols_targets

def tomar_decision(file_path):
    monitoreados = set()  # Para rastrear qué monedas ya se han monitoreado y procesado
    while True:
        # Leer constantemente el archivo y actualizar los targets
        symbols_targets = read_symbols_targets(file_path)

        for symbol, (target_price_lg, target_price_st) in symbols_targets.items():
            if symbol not in monitoreados:  # Si la moneda no ha sido monitoreada aún
                try:
                    # Obtener el precio actual de la moneda
                    tickers = session.get_tickers(symbol=symbol, category="linear")
                    last_price = Decimal(tickers["result"]["list"][0]["lastPrice"])

                    # Cálculo de porcentaje de distancia para long y short
                    distancia_long = ((target_price_lg - last_price) / last_price) * 100
                    distancia_short = ((last_price - target_price_st) / last_price) * 100

                    # Verificar condiciones para abrir posición larga o corta
                    if last_price <= Decimal(target_price_lg):  # Condición para posición larga
                        base_asset_qty_final = qty_step(symbol, amount_usdt)
                        abrir_posicion_largo(symbol, base_asset_qty_final, distancia_porcentaje_sl)
                        monitoreados.add(symbol)  # Marcar la moneda como procesada
                        mensaje_monitor = f"""
🎯 <b>TARGET ALCANZADO - LONG</b>

📈 <b>Par:</b> <code>{symbol}</code>
💵 <b>Precio actual:</b> <code>{last_price:.6f} USDT</code>
🎯 <b>Target Long:</b> <code>{target_price_lg:.6f} USDT</code>
✅ <b>Estado:</b> Entrando en posición

━━━━━━━━━━━━━━━━━━━━━
"""
                        enviar_mensaje_telegram(chat_id=chat_id, mensaje=mensaje_monitor)
                        print(mensaje_monitor)

                    elif last_price >= Decimal(target_price_st):  # Condición para posición corta
                        base_asset_qty_final = qty_step(symbol, amount_usdt)
                        abrir_posicion_corto(symbol, base_asset_qty_final, distancia_porcentaje_sl)
                        monitoreados.add(symbol)  # Marcar la moneda como procesada
                        mensaje_monitor = f"""
🎯 <b>TARGET ALCANZADO - SHORT</b>

📉 <b>Par:</b> <code>{symbol}</code>
💵 <b>Precio actual:</b> <code>{last_price:.6f} USDT</code>
🎯 <b>Target Short:</b> <code>{target_price_st:.6f} USDT</code>
✅ <b>Estado:</b> Entrando en posición

━━━━━━━━━━━━━━━━━━━━━
"""
                        enviar_mensaje_telegram(chat_id=chat_id, mensaje=mensaje_monitor)
                        print(mensaje_monitor)

                    else:
                        # Log de precios actuales, targets y porcentajes
                        print(f"{symbol} - Precio actual: {last_price}, "
                              f"Long Target: {target_price_lg} ({distancia_long:.2f}%), "
                              f"Short Target: {target_price_st} ({distancia_short:.2f}%)")
                        print("")


                except Exception as e:
                    print(f"Error al tomar decisión para {symbol}: {e}")

        # Retornar a la lectura del archivo para verificar si hubo cambios
        time.sleep(2)  # Espera de 5 segundos antes de volver a leer el archivo


def cancelar_ordenes():
    symbols_monitored = set()  # Conjunto para almacenar los símbolos monitoreados
    last_entry_prices = {}  # Diccionario para almacenar el último precio de entrada por símbolo

    while True:
        try:
            # Obtener todas las posiciones abiertas
            positions = session.get_positions(category="linear", settleCoin="USDT")['result']['list']

            # Verificar cada posición
            for position in positions:
                symbol = position['symbol']
                current_price = Decimal(position['avgPrice'])
                # Verificar si el precio de entrada ha cambiado desde la última revisión
                if symbol in last_entry_prices and last_entry_prices[symbol] != current_price:
                    # Cancelar la orden de take profit existente
                    open_orders = session.get_open_orders(category="linear", symbol=symbol)['result']['list']
                    tp_limit_orders = [order for order in open_orders
                                       if order.get('orderType') == "Limit" and order.get('reduceOnly') == True]

                    for order in tp_limit_orders:
                        cancel_response = session.cancel_order(category="linear", symbol=symbol, orderId=order['orderId'])
                        if 'result' in cancel_response and cancel_response['result']:
                            print(f"Orden de take profit cancelada con éxito en {symbol}: {cancel_response}")

                    # Volver a colocar el take profit
                    take_profit(symbol)

                # Actualizar el precio de entrada anterior
                last_entry_prices[symbol] = current_price

                # Agregar el símbolo al conjunto de monitoreo si no está presente
                if symbol not in symbols_monitored:
                    symbols_monitored.add(symbol)

            # Cancelar todas las órdenes limit abiertas para los símbolos no monitoreados
            for symbol in symbols_monitored.copy():
                if symbol not in [pos['symbol'] for pos in positions]:
                    session.cancel_all_orders(category="linear", symbol=symbol)
                    get_pnl(symbol)
                    symbols_monitored.remove(symbol)

        except Exception as e:
            print(f"Error en la cancelación de órdenes: {e}")

        time.sleep(2)  # Esperar 5 segundos antes de la próxima iteración



if __name__ == "__main__":
    file_path = 'symbols_targets.txt'

    tomar_decision_thread = threading.Thread(target=tomar_decision, args=(file_path,))
    tomar_decision_thread.start()

    cancelar_ordenes_thread = threading.Thread(target=cancelar_ordenes)
    cancelar_ordenes_thread.start()
