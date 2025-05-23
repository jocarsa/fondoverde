import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np
import os
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class RemovedorCromaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Eliminador de Fondo Verde")
        self.root.geometry("1400x700")

        self.imagen = None
        self.ruta_imagen = None
        self.resultado_rgba = None
        self.mascara = None

        # Layout principal
        self.marco_izquierdo = ttk.Frame(root, padding=10)
        self.marco_izquierdo.pack(side=tk.LEFT, fill=tk.Y)

        self.marco_derecho = ttk.Frame(root, padding=10)
        self.marco_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Canvases para original, resultado, máscara
        self.canvas_original = tk.Canvas(self.marco_derecho, bg="black", highlightthickness=1)
        self.canvas_resultado = tk.Canvas(self.marco_derecho, bg="black", highlightthickness=1)
        self.canvas_mascara = tk.Canvas(self.marco_derecho, bg="black", highlightthickness=1)

        self.canvas_original.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.canvas_resultado.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.canvas_mascara.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # Botones
        ttk.Button(self.marco_izquierdo, text="Cargar imagen", command=self.cargar_imagen, bootstyle=PRIMARY).pack(pady=5, fill=X)
        ttk.Button(self.marco_izquierdo, text="Guardar como...", command=self.guardar_imagen, bootstyle=SUCCESS).pack(pady=5, fill=X)

        self.estado = ttk.Label(self.marco_izquierdo, text="", wraplength=250, anchor="w", justify=tk.LEFT)
        self.estado.pack(pady=10)

        self.deslizadores = {}
        self.configurar_deslizadores()

        self.root.bind("<Configure>", lambda e: self.actualizar_vista())

    def configurar_deslizadores(self):
        parametros = [
            ("Tono mínimo", 0, 179, 35),
            ("Saturación mínima", 0, 255, 40),
            ("Valor mínimo", 0, 255, 40),
            ("Tono máximo", 0, 179, 85),
            ("Saturación máxima", 0, 255, 255),
            ("Valor máximo", 0, 255, 255),
        ]
        for nombre, minimo, maximo, por_defecto in parametros:
            ttk.Label(self.marco_izquierdo, text=nombre).pack()
            deslizador = ttk.Scale(self.marco_izquierdo, from_=minimo, to=maximo, orient=tk.HORIZONTAL,
                                   command=lambda val, n=nombre: self.aplicar_filtro())
            deslizador.set(por_defecto)
            deslizador.pack(fill=X, pady=2)
            self.deslizadores[nombre] = deslizador

        # Feather / Desvanecido
        ttk.Label(self.marco_izquierdo, text="Desvanecido (Feather)").pack()
        feather = ttk.Scale(self.marco_izquierdo, from_=0, to=30, orient=tk.HORIZONTAL,
                            command=lambda val: self.aplicar_filtro())
        feather.set(5)
        feather.pack(fill=X, pady=2)
        self.deslizadores["Desvanecido"] = feather

    def cargar_imagen(self):
        ruta = filedialog.askopenfilename(filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.bmp")])
        if not ruta:
            return
        self.ruta_imagen = ruta
        self.imagen = cv2.imread(ruta)
        self.aplicar_filtro()

    def aplicar_filtro(self):
        if self.imagen is None:
            return

        inferior = np.array([
            self.deslizadores["Tono mínimo"].get(),
            self.deslizadores["Saturación mínima"].get(),
            self.deslizadores["Valor mínimo"].get()
        ])
        superior = np.array([
            self.deslizadores["Tono máximo"].get(),
            self.deslizadores["Saturación máxima"].get(),
            self.deslizadores["Valor máximo"].get()
        ])
        feather = int(self.deslizadores["Desvanecido"].get())

        hsv = cv2.cvtColor(self.imagen, cv2.COLOR_BGR2HSV)
        mascara = cv2.inRange(hsv, inferior, superior)
        self.mascara = mascara

        if feather > 0:
            inv_mascara = 255 - mascara
            distancia = cv2.distanceTransform(inv_mascara, cv2.DIST_L2, 5)
            distancia = np.clip(distancia, 0, feather)
            alpha = (distancia / feather) * 255
            alpha = alpha.astype(np.uint8)
        else:
            alpha = np.where(mascara > 0, 0, 255).astype(np.uint8)

        rgba = cv2.cvtColor(self.imagen, cv2.COLOR_BGR2BGRA)
        rgba[..., 3] = alpha
        self.resultado_rgba = rgba

        self.actualizar_vista()

    def actualizar_vista(self):
        if self.imagen is None or self.resultado_rgba is None:
            return

        # Imagen original
        self.mostrar_imagen(self.imagen, self.canvas_original)

        # Resultado (mostrar con alfa sobre negro como antes)
        vista_resultado = self.resultado_rgba.copy()
        self.mostrar_imagen(vista_resultado, self.canvas_resultado)

        # Máscara blanco y negro
        if self.mascara is not None:
            mascara_rgb = cv2.cvtColor(self.mascara, cv2.COLOR_GRAY2RGB)
            self.mostrar_imagen(mascara_rgb, self.canvas_mascara)

    def mostrar_imagen(self, imagen_cv, canvas):
        canvas.update()
        h_canvas = canvas.winfo_height()
        h_img, w_img = imagen_cv.shape[:2]
        escala = h_canvas / h_img if h_img > 0 else 1
        nuevo_ancho = int(w_img * escala)
        nuevo_alto = int(h_img * escala)

        redimensionada = cv2.resize(imagen_cv, (nuevo_ancho, nuevo_alto), interpolation=cv2.INTER_AREA)

        if redimensionada.shape[2] == 4:
            if canvas == self.canvas_resultado:
                img_rgb = cv2.cvtColor(redimensionada, cv2.COLOR_BGRA2RGBA)  # ✅ Esta conversión mantiene transparencia sobre negro
            else:
                img_rgb = cv2.cvtColor(redimensionada, cv2.COLOR_BGRA2RGB)
        else:
            img_rgb = cv2.cvtColor(redimensionada, cv2.COLOR_BGR2RGB)

        imagen_pil = Image.fromarray(img_rgb)
        imagen_tk = ImageTk.PhotoImage(imagen_pil)

        canvas.delete("all")
        canvas.image = imagen_tk
        canvas.create_image(canvas.winfo_width() // 2, 0, anchor=tk.N, image=imagen_tk)

    def guardar_imagen(self):
        if self.resultado_rgba is None or self.ruta_imagen is None:
            return
        nombre_base, _ = os.path.splitext(os.path.basename(self.ruta_imagen))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"{nombre_base}_transparente_{timestamp}.png"
        ruta_guardar = filedialog.asksaveasfilename(defaultextension=".png", initialfile=nombre_archivo,
                                                    filetypes=[("Imagen PNG", "*.png")])
        if ruta_guardar:
            cv2.imwrite(ruta_guardar, self.resultado_rgba)
            self.estado.config(text=f"✅ Imagen guardada en:\n{ruta_guardar}")

# Ejecutar aplicación
app = ttk.Window(themename="cyborg")
RemovedorCromaApp(app)
app.mainloop()
