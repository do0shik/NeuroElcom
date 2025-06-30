import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QScrollArea, QLabel, QFrame, QScrollBar)
from PyQt5.QtCore import Qt, QSize, QPoint, QRect
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QPalette

class CustomScrollBar(QScrollBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(20)
        self.setMinimum(0)  # Устанавливаем минимальное значение
        self.setMaximum(100)  # Устанавливаем максимальное значение
        self.handle_color = QColor(194, 194, 194)
        self.track_color = QColor(244, 244, 244)
        self.offset_vertical = 10  # Вертикальный отступ в пикселях
        self.offset_horizontal = 5  # Горизонтальный отступ справа в пикселях

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Рисуем трек
        painter.fillRect(self.rect(), self.track_color)

        # Рассчитываем положение и размер ползунка
        handle_height = int(self.height() * 0.2)  # Высота ползунка как 20% от высоты трека
        max_handle_y = self.height() - handle_height - 2 * self.offset_vertical
        ratio = max_handle_y / (self.maximum() - self.minimum())
        handle_y = int((self.value() - self.minimum()) * ratio + self.offset_vertical)

        # Учитываем горизонтальный отступ справа
        handle_width = self.width() - 4 - self.offset_horizontal
        handle_rect = QRect(2, handle_y, handle_width, handle_height)

        # Рисуем закругленный ползунок
        painter.setBrush(QBrush(self.handle_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(handle_rect, 8, 8)

class ScrollableWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Кастомная прокрутка")
        self.setGeometry(100, 100, 400, 600)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        custom_scrollbar = CustomScrollBar()
        self.scroll_area.setVerticalScrollBar(custom_scrollbar)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignTop)

        for i in range(50):
            frame = QFrame()
            frame.setFrameShape(QFrame.StyledPanel)
            frame.setFixedHeight(80)

            label = QLabel(f"Элемент {i + 1}")
            label.setAlignment(Qt.AlignCenter)

            frame_layout = QVBoxLayout(frame)
            frame_layout.addWidget(label)

            content_layout.addWidget(frame)

        self.scroll_area.setWidget(content_widget)
        main_layout.addWidget(self.scroll_area)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ScrollableWindow()
    window.show()
    sys.exit(app.exec_())
