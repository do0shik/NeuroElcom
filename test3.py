from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QScrollArea, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontDatabase, QFont
import sys
import json
import os

class ComboBoxWindow(QMainWindow):
    def __init__(self, data_file):
        super().__init__()
        self.setWindowTitle("Выпадающие списки")
        self.setGeometry(0, 0, 1920, 1020)

        # Загрузка шрифта Manrope
        font_db = QFontDatabase()
        font_id = font_db.addApplicationFont("C:/Users/a.avdashkova/PycharmProjects/AI_application/font/Manrope-VariableFont_wght.ttf")
        if font_id < 0:
            print("Ошибка загрузки шрифта Manrope")
        else:
            manrope_font = QFont("Manrope")
            QApplication.setFont(manrope_font)  # Устанавливаем шрифт по умолчанию для всего приложения

        # Основной виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Контейнер с рамкой
        left_container = QWidget(central_widget)
        left_container.setGeometry(50, 120, 900, 850)  # x=50, y=120, ширина=900, высота=850
        left_container.setStyleSheet("""
            background-color: rgba(255, 255, 255, 50);
            border-radius: 20px;
            border: 4px solid #3C7D94;  
        """)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(5, 5, 5, 5)  # Отступы для рамки
        left_layout.setSpacing(0)

        # Создаем QScrollArea внутри left_container
        scroll_area = QScrollArea(left_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 20px;
                margin: 15px 0 15px 0;  
            }
            QScrollBar::handle:vertical {
                background: #C2C2C2;  
                border-radius: 5px; 
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;     
                height: 15px;
                subcontrol-origin: margin;
            }
            QScrollBar::add-line:vertical {
                subcontrol-position: bottom;
            }
            QScrollBar::sub-line:vertical {
                subcontrol-position: top;
            }
            QScrollBar::up-arrow:vertical {
                image: url(icons/drop_up.png); 
                width: 10px;
                height: 10px;
            }
            QScrollBar::down-arrow:vertical {
                image: url(icons/drop_down.png);  
                width: 10px;
                height: 10px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: #F4F4F4;  
            }
        """)
        left_layout.addWidget(scroll_area)

        # Контейнер для содержимого QScrollArea
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent; border: none;")
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setAlignment(Qt.AlignTop)
        content_layout.setContentsMargins(10, 10, 10, 10)  # Отступы внутри прокручиваемого содержимого
        content_layout.setSpacing(10)

        # Загрузка данных из файла
        data = self.load_data_from_file(data_file)
        if not data:
            error_label = QLabel("Ошибка: данные не загружены или пусты")
            error_label.setStyleSheet("font-size: 20px; color: #D32F2F; border: none;")
            content_layout.addWidget(error_label, alignment=Qt.AlignCenter)
            scroll_area.setWidget(scroll_content)
            return

        # Группировка данных по категориям
        category_groups = {}
        for group in data:
            if not group or not isinstance(group, list):
                continue

            first_item = group[0] if group and isinstance(group[0], dict) else {}
            category = "Автоматические выключатели" if first_item.get('id', '').startswith(('14.01', '14.02')) else \
                      "Трансформаторы" if first_item.get('id', '').startswith(('ITB', 'ITT')) else \
                      "Счетчики 'Меркурий'" if first_item.get('id', '').startswith('13.03') or first_item.get('id') == '1' else "Неизвестно"

            sorted_group = sorted(group, key=lambda x: x.get('id', '') if isinstance(x, dict) else '')
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(sorted_group)

        # Обработка каждой категории
        for category, groups in category_groups.items():
            # Контейнер для категории
            category_container = QWidget()
            category_container.setStyleSheet("background-color: transparent; border: none;")
            category_layout = QVBoxLayout(category_container)
            category_layout.setSpacing(0)
            category_layout.setContentsMargins(10, 0, 0, 0)  # Отступ слева

            # Заголовок категории
            header = QLabel(category)
            header.setStyleSheet("font-size: 20px; font-weight: bold; color: #2A7179; margin-bottom: 5px; border: none;")
            header.setAlignment(Qt.AlignCenter)
            category_layout.addWidget(header)

            # Контейнер для заголовков столбцов
            headers_container = QWidget()
            headers_container.setStyleSheet("background-color: transparent; border: none;")
            headers_layout = QHBoxLayout(headers_container)
            headers_layout.setSpacing(20)  # Расстояние между заголовками 20px
            headers_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))  # Отступ слева 10px

            # Определяем ширины столбцов
            column_widths = [155, 500, 115]  # ID, Наименование, Цена

            # Заголовки столбцов
            for header_text, width in zip(["Артикул", "Наименование", "Цена"], column_widths):
                header_label = QLabel(header_text)
                header_label.setStyleSheet("font-size: 14px; color: #B1B1B1; border: none;")
                header_label.setFixedWidth(width)
                header_label.setAlignment(Qt.AlignCenter)
                headers_layout.addWidget(header_label)
            headers_layout.addStretch()

            category_layout.addWidget(headers_container)

            # Добавляем выпадающие списки для каждой группы
            for group in groups:
                combos_container = QWidget()
                combos_container.setStyleSheet("background-color: transparent; border: none;")
                combos_layout = QHBoxLayout(combos_container)
                combos_layout.setSpacing(20)  # Расстояние между списками 20px

                combo_id = QComboBox()
                combo_name = QComboBox()
                combo_price = QComboBox()

                for item in group:
                    if isinstance(item, dict):
                        combo_id.addItem(item.get('id', 'N/A'), item)
                        combo_name.addItem(item.get('name', 'N/A'), item)
                        combo_price.addItem(f"{item.get('price', 'N/A')} руб.", item)

                # Устанавливаем фиксированные ширины для QComboBox
                combo_id.setFixedWidth(column_widths[0])  # ID: 145px
                combo_name.setFixedWidth(column_widths[1])  # Наименование: 400px
                combo_price.setFixedWidth(column_widths[2])  # Цена: 110px

                # Стили для QComboBox
                for combo in [combo_id, combo_name, combo_price]:
                    combo.setStyleSheet("""
                                    QComboBox {
                            border: 1px solid #A4A4A4;
                            border-radius: 10px;
                            padding: 5px;
                            background-color: #F2F2F2;
                            font-size: 14px;
                            color: #000000;
                            font-weight: 300;
                        }
                        QComboBox::drop-down {
                            subcontrol-origin: padding;
                            subcontrol-position: right;
                            width: 20px;
                            border-left: none;
                            border-top-right-radius: 5px;
                            border-bottom-right-radius: 10px;
                        }
                        QComboBox::down-arrow {
                            image: url(icons/drop_down.png);
                            width: 10px;
                            height: 10px;
                        }
                        QComboBox QAbstractItemView {
                            border: none;
                            background-color: #ffffff;
                            selection-background-color: #6CB9C4;
                        }
                    """)

                combos_layout.addWidget(combo_id)
                combos_layout.addWidget(combo_name)
                combos_layout.addWidget(combo_price)
                combos_layout.addStretch()

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

                sync_func = create_sync_func(combo_id, combo_name, combo_price)
                combo_id.currentIndexChanged.connect(sync_func)
                combo_name.currentIndexChanged.connect(sync_func)
                combo_price.currentIndexChanged.connect(sync_func)

                category_layout.addWidget(combos_container)

            content_layout.addWidget(category_container)

        scroll_area.setWidget(scroll_content)

    def load_data_from_file(self, file_path=None):
        try:
            if file_path and file_path.lower().endswith('.json'):
                print(f"Попытка загрузки файла: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"Содержимое файла {file_path}: {content[:200]}...")  # Отладка
                    data = json.loads(content)
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

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        window = ComboBoxWindow("C:/Users/a.avdashkova/PycharmProjects/AI_application/example/test666.json")
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Ошибка при запуске приложения: {e}")