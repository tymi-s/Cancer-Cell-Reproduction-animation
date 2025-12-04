import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QSlider, QFileDialog)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap
from PIL import Image


class CancerCellSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Symulator Rozprzestrzeniania Komórek Rakowych")
        self.setGeometry(100, 100, 900, 700)

        self.grid_size = 200
        self.cell_size = 3
        self.spread_rate = 0.3
        self.generation = 0
        self.is_running = False

        self.grid = np.zeros((self.grid_size, self.grid_size), dtype=np.uint8)
        self.background_image = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_generation)

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        title = QLabel("Symulator Rozprzestrzeniania Komórek Rakowych")
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        control_layout = QHBoxLayout()

        self.load_btn = QPushButton("Wczytaj Zdjęcie Skóry")
        self.load_btn.clicked.connect(self.load_image)
        control_layout.addWidget(self.load_btn)

        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.toggle_simulation)
        control_layout.addWidget(self.start_btn)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_simulation)
        control_layout.addWidget(self.reset_btn)

        main_layout.addLayout(control_layout)

        speed_layout = QHBoxLayout()
        speed_label = QLabel("Szybkość rozprzestrzeniania:")
        speed_layout.addWidget(speed_label)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(9)
        self.speed_slider.setValue(3)
        self.speed_slider.valueChanged.connect(self.update_spread_rate)
        speed_layout.addWidget(self.speed_slider)

        self.speed_value_label = QLabel(f"{self.spread_rate:.1f}")
        speed_layout.addWidget(self.speed_value_label)

        main_layout.addLayout(speed_layout)

        stats_layout = QHBoxLayout()

        self.gen_label = QLabel("Generacja: 0")
        self.gen_label.setStyleSheet("padding: 5px; background-color: #e0e0e0; border-radius: 5px;")
        stats_layout.addWidget(self.gen_label)

        self.cancer_label = QLabel("Komórki rakowe: 0")
        self.cancer_label.setStyleSheet("padding: 5px; background-color: #ffcccc; border-radius: 5px;")
        stats_layout.addWidget(self.cancer_label)

        self.healthy_label = QLabel("Zdrowe tkanki: 100.0%")
        self.healthy_label.setStyleSheet("padding: 5px; background-color: #ccffcc; border-radius: 5px;")
        stats_layout.addWidget(self.healthy_label)

        main_layout.addLayout(stats_layout)

        self.canvas_label = QLabel()
        self.canvas_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas_label.setStyleSheet("border: 2px solid #333; background-color: #fdd8b5;")
        main_layout.addWidget(self.canvas_label)

        info = QLabel(
            "Instrukcja:\n"
            "1. Wczytaj zdjęcie skóry - ciemne obszary (pieprzyki) staną się komórkami rakowymi\n"
            "2. Naciśnij Start, aby rozpocząć symulację rozprzestrzeniania\n"
            "3. Dostosuj szybkość rozprzestrzeniania suwakiem"
        )
        info.setStyleSheet("padding: 10px; background-color: #e3f2fd; border-radius: 5px; font-size: 11px;")
        main_layout.addWidget(info)

        self.draw_canvas()

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Wybierz zdjęcie skóry", "", "Obrazy (*.png *.jpg *.jpeg *.bmp)"
        )

        if not file_path:
            return

        img = Image.open(file_path).convert('RGB')
        img = img.resize((self.grid_size, self.grid_size))

        img_array = np.array(img)

        self.background_image = img_array.copy()

        brightness = np.mean(img_array, axis=2)

        self.grid = (brightness < 100).astype(np.uint8)

        self.generation = 0
        self.update_stats()
        self.draw_canvas()

    def update_spread_rate(self, value):
        self.spread_rate = value / 10.0
        self.speed_value_label.setText(f"{self.spread_rate:.1f}")

    def toggle_simulation(self):
        if self.is_running:
            self.is_running = False
            self.timer.stop()
            self.start_btn.setText("Start")
        else:
            self.is_running = True
            self.timer.start(200)
            self.start_btn.setText("Pauza")

    def reset_simulation(self):
        self.grid = np.zeros((self.grid_size, self.grid_size), dtype=np.uint8)
        self.generation = 0
        self.background_image = None
        self.is_running = False
        self.timer.stop()
        self.start_btn.setText("Start")
        self.update_stats()
        self.draw_canvas()

    def update_generation(self):
        kernel = np.array([[1, 1, 1],
                           [1, 0, 1],
                           [1, 1, 1]], dtype=np.uint8)

        padded = np.pad(self.grid, 1, mode='constant', constant_values=0)

        neighbors = np.zeros_like(self.grid, dtype=np.int32)
        for i in range(3):
            for j in range(3):
                if i == 1 and j == 1:
                    continue
                neighbors += padded[i:i + self.grid_size, j:j + self.grid_size] * kernel[i, j]

        new_grid = self.grid.copy()

        healthy_mask = (self.grid == 0)
        infection_prob = np.random.random((self.grid_size, self.grid_size))
        infection_threshold = self.spread_rate * (neighbors / 8.0)

        new_infections = healthy_mask & (neighbors > 0) & (infection_prob < infection_threshold)
        new_grid[new_infections] = 1

        self.grid = new_grid
        self.generation += 1

        self.update_stats()
        self.draw_canvas()

    def update_stats(self):
        cancer_cells = np.sum(self.grid)
        total_cells = self.grid_size * self.grid_size
        healthy_percent = (1 - cancer_cells / total_cells) * 100

        self.gen_label.setText(f"Generacja: {self.generation}")
        self.cancer_label.setText(f"Komórki rakowe: {cancer_cells}")
        self.healthy_label.setText(f"Zdrowe tkanki: {healthy_percent:.1f}%")

    def draw_canvas(self):
        width = self.grid_size * self.cell_size
        height = self.grid_size * self.cell_size

        if self.background_image is not None:
            img_array = self.background_image.copy()

            cancer_mask = self.grid == 1
            img_array[cancer_mask] = [139, 0, 0]

            height_img, width_img, channel = img_array.shape
            bytes_per_line = 3 * width_img
            q_img = QImage(img_array.data, width_img, height_img, bytes_per_line, QImage.Format.Format_RGB888)

        else:
            img_array = np.full((self.grid_size, self.grid_size, 3), [253, 216, 181], dtype=np.uint8)

            cancer_mask = self.grid == 1
            img_array[cancer_mask] = [139, 0, 0]

            height_img, width_img, channel = img_array.shape
            bytes_per_line = 3 * width_img
            q_img = QImage(img_array.data, width_img, height_img, bytes_per_line, QImage.Format.Format_RGB888)

        pixmap = QPixmap.fromImage(q_img).scaled(
            width, height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation
        )

        self.canvas_label.setPixmap(pixmap)


def main():
    app = QApplication(sys.argv)
    window = CancerCellSimulator()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()