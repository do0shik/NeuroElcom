import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QComboBox, QLabel, QPushButton, QFileDialog, QScrollArea, QHBoxLayout
from PyQt5.QtGui import QIcon, QPixmap, QFontDatabase, QFont
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QTimer
import os
import json

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

        # Инициализация путей
        self.image_path = ""
        self.json_path = "example/test.json"  # Фиксированный путь к JSON

        upload_widget = QWidget()
        main_layout = QVBoxLayout(upload_widget)
        self.stacked_widget.addWidget(upload_widget)
        self.stacked_widget.setCurrentIndex(0)

        # Используем QScrollArea для прокрутки второго экрана
        scroll_area = QScrollArea()
        self.result_widget = QWidget()
        self.result_layout = QVBoxLayout(self.result_widget)
        scroll_area.setWidget(self.result_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.stacked_widget.addWidget(scroll_area)

        self.back_button = QPushButton("Back")
        self.back_button.setStyleSheet("QPushButton {font-size: 16px; "
                                       "color: white; background-color: #2A7179; "
                                       "border-radius: 10px; padding: 10px;} "
                                       "QPushButton:hover {background-color: #1A5159;}")
        self.back_button.clicked.connect(self.return_to_upload)
        self.result_layout.addWidget(self.back_button, alignment=Qt.AlignCenter)

        self.drop_area = DropArea(self)
        main_layout.addWidget(self.drop_area)
        main_layout.setAlignment(Qt.AlignCenter)

        self.logo_label = QLabel()
        icon_path = 'icons/logo_max.png'
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                self.logo_label.setPixmap(pixmap)
                self.logo_label.resize(pixmap.size())
        self.logo_label.move(20, 20)
        self.logo_label.setParent(self)
        self.logo_label.setScaledContents(False)
        self.logo_label.raise_()
        self.logo_label.show()

    def load_data_from_file(self, file_path=None):
        try:
            if file_path and file_path.lower().endswith('.json'):
                print(f"Попытка загрузки файла: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"Содержимое файла {file_path}: {content[:200]}...")  # Отладка
                    data = json.loads(content)
                    # Обработка вложенности
                    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                        flattened_groups = []
                        for category in data:
                            if isinstance(category, list):
                                for group in category:
                                    if isinstance(group, list):
                                        flattened_groups.append(group)
                        return flattened_groups
                    print(f"Неверный формат данных в {file_path}")
                    return None
            else:
                print(f"Не указан JSON-файл или неверный формат: {file_path}")
                return None
        except FileNotFoundError:
            print(f"Файл {file_path} не найден")
            return None
        except json.JSONDecodeError as e:
            print(f"Ошибка декодирования JSON в {file_path}: {e} на позиции {e.pos}")
            return None
        except Exception as e:
            print(f"Неожиданная ошибка при загрузке {file_path}: {e}")
            return None

    def update_result_layout(self, data):
        if not data:
            print("Нет данных для отображения")
            error_label = QLabel("Ошибка: данные не загружены или пусты")
            error_label.setStyleSheet("font-size: 18px; color: #D32F2F;")
            self.result_layout.addWidget(error_label, alignment=Qt.AlignCenter)
            return

        # Очистка предыдущих данных
        for i in reversed(range(self.result_layout.count())):
            if self.result_layout.itemAt(i):
                widget = self.result_layout.itemAt(i).widget()
                if widget and widget != self.back_button:
                    widget.setParent(None)

        # Создаем контейнер для результатов с прозрачным фоном
        result_container = QWidget()
        result_container.setStyleSheet("background-color: transparent;")
        container_layout = QVBoxLayout(result_container)

        # Обработка каждой группы
        for group_idx, group in enumerate(data, 1):
            if not group or not isinstance(group, list):
                continue

            first_item = group[0] if group else {}
            category = "Автоматические выключатели" if first_item.get('id', '').startswith(('14.01', '14.02')) else \
                "Трансформаторы" if first_item.get('id', '').startswith(('ITB', 'ITT')) else \
                    "Счетчики 'Меркурий'" if first_item.get('id', '').startswith('13.03') or first_item.get(
                        'id') == '1' else "Неизвестно"

            sorted_group = sorted(group, key=lambda x: x.get('id', ''))

            # Создаем горизонтальный контейнер для группы
            group_container = QWidget()
            group_container.setStyleSheet(
                "background-color: rgba(255, 255, 255, 150); border-radius: 10px; padding: 10px;")
            group_layout = QVBoxLayout(group_container)

            # Заголовок группы
            header = QLabel(f"{category} {group_idx}")
            header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2A7179;")
            group_layout.addWidget(header)

            # Создаем горизонтальный контейнер для выпадающих списков
            combos_container = QWidget()
            combos_layout = QHBoxLayout(combos_container)
            combos_layout.setSpacing(10)

            combo_id = QComboBox()
            combo_name = QComboBox()
            combo_price = QComboBox()

            for item in sorted_group:
                combo_id.addItem(item.get('id', 'N/A'), item)
                combo_name.addItem(item.get('name', 'N/A'), item)
                combo_price.addItem(f"{item.get('price', 'N/A')} руб.", item)

            # Настройка стилей
            for combo in [combo_id, combo_name, combo_price]:
                combo.setStyleSheet("""
                    QComboBox {
                        font-size: 14px; 
                        color: #2A7179; 
                        background-color: rgba(194, 234, 234, 200); 
                        border-radius: 5px; 
                        padding: 5px;
                        min-width: 200px;
                    }
                    QComboBox::drop-down {
                        border: none;
                    }
                """)

            # Добавляем выпадающие списки в горизонтальный layout
            combos_layout.addWidget(QLabel("ID:"))
            combos_layout.addWidget(combo_id)
            combos_layout.addWidget(QLabel("Наименование:"))
            combos_layout.addWidget(combo_name)
            combos_layout.addWidget(QLabel("Цена:"))
            combos_layout.addWidget(combo_price)
            combos_layout.addStretch()

            # Функция для синхронизации комбобоксов
            def create_sync_func(c1, c2, c3):
                def sync_combos():
                    sender = self.sender()
                    current_item = sender.currentData()
                    if current_item:
                        for combo in [c1, c2, c3]:
                            if combo != sender:
                                combo.blockSignals(True)
                                for i in range(combo.count()):
                                    if combo.itemData(i) == current_item:
                                        combo.setCurrentIndex(i)
                                        break
                                combo.blockSignals(False)

                return sync_combos

            # Связываем сигналы
            sync_func = create_sync_func(combo_id, combo_name, combo_price)
            combo_id.currentIndexChanged.connect(sync_func)
            combo_name.currentIndexChanged.connect(sync_func)
            combo_price.currentIndexChanged.connect(sync_func)

            # Добавляем в группу
            group_layout.addWidget(combos_container)
            container_layout.addWidget(group_container)

        # Добавляем контейнер с результатами и кнопку "Назад"
        self.result_layout.addWidget(result_container)
        if not self.result_layout.indexOf(self.back_button) >= 0:
            self.result_layout.addWidget(self.back_button, alignment=Qt.AlignCenter)

        # Устанавливаем отступы и выравнивание
        self.result_layout.setContentsMargins(50, 20, 50, 20)
        self.result_layout.setAlignment(Qt.AlignTop)

    def return_to_upload(self):
        self.stacked_widget.setCurrentIndex(0)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", "Изображения (*.png *.jpg *.jpeg);;JSON Files (*.json);;Все файлы (*)")
        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    f.read(1)
                print(f"Выбран файл: {file_path}")
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    self.image_path = file_path
                    self.show_success_message(file_path)
                    # Автоматическая загрузка JSON после изображения
                    data = self.load_data_from_file(self.json_path)
                    if data:
                        print("Данные из JSON загружены, переход на второй экран")
                        self.stacked_widget.setCurrentIndex(1)
                        self.update_result_layout(data)
                    else:
                        print(f"Не удалось загрузить данные из {self.json_path}")
                elif file_path.lower().endswith('.json'):
                    self.json_path = file_path
                    print(f"JSON путь обновлен: {self.json_path}")
                    data = self.load_data_from_file(self.json_path)
                    if data:
                        print("Данные загружены, переход на второй экран")
                        self.stacked_widget.setCurrentIndex(1)
                        self.update_result_layout(data)
                    else:
                        print("Данные не загружены, переход не выполнен")
            except Exception as e:
                self.drop_area.drop_label.setText(f"Ошибка доступа к файлу: {str(e)}")
                self.drop_area.drop_label.setStyleSheet(
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

        self.success_label = QLabel(f"Файл загружен:\n{os.path.basename(file_path)}")
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
            # Автоматическая загрузка JSON после завершения анимации
            print(f"Проверка JSON пути в cleanup: {self.json_path}")
            data = self.load_data_from_file(self.json_path)
            if data:
                print("Данные загружены в cleanup, переход на второй экран")
                self.stacked_widget.setCurrentIndex(1)
                self.update_result_layout(data)
            else:
                print(f"Не удалось загрузить данные из {self.json_path} в cleanup")

    def handle_file_load(self, path):
        if path.lower().endswith(('.png', '.jpg', '.jpeg')):
            self.image_path = path
        self.show_success_message(path)

class DropArea(QWidget):
    def __init__(self, start_w):
        super().__init__()
        self.start_w = start_w
        self.setAcceptDrops(True)
        self.drop_label = QLabel(self)
        self.drop_label.setText("Перетащите изображение или выберите файл")
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setFixedSize(1500, 600)
        self.setFixedSize(1600, 700)
        drop_center = self.drop_label.rect().center()
        drop_pos = self.drop_label.pos()
        self.drop_label.raise_()

        layout = QVBoxLayout(self)
        layout.addWidget(self.drop_label, alignment=Qt.AlignCenter)
        self.setStyleSheet("background-color: transparent;")
        self.drop_label.setStyleSheet("font: bold 14px; color: black; background-color: transparent; "
                                      "padding: 20px; border: 2px dashed #A4A4A4; border-radius: 10px;")

        self.file_button = QPushButton(self.drop_label)
        self.file_button.setIcon(QIcon("icons/download.png"))
        self.file_button.setIconSize(QSize(64, 64))
        self.file_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                border-radius: 10px;
                padding: 5px;
                background: rgba(194, 234, 234, 100);
            }
            QPushButton:hover {
                background: rgba(152, 227, 227, 100);
            }
            QPushButton:pressed {
                background: rgba(116, 200, 200, 100);
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
                if path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    try:
                        with open(path, 'rb') as f:
                            f.read(1)
                        self.start_w.handle_file_load(path)
                        event.acceptProposedAction()
                        self.overlay.hide()
                    except Exception as e:
                        event.ignore()
                        self.drop_label.setText(f"Ошибка: {str(e)}")
                        self.drop_label.setStyleSheet("font-size: 18px; color: #D32F2F; padding: 20px; border: 2px solid #D32F2F; background-color: #FFEBEE;")
                else:
                    event.ignore()
                    self.drop_label.setText("Ошибка: выберите изображение (*.png, *.jpg, *.jpeg)")
                    self.drop_label.setStyleSheet("font-size: 18px; color: #D32F2F; padding: 20px; border: 2px solid #D32F2F; background-color: #FFEBEE;")
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