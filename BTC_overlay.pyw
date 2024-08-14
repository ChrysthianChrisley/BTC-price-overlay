import tkinter as tk
import requests
import threading
from PIL import Image, ImageDraw, ImageFont
import pystray
import sys
import os

currencies = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ETCUSDT', 'XRPUSDT', 'TRXUSDT', 'TONUSDT', 'SOLUSDT',
              'ETHBTC', 'BNBBTC', 'TONBTC', 'SOLBTC']
current_currency = currencies[0]
price_label = None
window_hidden = False
previous_price = None
stop_event = threading.Event()

# Verifique o idioma passado como argumento, padrão é English
language = sys.argv[1] if len(sys.argv) > 1 else "English"

def get_price(currency):
    try:
        response = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={currency}')
        data = response.json()
        price = float(data['price'])
        return price
    except Exception as e:
        return f"Error: {e}"

def update_price():
    global current_currency, price_label, previous_price
    if not stop_event.is_set():
        price = get_price(current_currency)
        
        if isinstance(price, str) and price.startswith("Error"):
            price_label.config(text=price, fg="black")
        else:
            if previous_price is None:
                price_label.config(fg="black")
            elif price > previous_price:
                price_label.config(fg="green")
            elif price < previous_price:
                price_label.config(fg="red")
            else:
                price_label.config(fg="black")
            previous_price = price
            if price > 100:
                price = f"{price:,.2f}"
            elif price > 1:
                price = f"{price:,.3f}"
            elif price > 0.25:
                price = f"{price:,.4f}"
            else:
                price = str(price)
            if 'USD' in current_currency:
                price = '$' + price
            price_label.config(text=f"{current_currency}: {price}")
        
        root.after(1000, update_price)

def quit_app(icon, item):
    stop_event.set()
    icon.stop()
    root.quit()

def hide_window(icon, item):
    global window_hidden
    if window_hidden:
        root.deiconify()
        window_hidden = False
    else:
        root.withdraw()
        window_hidden = True
    update_tray_menu()

def set_currency(currency_key):
    global current_currency, previous_price
    current_currency = str(currency_key)
    previous_price = None
    price_label.config(text="Loading...", fg="black")
    update_tray_menu()

def create_image():
    image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 56, 56), outline="black", fill="orange")
    font = ImageFont.truetype("arial", 36)
    draw.text((18, 10), "B", font=font, fill="white")
    return image

def change_language(icon, item, lang):
    # Reinicie o aplicativo com o novo idioma
    os.execl(sys.executable, sys.executable, *sys.argv[:1], lang)

def update_tray_menu():
    global icon
    currency_label = "Moeda" if language == "Português" else "Currency"
    show_label = "Exibir" if window_hidden and language == "Português" else "Esconder" if language == "Português" else "Show" if window_hidden else "Hide"
    exit_label = "Sair" if language == "Português" else "Exit"
    title = "Rastreador de Preços" if language == "Português" else "Price Tracker"

    currency_menu = pystray.Menu(
        *[
            pystray.MenuItem(currency, lambda _, cur=currency: set_currency(cur), 
                             checked=lambda item, cur=currency: current_currency == cur)
            for currency in currencies
        ]
    )
    
    menu = pystray.Menu(
        pystray.MenuItem(currency_label, currency_menu),
        pystray.MenuItem(show_label, hide_window),
        pystray.MenuItem(exit_label, quit_app),
        pystray.MenuItem('Language', pystray.Menu(
            pystray.MenuItem('English', lambda icon, item: change_language(icon, item, "English"), checked=lambda item: language == "English"),
            pystray.MenuItem('Português', lambda icon, item: change_language(icon, item, "Português"), checked=lambda item: language == "Português")
        ))
    )
    
    icon = pystray.Icon("price_tracker", create_image(), title)
    icon.menu = menu

def setup_tray():
    global icon
    icon = pystray.Icon("price_tracker", create_image(), "Price Tracker")
    update_tray_menu()
    icon.run()

def update_window_position(event=None):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = screen_width - window_width - 23
    y = 23
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

root = tk.Tk()
root.title("Price Tracker")
root.attributes('-topmost', True)
root.attributes('-alpha', 0.7)
root.overrideredirect(True)

window_width = 180
window_height = 26

update_window_position()

price_label = tk.Label(root, font=('Helvetica', 12))
price_label.pack()

root.bind('<Configure>', update_window_position)

root.after(0, update_price)

threading.Thread(target=setup_tray, daemon=True).start()

root.mainloop()
