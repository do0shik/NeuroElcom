import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QComboBox
from PyQt5.QtGui import QIcon, QPixmap, QFontDatabase, QFont
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QTimer
from PyQt5.QtWidgets import QLabel, QPushButton, QFileDialog
import os
import json

CURRENT_IMG_PATH = ""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon('icons/logo_mini.png'))
        self.setWindowTitle("Neuro Elcom")
        self.setGeometry(0, 0, 1920, 1020)
        self.showMaximized()

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.setStyleSheet("QMainWindow { "
                           "background-image: url(icons/Computer. Tab1_beta.png); "
                           "background-position: center;"
                           "}")

        self.image_path = ""
        self.json_path = "example/test.json"

        upload_widget = QWidget()
        main_layout = QVBoxLayout(upload_widget)
        self.stacked_widget.addWidget(upload_widget)
        self.stacked_widget.setCurrentIndex(0)

        self.result_widget = QWidget()
        self.result_layout = QHBoxLayout(self.result_widget)  # Изменили на QHBoxLayout
        self.stacked_widget.addWidget(self.result_widget)

        self.back_button = QPushButton("Back")
        self.back_button.setStyleSheet("QPushButton {font-size: 16px; "
                                       "color: white; background-color: #2A7179; "
                                       "border-radius: 10px; padding: 10px;} "
                                       "QPushButton:hover {background-color: #1A5159;}")
        self.back_button.clicked.connect(self.return_to_upload)

        self.drop_area = DropArea(self)
        main_layout.addWidget(self.drop_area)
        main_layout.setAlignment(Qt.AlignCenter)

        self.logo_label = QLabel()
        icon_path = 'icons/logo_max.png'
        if not os.path.exists(icon_path):
            print(f"Файл не найден! Ищем по пути: {os.path.abspath(icon_path)}")
        else:
            print(f"Файл найден: {os.path.abspath(icon_path)}")
            pixmap = QPixmap(icon_path)
            if pixmap.isNull():
                print("Ошибка: не удалось загрузить изображение!")
            else:
                self.logo_label.setPixmap(pixmap)
                self.logo_label.resize(pixmap.size())

        self.logo_label.move(20, 20)
        self.logo_label.setParent(self)
        self.logo_label.setScaledContents(False)
        self.logo_label.raise_()
        self.logo_label.show()

    def load_data_from_file(self):
        try:
            with open('example/test.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"Загруженные данные: {data}")  # Отладка
                if not data or not isinstance(data, list):
                    print("Неверный формат данных")
                    return None
                return data
        except FileNotFoundError:
            print("Файл test.json не найден")
            return None
        except json.JSONDecodeError:
            print("Ошибка декодирования JSON")
            return None

    def update_result_layout(self, data):
        if not data:
            print("Нет данных для отображения")
            error_label = QLabel("Данные не загружены или пусты")
            error_label.setStyleSheet("font-size: 18px; color: #D32F2F;")
            self.result_layout.addWidget(error_label, alignment=Qt.AlignCenter)
            return

        # 🔧 Удаление лишнего уровня вложенности
        while isinstance(data, list) and len(data) == 1:
            data = data[0]

        # Очистка предыдущих данных
        for i in reversed(range(self.result_layout.count())):
            if self.result_layout.itemAt(i):
                widget = self.result_layout.itemAt(i).widget()
                if widget and widget != self.back_button:
                    widget.setParent(None)

        # Контейнер для списков (левая часть)
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.addStretch()

        switches = []
        transformers = []
        meters = []

        for group in data:
            if not group or not isinstance(group, list):
                continue
            first_item = group[0]
            if 'id' in first_item:
                if first_item['id'].startswith(('14.01', '14.02')):
                    switches.append(group)
                elif first_item['id'].startswith('15'):
                    transformers.append(group)
                elif first_item['id'].startswith('13.03'):
                    meters.append(group)

        categories = [('Автоматические выключатели', switches),
                      ('Трансформаторы', transformers),
                      ('Счетчики "Меркурий"', meters)]

        for category_name, category_groups in categories:
            for group_idx, group in enumerate(category_groups, 1):
                if not group or not isinstance(group, list):
                    continue
                sorted_group = sorted(group, key=lambda x: x['id'])

                combo_id = QComboBox()
                combo_name = QComboBox()
                combo_price = QComboBox()

                for item in sorted_group:
                    combo_id.addItem(item.get('id', 'N/A'), item)
                    combo_name.addItem(item.get('name', 'N/A'), item)
                    combo_price.addItem(str(item.get('price', 'N/A')) + " руб.", item)

                for combo in [combo_id, combo_name, combo_price]:
                    combo.setStyleSheet(
                        "QComboBox {font-size: 16px; color: #2A7179; background-color: rgba(194, 234, 234, 100); border-radius: 5px; padding: 5px;}"
                    )

                def sync_combos(combo, other1, other2):
                    current_item = combo.currentData()
                    if current_item:
                        for i in range(other1.count()):
                            if other1.itemData(i) == current_item:
                                other1.setCurrentIndex(i)
                                break
                        for i in range(other2.count()):
                            if other2.itemData(i) == current_item:
                                other2.setCurrentIndex(i)
                                break

                combo_id.currentIndexChanged.connect(lambda: sync_combos(combo_id, combo_name, combo_price))
                combo_name.currentIndexChanged.connect(lambda: sync_combos(combo_name, combo_id, combo_price))
                combo_price.currentIndexChanged.connect(lambda: sync_combos(combo_price, combo_id, combo_name))

                header = QLabel(f"{category_name} {group_idx}")
                header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2A7179;")
                left_layout.addWidget(header, alignment=Qt.AlignCenter)

                left_layout.addWidget(combo_id, alignment=Qt.AlignCenter)
                left_layout.addWidget(combo_name, alignment=Qt.AlignCenter)
                left_layout.addWidget(combo_price, alignment=Qt.AlignCenter)

        left_layout.addWidget(self.back_button, alignment=Qt.AlignCenter)
        left_layout.addStretch()

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.addStretch()

        if CURRENT_IMG_PATH and os.path.exists(CURRENT_IMG_PATH):
            image_label = QLabel()
            pixmap = QPixmap(CURRENT_IMG_PATH)
            if not pixmap.isNull():
                image_label.setPixmap(pixmap.scaled(800, 800, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                right_layout.addWidget(image_label, alignment=Qt.AlignCenter)
            else:
                right_layout.addWidget(QLabel("Ошибка загрузки изображения"), alignment=Qt.AlignCenter)
        else:
            right_layout.addWidget(QLabel("Изображение не загружено"), alignment=Qt.AlignCenter)

        right_layout.addStretch()

        self.result_layout.addWidget(left_container, 1)
        self.result_layout.addWidget(right_container, 1)
        self.result_layout.setStretch(0, 1)
        self.result_layout.setStretch(1, 1)

    def return_to_upload(self):
        self.stacked_widget.setCurrentIndex(0)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", "Все файлы (*)")
        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    f.read(1)
                self.show_success_message(file_path)
                global CURRENT_IMG_PATH
                CURRENT_IMG_PATH = file_path
            except Exception as e:
                self.drop_area.file_label.setText(f"Ошибка доступа к файлу: {str(e)}")
                self.drop_area.file_label.setStyleSheet(
                    "font-size: 18px; color: #D32F2F; padding: 20px; border: 2px solid #D32F2F; background-color: #FFEBEE;")

    def show_success_message(self, file_path):
        self.success_widget = QWidget(self)
        self.success_widget.setWindowFlags(Qt.FramelessWindowHint)
        self.success_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.success_widget.setFixedSize(300, 100)

        inner_container = QWidget(self.success_widget)
        inner_container.setStyleSheet("""
                   background-color: rgba(235, 235, 235, 100);
                   border-radius: 10px;
                   border: none;
               """)
        inner_layout = QVBoxLayout(inner_container)
        inner_layout.setContentsMargins(20, 10, 20, 10)

        self.success_label = QLabel(f"Файл загружен:\n{file_path}")
        self.success_label.setStyleSheet("border: none; background-color: transparent; font-size: 14px; color: black; padding: 5px; qproperty-alignment: 'AlignCenter'")
        self.success_label.setWordWrap(True)
        inner_layout.addWidget(self.success_label, alignment=Qt.AlignCenter)

        outer_layout = QVBoxLayout(self.success_widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(inner_container)

        center_x = self.rect().center().x()
        center_y = self.rect().center().y()
        self.success_widget.move(center_x - 150, center_y + 180)
        self.success_widget.show()

        self.animation_in = QPropertyAnimation(self.success_widget, b"windowOpacity")
        self.animation_in.setDuration(500)
        self.animation_in.setStartValue(0)
        self.animation_in.setEndValue(1)
        self.animation_in.start()

        self.animation_out = QPropertyAnimation(self.success_widget, b"windowOpacity")
        self.animation_out.setDuration(500)
        self.animation_out.setStartValue(1)
        self.animation_out.setEndValue(0)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.start_fade_out)
        self.timer.start()

        self.animation_out.finished.connect(self.cleanup_success_widget)

    def start_fade_out(self):
        self.animation_out.start()
        self.timer.stop()

    def cleanup_success_widget(self):
        if self.success_widget:
            self.success_widget.deleteLater()
            self.success_widget = None
            self.stacked_widget.setCurrentIndex(1)
            data = self.load_data_from_file()
            if data:
                self.update_result_layout(data)

    def handle_file_load(self, path):
        global CURRENT_IMG_PATH
        self.show_success_message(path)
        CURRENT_IMG_PATH = path
        data = self.load_data_from_file()
        if data:
            self.update_result_layout(data)

class DropArea(QWidget):
    def __init__(self, start_w):
        super().__init__()
        self.start_w = start_w
        self.setAcceptDrops(True)
        self.drop_label = QLabel(self)
        self.drop_label.setText("")
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setFixedSize(1500, 600)
        self.setFixedSize(1600, 700)
        drop_center = self.drop_label.rect().center()
        drop_pos = self.drop_label.pos()
        self.drop_label.raise_()

        layout = QVBoxLayout(self)
        layout.addWidget(self.drop_label, alignment=Qt.AlignCenter)
        self.setStyleSheet("background-color: transparent;")
        self.drop_label.setStyleSheet("font: bold 14px;"
                                      "color: black;"
                                      "background-color: transparent;"
                                      "padding: 20px;"
                                      "border: 2px dashed #A4A4A4;"
                                      "border-radius: 10px;")

        self.file_button = QPushButton(self.drop_label)
        self.file_button.setIcon(QIcon("icons/download.png"))
        self.file_button.setIconSize(QSize(64, 64))
        self.file_button.setStyleSheet("""
                    QPushButton {
                        border: none !important;
                        background: transparent !important;
                        border-radius: 10px !important;
                        padding: 5px;
                        background: rgba(194, 234, 234, 100) !important;
                    }
                    QPushButton:hover {
                        background: rgba(152, 227, 227, 100) !important;
                    }
                    QPushButton:pressed {
                        background: rgba(116, 200, 200, 100) !important;
                    }
                """)

        pixmap = QPixmap("icons/download.png")
        icon_size = pixmap.size()
        self.file_button.setFixedSize(icon_size.width() + 5, icon_size.height() + 5)
        self.file_button.clicked.connect(self.start_w.select_file)
        button_size = self.file_button.size()
        button_x = drop_pos.x() + drop_center.x() - button_size.width() // 2
        button_y = drop_pos.y() + drop_center.y() - button_size.height() // 2 - 50
        self.file_button.move(button_x, button_y)
        self.file_button.show()

        self.download_label = QLabel(f"Выберите файл или перетащите сюда")
        self.download_label.setParent(self.drop_label)
        self.download_label.setStyleSheet(
            "font-size: 18px ; font-weight: bold; color: #2A7179; padding: 10px; border: none; background-color: transparent;")
        self.download_label.setFixedSize(402, 50)
        self.download_label.move(
            drop_pos.x() + drop_center.x() - 201,
            drop_pos.y() + drop_center.y()
        )
        self.download_label.setScaledContents(False)
        self.download_label.show()

        self.format_label = QLabel(f"Формат *.png, *.jpg, *.jpeg")
        self.format_label.setParent(self.drop_label)
        self.format_label.setStyleSheet(
            "font-size: 14px; color: #A8A8A8; padding: 10px; border: none; background-color: transparent;")
        self.format_label.setFixedSize(260, 50)
        self.format_label.move(
            drop_pos.x() + drop_center.x() - 120,
            drop_pos.y() + drop_center.y() + 27
        )
        self.format_label.setScaledContents(False)
        self.format_label.show()

        self.overlay = QLabel(self.drop_label)
        self.overlay.setStyleSheet("font: bold 25px; color: white; background-color: rgba(67, 134, 139, 230); border-radius: 10px;")
        self.overlay.setGeometry(self.drop_label.rect())
        self.overlay.hide()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.overlay.setAlignment(Qt.AlignCenter)
            self.overlay.setText("Перетащите файл сюда")
            self.overlay.show()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                if path:
                    try:
                        with open(path, 'rb') as u:
                            u.read(1)
                        global CURRENT_IMG_PATH
                        self.start_w.handle_file_load(path)
                        event.acceptProposedAction()
                        CURRENT_IMG_PATH = path
                        self.overlay.hide()
                    except Exception as e:
                        event.ignore()
                else:
                    event.ignore()
            else:
                event.ignore()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.overlay.hide()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    font_db = QFontDatabase()
    font_id = font_db.addApplicationFont("font/Manrope-VariableFont_wght.ttf")
    if font_id != -1:
        font_family = font_db.applicationFontFamilies(font_id)[0]
        app.setFont(QFont(font_family, 10))
    else:
        print("Не удалось загрузить шрифт")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())