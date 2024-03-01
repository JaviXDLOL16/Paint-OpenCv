import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk


class PaintApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Paint App")
        self.root.resizable(False, False)  # Evitar redimensionar la ventana

        self.container = tk.Frame(root)
        self.container.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        self.canvas_frame = tk.Frame(self.container)
        self.canvas_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.canvas = tk.Canvas(
            self.canvas_frame, bg="white", width=600, height=600, cursor="cross")
        self.canvas.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        # Create floating menu
        self.menu_frame = tk.Frame(self.container, width=100)
        self.menu_frame.pack(side=tk.RIGHT, padx=5, pady=5)

        self.selected_tool = tk.StringVar()

        tools = [("Línea", "line", "images\Linea.png"), 
                        ("Polilínea", "freehand", "images\Lapiz.png"), 
                        ("Rectángulo", "rectangle", "images\Rectangulo.png"),
                        ("Círculo", "circle", "images\Circulo.png"), 
                        ("Borrador", "eraser", "images\Borrador.png")]

        for tool_name, tool_type, icon_path in tools:
            icon = self.load_icon(icon_path)
            btn = tk.Button(self.menu_frame, image=icon, text=tool_name, compound=tk.TOP, command=lambda t=tool_type: self.selected_tool.set(t))
            btn.image = icon  # Esto es importante para evitar que Python "limpie" la imagen de memoria
            btn.pack(fill=tk.X, padx=5, pady=5)

        self.cv_image = np.ones(
            (600, 600, 3), dtype=np.uint8) * 255  # Lienzo blanco
        self.cv_image = cv2.cvtColor(self.cv_image, cv2.COLOR_BGR2RGB)
        self.photo = self.convert_cv_to_photo(self.cv_image)
        self.canvas_image = self.canvas.create_image(
            0, 0, anchor=tk.NW, image=self.photo)

        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.end_draw)

        # Variables para el manejo de redimensionamiento
        self.prev_width = self.canvas.winfo_width()
        self.prev_height = self.canvas.winfo_height()

        # Variables para arrastrar y soltar la pestaña del menú flotante
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0

        # Inicializar la funcionalidad de arrastrar y soltar
        self.container.bind("<ButtonPress-1>", self.on_drag_start)
        self.container.bind("<ButtonRelease-1>", self.on_drag_stop)
        self.container.bind("<B1-Motion>", self.on_drag_motion)

    def start_draw(self, event):
        self.start_x = event.x
        self.start_y = event.y

        self.color = (0, 0, 0)  # Color negro
        self.size = 2

        self.tool_type = self.selected_tool.get()

        if self.tool_type == "eraser":
            self.color = (255, 255, 255)  # Color blanco

        if self.tool_type == "freehand":
            self.prev_x = event.x
            self.prev_y = event.y

        self.drawing = True
        if self.tool_type != "freehand":
            self.cv_image_copy = self.cv_image.copy()

    def draw(self, event):
        if self.drawing and self.tool_type != "eraser":
            if self.tool_type == "line":
                self.draw_line(event.x, event.y)
            elif self.tool_type == "freehand":
                self.draw_freehand(event.x, event.y)
            elif self.tool_type == "rectangle":
                self.draw_rectangle(event.x, event.y)
            elif self.tool_type == "circle":
                self.draw_circle(event.x, event.y)
        elif self.tool_type == "eraser":
            self.erase(event.x, event.y)

    def end_draw(self, event):
        self.drawing = False
        if hasattr(self, 'cv_image_copy'):
            del self.cv_image_copy

    def draw_line(self, end_x, end_y):
        if self.drawing:
            self.cv_image = self.cv_image_copy.copy()
            self.cv_image = cv2.line(
                self.cv_image, (self.start_x, self.start_y), (end_x, end_y), self.color, self.size)
            self.update_canvas()

    def draw_freehand(self, x, y):
        if not hasattr(self, 'prev_x') or not hasattr(self, 'prev_y'):
            self.prev_x = x
            self.prev_y = y

        self.cv_image = cv2.line(
            self.cv_image, (self.prev_x, self.prev_y), (x, y), self.color, self.size)
        self.update_canvas()
        self.prev_x = x
        self.prev_y = y

    def draw_rectangle(self, end_x, end_y):
        if self.drawing:
            self.cv_image = self.cv_image_copy.copy()
            self.cv_image = cv2.rectangle(
                self.cv_image, (self.start_x, self.start_y), (end_x, end_y), self.color, self.size)
            self.update_canvas()

    def draw_circle(self, end_x, end_y):
        if self.drawing:
            self.cv_image = self.cv_image_copy.copy()
            radius_x = abs(end_x - self.start_x)
            radius_y = abs(end_y - self.start_y)
            center_x = min(end_x, self.start_x) + radius_x
            center_y = min(end_y, self.start_y) + radius_y
            self.cv_image = cv2.ellipse(
                self.cv_image, (center_x, center_y), (radius_x, radius_y), 0, 0, 360, self.color, self.size)
            self.update_canvas()

    def erase(self, x, y):
        erase_size = 20
        self.cv_image[max(0, y - erase_size):min(600, y + erase_size),
                      max(0, x - erase_size):min(600, x + erase_size)] = (255, 255, 255)
        self.update_canvas()

    def update_canvas(self):
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        self.cv_image = cv2.resize(self.cv_image, (width, height))
        self.cv_image = cv2.cvtColor(self.cv_image, cv2.COLOR_BGR2RGB)
        self.photo = self.convert_cv_to_photo(self.cv_image)
        self.canvas.itemconfig(self.canvas_image, image=self.photo)

    def convert_cv_to_photo(self, cv_image):
        return ImageTk.PhotoImage(data=cv2.imencode('.png', cv_image)[1].tobytes())

    def load_icon(self, path):
        image = Image.open(path)
        image = image.resize((24, 24))
        return ImageTk.PhotoImage(image)

    def on_drag_start(self, event):
        self.dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_drag_stop(self, event):
        self.dragging = False

    def on_drag_motion(self, event):
        if self.dragging:
            x = self.root.winfo_x() - self.drag_start_x + event.x
            y = self.root.winfo_y() - self.drag_start_y + event.y
            self.root.geometry(f'+{x}+{y}')


if __name__ == "__main__":
    root = tk.Tk()
    app = PaintApp(root)
    root.mainloop()
