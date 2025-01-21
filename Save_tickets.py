import tkinter as tk
from tkinter import messagebox
from decimal import Decimal
from pybit.unified_trading import HTTP

# Iniciar la conexión con Bybit
session = HTTP(testnet=False)

# Función para obtener la lista de símbolos disponibles en Bybit
def obtener_lista_simbolos():
    try:
        response = session.get_tickers(category="linear")
        if response["retCode"] == 0:
            return [item["symbol"] for item in response["result"]["list"]]
    except Exception as e:
        print(f"Error al obtener la lista de símbolos: {e}")
    return []

# Función para guardar la moneda y precios en el archivo de texto y agregarla a la lista visual
def guardar_moneda():
    # Obtener los valores de los recuadros de texto
    moneda = entry_moneda.get().strip()
    precio_long = entry_long.get().strip()
    precio_short = entry_short.get().strip()

    # Validar que los campos no estén vacíos y los precios sean válidos
    if not moneda or not precio_long or not precio_short:
        messagebox.showerror("Error", "Todos los campos deben estar completos")
        return

    try:
        # Convertir los precios a Decimal para asegurarse de que son números válidos
        precio_long = Decimal(precio_long)
        precio_short = Decimal(precio_short)
    except Exception as e:
        messagebox.showerror("Error", "Los precios deben ser números válidos")
        return

    # Convertir la moneda a mayúsculas y asegurarse de que termine en 'USDT'
    moneda = moneda.upper()
    if not moneda.endswith("USDT"):
        moneda += "USDT"

    # Verificar si la moneda está en la lista de símbolos de Bybit
    lista_simbolos = obtener_lista_simbolos()
    if moneda not in lista_simbolos:
        messagebox.showerror("Error", f"La moneda {moneda} no está disponible en Bybit.")
        return

    # Escribir la información en el archivo symbols_targets.txt
    try:
        with open("symbols_targets.txt", "a") as file:
            file.write(f"{moneda} {precio_long} {precio_short}\n")
        
        # Actualizar la lista visual con la nueva moneda
        lista_monedas.insert(tk.END, f"{moneda} - Long: {precio_long} - Short: {precio_short}")
        
        # Limpiar los campos después de guardar
        entry_moneda.delete(0, tk.END)
        entry_long.delete(0, tk.END)
        entry_short.delete(0, tk.END)
        
        messagebox.showinfo("Éxito", f"Moneda {moneda} guardada exitosamente.")
    except Exception as e:
        messagebox.showerror("Error", f"Error al guardar la moneda: {e}")

# Función para manejar el evento de presionar Enter
def enter_guardar(event):
    guardar_moneda()

# Función para borrar todo el análisis (el archivo y la lista de monedas)
def borrar_analisis():
    # Confirmación antes de borrar
    confirmacion = messagebox.askyesno("Confirmación", "¿Estás seguro de que deseas borrar todo el análisis?")
    if confirmacion:
        try:
            # Borrar el archivo de texto
            open("symbols_targets.txt", "w").close()
            # Limpiar la lista visual
            lista_monedas.delete(0, tk.END)
            messagebox.showinfo("Éxito", "Todo el análisis ha sido borrado.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al borrar el análisis: {e}")

# Crear la ventana principal
root = tk.Tk()
root.title("Herramienta de Monedas")
root.geometry("800x400")
root.config(bg="#f0f0f0")

# Crear el frame principal que contiene los recuadros de texto y la lista
frame_principal = tk.Frame(root, bg="#f0f0f0")
frame_principal.pack(pady=10, fill=tk.BOTH, expand=True)

# Crear un frame para los recuadros de texto
frame_entrada = tk.Frame(frame_principal, bg="#f0f0f0")
frame_entrada.pack(side=tk.LEFT, padx=20)

# Crear las etiquetas y entradas
label_moneda = tk.Label(frame_entrada, text="Moneda (Ej. BTC):", font=("Arial", 12), bg="#f0f0f0")
label_moneda.pack(pady=10)
entry_moneda = tk.Entry(frame_entrada, font=("Arial", 12), width=20)
entry_moneda.pack(pady=5)

label_long = tk.Label(frame_entrada, text="Precio Long:", font=("Arial", 12), bg="#f0f0f0")
label_long.pack(pady=5)
entry_long = tk.Entry(frame_entrada, font=("Arial", 12), width=20)
entry_long.pack(pady=5)

label_short = tk.Label(frame_entrada, text="Precio Short:", font=("Arial", 12), bg="#f0f0f0")
label_short.pack(pady=5)
entry_short = tk.Entry(frame_entrada, font=("Arial", 12), width=20)
entry_short.pack(pady=5)

# Crear botón para guardar la moneda
btn_guardar = tk.Button(frame_entrada, text="Guardar Moneda", font=("Arial", 12), bg="#4CAF50", fg="white", command=guardar_moneda)
btn_guardar.pack(pady=20)

# Crear un frame para la lista de monedas guardadas
frame_lista_monedas = tk.Frame(frame_principal, bg="#f0f0f0")
frame_lista_monedas.pack(side=tk.LEFT, padx=20, fill=tk.BOTH, expand=True)

label_lista_monedas = tk.Label(frame_lista_monedas, text="Monedas Guardadas:", font=("Arial", 12), bg="#f0f0f0")
label_lista_monedas.pack(anchor="w", padx=20)  # Moved slightly to the right

# Crear una lista con las monedas
lista_monedas = tk.Listbox(frame_lista_monedas, font=("Arial", 10), height=15, width=40)  # Aumentado el alto
lista_monedas.pack(pady=5)

# Crear botón rojo para borrar todo el análisis
btn_borrar_analisis = tk.Button(frame_lista_monedas, text="Borrar todo el análisis", font=("Arial", 12), bg="#F44336", fg="white", command=borrar_analisis)
btn_borrar_analisis.pack(pady=20)

# Asignar la función de presionar Enter al campo de entrada
entry_moneda.bind("<Return>", enter_guardar)
entry_long.bind("<Return>", enter_guardar)
entry_short.bind("<Return>", enter_guardar)

# Iniciar la interfaz gráfica
root.mainloop()
