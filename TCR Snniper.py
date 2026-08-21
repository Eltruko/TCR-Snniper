import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageGrab
import pytesseract
import pyperclip
import ctypes
import os
import sys

# --- 1. CONFIGURACIÓN DE RUTAS ---
def get_resource_path(relative_path):
    """Devuelve la ruta absoluta de los recursos, compatible con el .exe de PyInstaller"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# --- 2. CONFIGURACIÓN INTELIGENTE DE TESSERACT (Ideal para GitHub) ---
# Busca el ejecutable en la ruta local del proyecto o en la instalación global de Windows
base_dir = get_resource_path('')
exe_local = os.path.join(base_dir, 'Tesseract-OCR', 'tesseract.exe')
exe_global = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

if os.path.exists(exe_local):
    pytesseract.pytesseract.tesseract_cmd = exe_local
    os.environ['TESSDATA_PREFIX'] = os.path.join(base_dir, 'Tesseract-OCR', 'tessdata')
else:
    pytesseract.pytesseract.tesseract_cmd = exe_global

# --- 3. MEJORA DE RESOLUCIÓN (DPI AWARENESS) ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# --- 4. HERRAMIENTA DE RECORTE (SNIPPING TOOL) ---
class SnippingTool(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.attributes("-fullscreen", True)
        self.attributes("-alpha", 0.3)
        self.attributes("-topmost", True)
        self.configure(cursor="cross")
        self.configure(bg="black")
        
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        self.canvas = tk.Canvas(self, cursor="cross", bg="grey11")
        self.canvas.pack(fill="both", expand=True)
        
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.bind("<Escape>", lambda e: self.destroy())

    def on_button_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        # Rectángulo azul neón para combinar con el tema
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline='#1c54ff', width=2)

    def on_move_press(self, event):
        cur_x, cur_y = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x, end_y = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        self.destroy()
        if (x2 - x1) > 5 and (y2 - y1) > 5:
            self.callback((x1, y1, x2, y2))

# --- 5. INTERFAZ GRÁFICA PRINCIPAL ---
class AppOCR(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuración de Ventana
        self.title("OCR Sniper")
        self.geometry("700x500") 
        
        # Tema Oscuro Personalizado
        ctk.set_appearance_mode("Dark")
        self.configure(fg_color="#050505") 

        # Cargar Icono
        try:
            icon_path = get_resource_path("logo.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass
        
        # Título
        self.lbl_titulo = ctk.CTkLabel(
            self, 
            text="EXTRACTOR DE TEXTO", 
            font=("Segoe UI", 24, "bold"),
            text_color="white"
        )
        self.lbl_titulo.pack(pady=(30, 15))

        # Botón Grande
        self.btn_capturar = ctk.CTkButton(
            self, 
            text="✂  SELECCIONAR ÁREA", 
            command=self.iniciar_recorte, 
            height=60, 
            width=250,
            font=("Segoe UI", 16, "bold"),
            fg_color="#1c54ff",    
            hover_color="#0033cc", 
            corner_radius=10
        )
        self.btn_capturar.pack(pady=10)

        # Estado
        self.lbl_info = ctk.CTkLabel(self, text="Listo para escanear...", text_color="gray")
        self.lbl_info.pack(pady=5)
        
        # Caja de Texto
        self.resultado_txt = ctk.CTkTextbox(
            self, 
            width=600, 
            height=250,
            fg_color="#111111",      
            text_color="#e0e0e0",    
            border_color="#1c54ff",  
            border_width=1,
            font=("Consolas", 14)    
        )
        self.resultado_txt.pack(pady=20, padx=20, fill="both", expand=True)

    def iniciar_recorte(self):
        self.iconify()
        self.after(200, lambda: SnippingTool(self, self.procesar_captura))

    def procesar_captura(self, bbox):
        self.deiconify()
        self.lbl_info.configure(text="Procesando...", text_color="#1c54ff")
        self.update() 
        
        try:
            img = ImageGrab.grab(bbox=bbox)
            config_simple = '--psm 6'
            
            # Ejecuta Tesseract en la imagen capturada
            texto = pytesseract.image_to_string(img, lang='spa+eng', config=config_simple)
            texto_limpio = texto.strip()
            
            self.resultado_txt.delete("0.0", "end")
            
            if texto_limpio:
                pyperclip.copy(texto_limpio)
                self.resultado_txt.insert("0.0", texto_limpio)
                self.lbl_info.configure(text="TEXTO COPIADO AL PORTAPAPELES", text_color="#00ff00") 
            else:
                self.resultado_txt.insert("0.0", "--- No se detectó texto ---")
                self.lbl_info.configure(text="⚠ No se encontró texto", text_color="orange")
                
        except Exception as e:
            self.resultado_txt.insert("0.0", f"Error de Tesseract: {str(e)}")
            self.lbl_info.configure(text="Error", text_color="red")

if __name__ == "__main__":
    app = AppOCR()
    app.mainloop()