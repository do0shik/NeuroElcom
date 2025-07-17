import sys
import os
import json
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QComboBox, QLabel, QPushButton, QFileDialog,
    QScrollArea, QScrollBar, QDialog, QMessageBox,
    QLineEdit, QDialogButtonBox, QGroupBox, QGridLayout, QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QIcon, QPixmap, QFontDatabase, QFont, QColor, QPainter, QBrush
from PyQt5.QtCore import Qt, QSize, QTimer, QRect, QEasingCurve, QPropertyAnimation

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import tempfile
from APIClient import APIClient
from datetime import datetime
# Global for current image path
CURRENT_IMG_PATH = ""

class CustomScrollBar(QScrollBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(12)  # Устанавливаем фиксированную ширину скроллбара
        self.setMinimum(0)      # Минимальное значение скроллбара
        self.setMaximum(100)    # Максимальное значение скроллбара
        # Цвета элементов
        self.handle_color = QColor(194, 194, 194)  # Цвет ползунка (серый)
        self.track_color = QColor(244, 244, 244)   # Цвет фонового трека (светло-серый)
        # Отступы
        self.offset_vertical = 4    # Вертикальный отступ (уменьшен для более тонкого вида)
        self.offset_horizontal = 2  # Горизонтальный отступ (уменьшен)
        # Параметры закругления и пропорций
        self.corner_radius = 3     # Радиус закругления углов (уменьшен для тонкого скроллбара)
        self.track_length_ratio = 1  # Длина трека относительно высоты скроллбара (100%)
        self.handle_length_ratio = 0.6  # Длина ползунка относительно высоты трека (60%)
        # Стили CSS
        self.setStyleSheet("QScrollBar { border: none; }")  # Убираем стандартную рамку

    def set_scrollbar_length(self, length):
        """Устанавливает фиксированную высоту скроллбара"""
        self.setFixedHeight(length)

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # Заполняем фон белым цветом
            painter.fillRect(self.rect(), QBrush(QColor(255, 255, 255, 255)))

            # Рассчитываем параметры трека
            track_height = int(self.height() * self.track_length_ratio)
            if track_height <= 0:
                track_height = 10  # Минимальная высота трека

            track_y = (self.height() - track_height) // 2

            # Ширина трека равна ширине скроллбара минус небольшой отступ
            track_width = self.width() - 2 * self.offset_horizontal
            if track_width <= 0:
                track_width = self.width()  # Защита от отрицательных значений

            # Позиционируем трек по центру
            track_x = self.offset_horizontal
            track_rect = QRect(
                track_x,
                track_y + self.offset_vertical,
                track_width,
                track_height - 2 * self.offset_vertical
            )

            # Рисуем трек с закругленными углами
            painter.setBrush(QBrush(self.track_color))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(track_rect, self.corner_radius, self.corner_radius)

            # Рассчитываем параметры ползунка
            handle_height = int(track_height * self.handle_length_ratio)
            if handle_height <= 0:
                handle_height = 10  # Минимальная высота ползунка

            max_handle_y = track_height - handle_height - 2 * self.offset_vertical
            if max_handle_y < 0:
                max_handle_y = 0  # Защита от отрицательных значений

            # Рассчитываем позицию ползунка
            if self.maximum() > self.minimum():
                ratio = max_handle_y / (self.maximum() - self.minimum())
            else:
                ratio = 0

            if ratio != 0 and (self.value() - self.minimum()) >= 0:
                handle_y = int((self.value() - self.minimum()) * ratio + self.offset_vertical)
            else:
                handle_y = self.offset_vertical

            # Ширина ползунка равна ширине трека
            handle_width = track_width

            # Позиционируем ползунок
            handle_x = track_x
            handle_rect = QRect(
                handle_x,
                handle_y + track_y,
                handle_width,
                handle_height
            )

            # Проверяем, что высота ползунка не превышает высоту трека
            if handle_rect.height() > track_rect.height():
                handle_rect.setHeight(track_rect.height())

            # Рисуем ползунок с закругленными углами
            painter.setBrush(QBrush(self.handle_color))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(handle_rect, self.corner_radius, self.corner_radius)

        except Exception as e:
            print(f"Ошибка при отрисовке скроллбара: {e}")
            # В случае ошибки рисуем простой прямоугольник
            painter = QPainter(self)
            painter.fillRect(self.rect(), QBrush(QColor(255, 255, 255, 255)))
            painter.setBrush(QBrush(self.track_color))
            painter.drawRect(0, 0, self.width(), self.height())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Window settings
        self.header_font_family = header_font_family
        self.setWindowIcon(QIcon('icons/logo_mini.png'))
        self.setWindowTitle("Neuro Elcom")
        self.setGeometry(0, 0, 1920, 1020)
        self.showMaximized()
        # Background
        self.setStyleSheet(
            "QMainWindow { "
                "background-image: url(icons/Computer. Tab1_beta.png); "
                "background-position: center; "
                "}"
        )
        # Stacked widget
        self.stacked = QStackedWidget(self)
        self.setCentralWidget(self.stacked)

        # Page1: Upload
        self.page_upload = QWidget()
        layout1 = QVBoxLayout(self.page_upload)
        layout1.setAlignment(Qt.AlignCenter)
        self.drop_area = DropArea(self)
        layout1.addWidget(self.drop_area)
        self.stacked.addWidget(self.page_upload)

        # Logo
        self.logo_label = QLabel(self)
        icon_path = 'icons/logo_max.png'
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                self.logo_label.setPixmap(pixmap)
                self.logo_label.resize(pixmap.size())
        self.logo_label.move(20, 20)
        self.logo_label.show()

        self.page_result = QWidget()
        self.stacked.addWidget(self.page_result)
        self.category_data = {}
        self.load_selected_items()

    def save_selected_items(self):
        """Сохраняет выбранные элементы в файл"""
        try:
            categories_data = {}

            # Получаем данные из всех категорий
            for category_name in self.category_data.keys():
                # Здесь нужно реализовать получение данных для каждой категории
                # Это временное решение, нужно заменить на реальную логику
                categories_data[category_name] = []

            # Сохраняем в файл JSON
            with open("selected_items.json", "w", encoding="utf-8") as f:
                json.dump(categories_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка при сохранении данных: {e}")

    def load_selected_items(self):
        """Загружает сохраненные элементы из файла"""
        try:
            with open("selected_items.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            return {}

    def closeEvent(self, event):
        """Обработчик события закрытия окна"""
        self.save_selected_items()
        event.accept()

    def _open_pdf(self, pdf_path):
        try:
            if sys.platform == 'win32':
                os.startfile(pdf_path)
            elif sys.platform == 'darwin':
                subprocess.call(['open', pdf_path])
            else:
                subprocess.call(['xdg-open', pdf_path])
        except Exception as e:
            print(f"Не удалось открыть PDF: {e}")
            self._show_error_message(f"PDF создан: {pdf_path}")

    def _show_error_message(self, message):
        msg = QLabel(message, self.page_result)
        msg.setStyleSheet("color: green; font-size: 16px; background-color: white; padding: 10px; border-radius: 5px;")
        msg.move(975, 100)
        msg.show()
        QTimer.singleShot(5000, msg.deleteLater)

    def create_pdf(self):
        print("Запуск создания PDF...")
        try:
            # Регистрация шрифта Manrope
            pdfmetrics.registerFont(TTFont('Manrope', '/font/Manrope-VariableFont_wght.ttf'))
            pdfmetrics.registerFont(TTFont('Manrope-Bold', '/font/Manrope-SemiBold.ttf'))

            # # Резервный шрифт на случай проблем с Manrope
            # pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
            # pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))

            pdf_path = os.path.join(tempfile.gettempdir(), "result.pdf")
            doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)

            elements = []
            styles = getSampleStyleSheet()

            # Устанавливаем шрифт Manrope с резервным переключением на DejaVuSans
            try:
                styles['Normal'].fontName = 'Manrope'
                styles['Heading2'].fontName = 'Manrope-Bold'
            except:
                styles['Normal'].fontName = 'DejaVuSans'
                styles['Heading2'].fontName = 'DejaVuSans-Bold'
                print("Переключение на шрифт DejaVuSans из-за ошибки с Manrope")

            self._add_logo_to_pdf(elements, styles)
            categories_data = self._get_selected_data_from_ui()
            print("Собранные данные:", categories_data)

            has_data = any(len(items) > 0 for items in categories_data.values()) if categories_data else False
            if not has_data:
                elements.append(Spacer(1, 0.5 * inch))
                elements.append(Paragraph("Нет данных для отображения", styles['Normal']))

            self._add_tables_to_pdf(elements, styles, categories_data)

            doc.build(elements)
            print(f"PDF создан: {pdf_path}")
            self._open_pdf(pdf_path)
        except Exception as e:
            print(f"Ошибка при создании PDF: {e}")
            self._show_error_message(f"Ошибка: {str(e)}")

    def _add_logo_to_pdf(self, elements, styles):
        logo_path = 'icons/logo_max.png'
        if os.path.exists(logo_path):
            try:
                logo_img = Image(logo_path)
                logo_img.drawWidth = 150
                logo_img.drawHeight = 35
                logo_img.hAlign = 'LEFT'
                elements.append(logo_img)
                elements.append(Spacer(1, 0.3 * inch))
            except Exception as e:
                print(f"Не удалось загрузить логотип: {e}")
                elements.append(Spacer(1, 0.6 * inch))
        else:
            print(f"Логотип не найден по пути: {logo_path}")
            elements.append(Spacer(1, 0.6 * inch))

    def _get_selected_data_from_ui(self):
        categories_data = {
            'Автоматические выключатели': [],
            'Трансформаторы': [],
            "Счетчики 'Меркурий'": []
        }

        print("Начинаем сбор данных из интерфейса...")

        # Проходим по всем дочерним элементам page_result
        for child in self.page_result.children():
            if isinstance(child, QWidget) and child.geometry().x() == 50 and child.geometry().y() == 120:
                scroll_area = None
                for widget in child.children():
                    if isinstance(widget, QScrollArea):
                        scroll_area = widget
                        print("Найден QScrollArea")
                        break

                if scroll_area:
                    content_widget = scroll_area.widget()
                    if content_widget:
                        print("Найден content_widget")
                        current_category = None

                        # Проходим по всем дочерним элементам content_widget
                        for child_widget in content_widget.children():
                            # Ищем блоки категорий
                            if isinstance(child_widget, QWidget) and hasattr(child_widget, 'objectName'):
                                category_name = None
                                if child_widget.objectName().endswith('_block'):
                                    # Это блок категории
                                    for header in child_widget.children():
                                        if isinstance(header, QLabel):
                                            if header.text() in categories_data:
                                                current_category = header.text()
                                                print(f"Найдена категория: {current_category}")
                                                break

                                    # Теперь находим все строки с данными внутри этого блока
                                    if current_category:
                                        # Ищем все QWidget, которые не являются заголовками или кнопками "+"
                                        for row_widget in child_widget.children():
                                            if isinstance(row_widget, QWidget) and row_widget != child_widget:
                                                # Пропускаем заголовки и кнопки "+"
                                                is_row = False
                                                has_comboboxes = False

                                                # Проверяем, есть ли в этом виджете комбобоксы
                                                combos = []
                                                for w in row_widget.children():
                                                    if isinstance(w, QComboBox):
                                                        combos.append(w)

                                                if len(combos) >= 3:
                                                    row_data = []
                                                    for i, combo in enumerate(combos):
                                                        if combo.currentIndex() >= 0:
                                                            data = combo.currentData()
                                                            if isinstance(data, dict):
                                                                if i == 0:
                                                                    row_data.append(data.get('id', ''))
                                                                elif i == 1:
                                                                    row_data.append(data.get('name', ''))
                                                                elif i == 2:
                                                                    row_data.append(data.get('price', ''))

                                                    if len(row_data) == 3:
                                                        item_data = {
                                                            'id': row_data[0],
                                                            'name': row_data[1],
                                                            'price': row_data[2]
                                                        }
                                                        categories_data[current_category].append(item_data)
                                                        print(f"Добавлен элемент: {item_data}")

        # Удаляем пустые категории
        for category in list(categories_data.keys()):
            if not categories_data[category]:
                print(f"Категория {category} пустая, удаляем")
                del categories_data[category]
            else:
                print(f"В категории {category} найдено {len(categories_data[category])} элементов")

        print("Сбор данных завершен")
        return categories_data

    def _add_tables_to_pdf(self, elements, styles, categories_data):
        if not categories_data or not isinstance(categories_data, dict):
            elements.append(Paragraph("Нет данных для отображения", styles['Normal']))
            return

        # Создаем общий список данных для таблицы
        table_data = []

        # Переменная для хранения общей суммы
        total_price = 0

        # Настраиваем стиль для названий категорий
        category_style = styles['Heading2'].clone('CategoryStyle')
        category_style.fontSize = 12  # Увеличиваем размер шрифта
        category_style.alignment = 1  # 1 = центр (0=left, 1=center, 2=right)
        category_style.spaceAfter = 6  # Отступ после категории

        # Проходим по каждой категории
        for cat_name, items in categories_data.items():
            if not items:
                continue

            # Добавляем название категории
            category_para = Paragraph(cat_name, category_style)
            table_data.append([category_para, "", ""])  # Три колонки, первая содержит текст, остальные пустые

            # Добавляем заголовки таблицы
            header_style = styles['Normal'].clone('HeaderStyle')
            header_style.alignment = 1  # Центрирование заголовков
            header_style.fontName = styles['Heading2'].fontName  # Жирный шрифт

            table_data.append([
                Paragraph("Артикул", header_style),
                Paragraph("Наименование", header_style),
                Paragraph("Цена", header_style)
            ])

            # Добавляем данные для каждого элемента в категории
            category_total = 0
            for item in items:
                price = float(item['price']) if item['price'] else 0
                category_total += price
                total_price += price

                table_data.append([
                    Paragraph(str(item['id']), styles['Normal']),
                    Paragraph(str(item['name']), styles['Normal']),
                    Paragraph(f"{price:.2f} руб.", styles['Normal'])
                ])

        # Создаем таблицу только если есть данные
        if table_data:
            # Определяем ширину колонок
            col_widths = [120, 300, 100]

            # Создаем таблицу
            table = Table(table_data, colWidths=col_widths)

            # Настраиваем стиль таблицы
            table_style = TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # По умолчанию выравнивание по левому краю
                ('FONTNAME', (0, 0), (-1, -1), styles['Normal'].fontName),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('WORDWRAP', (0, 0), (-1, -1), True),

                # Стиль для названий категорий
                ('SPAN', (0, 0), (-1, 0)),  # Первый заголовок - объединяем ячейки
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), styles['Heading2'].fontName),
                ('FONTSIZE', (0, 0), (-1, 0), 14),  # Более крупный шрифт
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),  # Отступ снизу
            ])

            # Добавляем стили для всех строк категорий
            row_index = 0
            for cat_name, items in categories_data.items():
                if not items:
                    continue

                # Стиль для названия категории
                table_style.add('SPAN', (0, row_index), (-1, row_index))  # Объединяем ячейки
                table_style.add('ALIGN', (0, row_index), (-1, row_index), 'CENTER')  # Центрирование
                table_style.add('BACKGROUND', (0, row_index), (-1, row_index), colors.lightgrey)
                table_style.add('FONTSIZE', (0, row_index), (-1, row_index), 14)  # Крупный шрифт
                table_style.add('FONTNAME', (0, row_index), (-1, row_index), styles['Heading2'].fontName)
                table_style.add('VALIGN', (0, row_index), (-1, row_index), 'MIDDLE')
                table_style.add('BOTTOMPADDING', (0, row_index), (-1, row_index), 6)  # Отступ снизу

                row_index += 1  # Переходим к строке заголовков

                # Стиль для заголовков таблицы (центрирование)
                table_style.add('BACKGROUND', (0, row_index), (-1, row_index), colors.lightgrey)
                table_style.add('ALIGN', (0, row_index), (-1, row_index), 'CENTER')  # Центрирование заголовков
                table_style.add('FONTNAME', (0, row_index), (-1, row_index), styles['Heading2'].fontName)
                table_style.add('FONTSIZE', (0, row_index), (-1, row_index), 10)
                row_index += 1

                # Пропускаем строки с данными (количество строк = количество элементов)
                row_index += len(items)

            table.setStyle(table_style)
            elements.append(table)

        # Добавляем итоговую строку как отдельный параграф (если есть данные)
        if total_price > 0:
            elements.append(Spacer(1, 0.2 * inch))  # Отступ перед итогом

            # Создаем специальный стиль для итога
            total_style = styles['Normal'].clone('TotalStyle')
            total_style.fontSize = 14  # Более крупный шрифт
            total_style.fontName = styles['Heading2'].fontName  # Жирный шрифт
            total_style.alignment = 2  # По правому краю

            total_text = f"ИТОГ: {total_price:.2f} руб."
            elements.append(Paragraph(total_text, total_style))

            elements.append(Spacer(1, 0.3 * inch))  # Отступ после итога

    def print_selected_data(self):
        """Выводит собранные данные в консоль для отладки"""
        categories_data = self._get_selected_data_from_ui()
        for cat_name, items in categories_data.items():
            print(f"Категория: {cat_name}")
            for item in items:
                print(f"  Артикул: {item.get('id', '')}")
                print(f"  Наименование: {item.get('name', '')}")
                print(f"  Цена: {item.get('price', '')}")

    def save_detection_image(self, image_bytes):
        """
        save_detection_image 
            Функция для создания временного файла из 
            полученного изображения
        Parameters
        image_bytes : base64
            Полученное изображение
        Returns 
        temp_image_path
            Путь до созданного временнного файла
        """
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_image_path = os.path.join(temp_dir, f"detection_result_{timestamp}.jpg")
    
        with open(temp_image_path, 'wb') as f:
            f.write(image_bytes)
        return temp_image_path
    
    def select_file(self):
        # Метод для выбора файла
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.handle_file_load(path)

    def handle_file_load(self, path):
        """
        handle_file_load 
            Функция для работы с API
            и передачи результатов
            (немного поменяла)
        Parameters
        path : str
             Принимается путь выбранного файла,
             Затем изображение удаленно передается на обработку.
             В результате получается измененное изображение
             И данные, полученные в результате обработки
        """
        global CURRENT_IMG_PATH
        global data
        api = APIClient()
        image_bytes, detection_results = api.detect_image(path)
        temp_image_path = self.save_detection_image(image_bytes)
        CURRENT_IMG_PATH = temp_image_path
        data = detection_results
        self.show_success(temp_image_path)

    def show_success(self, path):
        w = QWidget(self)
        w.setWindowFlags(Qt.FramelessWindowHint)
        w.setAttribute(Qt.WA_TranslucentBackground)
        w.setFixedSize(300, 100)
        inner = QWidget(w)
        inner.setStyleSheet("background-color: rgba(235,235,235,200); border-radius:10px;")
        v = QVBoxLayout(inner)
        lbl = QLabel(f"Файл загружен:\n{path}")
        lbl.setWordWrap(True)
        v.addWidget(lbl, alignment=Qt.AlignCenter)
        wl = QVBoxLayout(w)
        wl.addWidget(inner)
        c = self.rect().center()
        w.move(c.x()-150, c.y()+180)
        w.show()
        anim_in = QPropertyAnimation(w, b"windowOpacity")
        anim_in.setDuration(500)
        anim_in.setStartValue(0)
        anim_in.setEndValue(1)
        anim_in.start()
        anim_out = QPropertyAnimation(w, b"windowOpacity")
        anim_out.setDuration(500)
        anim_out.setStartValue(1)
        anim_out.setEndValue(0)
        t = QTimer(self)
        t.setInterval(1000)
        t.timeout.connect(lambda: self.finish_success(w, anim_out, t))
        t.start()

    def finish_success(self, w, anim_out, timer):
        anim_out.start()
        timer.stop()
        anim_out.finished.connect(lambda: self.build_result_page(w))

    def clear_result_page(self):
        """Очищает страницу результатов от всех виджетов"""
        # Удаляем все дочерние виджеты из page_result
        for child in self.page_result.children():
            child.deleteLater()

    def build_result_page(self, w):
        w.deleteLater()
        self.clear_result_page()
        self.page_result.setStyleSheet("background: transparent;")
        print("Создаем страницу результатов...")
        print(f"Текущий путь к изображению: {CURRENT_IMG_PATH}")
        print(f"Изображение существует: {os.path.exists(CURRENT_IMG_PATH) if CURRENT_IMG_PATH else False}")

        # Создаем шрифт для кнопок
        btn_font = QFont()
        if self.header_font_family:
            btn_font.setFamily(self.header_font_family)
            btn_font.setPointSize(18)
        else:
            btn_font.setBold(True)
            btn_font.setPointSize(18)

        # Кнопка "Назад" (теперь также не входит в левый контейнер)
        self.back_btn = QPushButton("← Назад", self.page_result)
        self.back_btn.setFont(btn_font)
        self.back_btn.setFixedSize(240, 65)
        self.back_btn.setStyleSheet(
            "QPushButton { font-weight: bold; color: #006172; background-color: white; border-radius: 20px; border: 4px solid #006172; }"
            "QPushButton:hover { background-color: #61B2B8; color: white; }"
            "QPushButton:pressed { background-color: #006172; color: white; }"
        )
        self.back_btn.clicked.connect(self.return_to_upload)

        # Кнопка "Создать PDF"
        pdf_btn = QPushButton("Создать PDF", self.page_result)
        pdf_btn.setFont(btn_font)
        pdf_btn.setFixedSize(240, 65)
        pdf_btn.setStyleSheet(
            "QPushButton { font-size: 18px; font-weight: bold; color: #006172; background-color: white; border-radius: 20px; border: 4px solid #006172; }"
            "QPushButton:hover { background-color: #61B2B8; color: white; }"
            "QPushButton:pressed { background-color: #006172; color: white; }"
        )
        pdf_btn.clicked.connect(self.create_pdf)

        # Левая панель с таблицей
        left = QWidget(self.page_result)
        left.setGeometry(50, 120, 950, 800)
        left.setStyleSheet(
            "background-color: rgba(255,255,255,50); "
            "border-radius: 20px; "
            "border: 4px solid #006172; "
        )

        # Создаем область прокрутки
        scroll = QScrollArea(left)
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setGeometry(10, 10, 920, 770)
        scroll.setStyleSheet("""
                QScrollArea {
                    background-color: transparent;
                    border: none;
                }
                QScrollArea viewport {
                    background-color: transparent;
                    border: none;
                }
            """)

        # Создаем контейнер для содержимого
        content = QWidget()
        content.setStyleSheet("background-color: transparent; border: none;")
        cont_v = QVBoxLayout(content)
        cont_v.setAlignment(Qt.AlignTop)
        cont_v.setContentsMargins(5, 5, 5, 5)
        cont_v.setSpacing(5)

        # Загрузка данных и создание таблицы
        switches, transformers, meters = [], [], []
        loaded_data = self.load_data(data)
        if data:
            for group in loaded_data:
                if not isinstance(group, list) or not group: continue
                item = group[0]
                cid = item.get('id', '')
                if cid.startswith(('14.01', '14.02')):
                    switches.append(group)
                elif cid.startswith(('ITB', 'ITT', '15')):
                    transformers.append(group)
                elif cid.startswith('13.03') or cid == '1':
                    meters.append(group)

        category_font = QFont()
        if self.header_font_family:
            category_font.setFamily(self.header_font_family)
            category_font.setPointSize(18)
        else:
            category_font.setBold(True)
            category_font.setPointSize(18)

        categories = [
            ('Автоматические выключатели', switches),
            ('Трансформаторы', transformers),
            ("Счетчики 'Меркурий'", meters)
        ]

        # Функция для создания новой строки в нужной категории
        def create_new_row(category_name, groups, cont_v, content, is_manual=True):
            combo_box_widths = [155, 500, 115]
            row_spacing = 10
            row_margins = (1, 10, 10, 10)
            combo_box_style = test3_styles()

            button_x_pos = None
            if is_manual:
                button_x_pos = sum(combo_box_widths) + row_spacing * (len(combo_box_widths) - 1) + row_margins[0] + \
                               row_margins[2] + 80

            current_category_index = None
            for i in range(cont_v.count()):
                widget = cont_v.itemAt(i).widget()
                if isinstance(widget, QLabel) and widget.text() == category_name:
                    current_category_index = i
                    break

            if current_category_index is None:
                row = _create_row(content, combo_box_widths, row_spacing, row_margins,
                                  combo_box_style, groups, is_manual, button_x_pos=button_x_pos)
                cont_v.addWidget(row)
                return row

            categories_in_layout = [c[0] for c in categories]
            current_cat_index = categories_in_layout.index(
                category_name) if category_name in categories_in_layout else -1
            next_category_index = None
            if current_cat_index != -1 and current_cat_index < len(categories_in_layout) - 1:
                next_category_name = categories_in_layout[current_cat_index + 1]
                for i in range(current_category_index, cont_v.count()):
                    widget = cont_v.itemAt(i).widget()
                    if isinstance(widget, QLabel) and widget.text() == next_category_name:
                        next_category_index = i
                        break

            last_row_index = current_category_index
            for i in range(current_category_index + 1, cont_v.count()):
                if next_category_index is not None and i >= next_category_index:
                    break
                widget = cont_v.itemAt(i).widget()
                if isinstance(widget, QWidget) and hasattr(widget, 'layout') and \
                        isinstance(widget.layout(), QHBoxLayout):
                    has_comboboxes = False
                    for child in widget.children():
                        if isinstance(child, QComboBox):
                            has_comboboxes = True
                            break
                    if has_comboboxes:
                        last_row_index = i

            insert_pos = last_row_index + 1
            if next_category_index is not None and insert_pos >= next_category_index:
                insert_pos = next_category_index
            elif insert_pos is None:
                insert_pos = cont_v.count()

            row = _create_row(content, combo_box_widths, row_spacing, row_margins,
                              combo_box_style, groups, is_manual, button_x_pos=button_x_pos)
            cont_v.insertWidget(insert_pos, row)
            return row

        def _create_row(content, combo_widths, spacing, margins, combo_style, groups, is_manual, button_x_pos=1000):
            row = QWidget(content)
            row_layout = QHBoxLayout(row)
            row_layout.setSpacing(spacing)
            row_layout.setContentsMargins(*margins)
            combos = []

            # Собираем все элементы из всех групп
            all_items = []
            if groups:
                for grp in groups:
                    if isinstance(grp, list):
                        for item in grp:
                            if item not in all_items:
                                all_items.append(item)

            # Сортируем элементы по ID
            #all_items_sorted = sorted(all_items, key=lambda x: x.get('name', '')) if all_items else []

            # Создаем комбобоксы
            for key, w in zip(['id', 'name', 'price'], combo_widths):
                cb = QComboBox(row)
                cb.addItem("", None)  # Пустой элемент
                if all_items:
                    for itm in all_items:
                        val = itm.get(key, 'N/A')
                        txt = f"{val}" + (" руб." if key == 'price' else "")
                        cb.addItem(txt, itm)
                cb.setFixedWidth(w)
                cb.setStyleSheet(combo_style)
                combos.append(cb)
                row_layout.addWidget(cb)

            # Добавляем кнопку удаления только для ручных строк
            if is_manual:
                remove_btn = QPushButton("×", row)
                remove_btn.setFixedSize(30, 30)
                remove_btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #2A7179;
                        font-size: 24px;
                        font-weight: bold;
                    }
                """)
                remove_btn.clicked.connect(lambda: row.deleteLater())
                if button_x_pos is not None:
                    row_height = sum([cb.sizeHint().height() for cb in combos])
                    button_y_pos = (row_height - remove_btn.height()) // 2
                    remove_btn.move(button_x_pos, button_y_pos)
                else:
                    row_layout.addStretch()
                    row_layout.addWidget(remove_btn)

            # Настройка синхронизации комбобоксов
            if len(combos) == 3:
                a, b, c = combos

                def make_sync(a, b, c):
                    def sync():
                        src = QApplication.focusWidget()
                        data = src.currentData()
                        for cb in (a, b, c):
                            if cb is not src:
                                idx = next((i for i in range(cb.count()) if cb.itemData(i) == data), 0)
                                cb.blockSignals(True)
                                cb.setCurrentIndex(idx)
                                cb.blockSignals(False)

                    return sync

                fn = make_sync(a, b, c)
                a.currentIndexChanged.connect(fn)
                b.currentIndexChanged.connect(fn)
                c.currentIndexChanged.connect(fn)

            return row

        # Обработка категорий
        for cat_name, groups in categories:
            if not groups:
                continue

            # Заголовок категории
            header = QLabel(cat_name, content)
            header.setStyleSheet("color:#2A7179;")
            header.setAlignment(Qt.AlignCenter)
            header.setFont(category_font)
            cont_v.addWidget(header)

            # Создаем контейнер для кнопки с горизонтальным layout
            button_row = QWidget(content)
            button_row_layout = QHBoxLayout(button_row)
            button_row_layout.setContentsMargins(30, 0, 0, 0)  # Убираем все отступы
            button_row_layout.setSpacing(0)  # Убираем расстояние между элементами

            # Создаем кнопку "+"
            add_button = QPushButton("+", button_row)
            add_button.setFont(btn_font)
            add_button.setFixedWidth(42)
            add_button.setFixedHeight(42)
            add_button.setStyleSheet("""
                            QPushButton {
                                background-color: #2A7179;
                                color: white;
                                border-radius: 10px;
                                border: 2px solid #2A7179;
                                font-size: 24px;
                                font-weight: bold;
                            }
                        """)

            # Устанавливаем выравнивание кнопки по левому краю
            add_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # Фиксированный размер
            button_row_layout.setAlignment(Qt.AlignLeft)  # Выравнивание всего layout по левому краю

            # Добавляем кнопку в layout
            button_row_layout.addWidget(add_button)

            # Добавляем растягивающийся элемент, чтобы кнопка оставалась слева
            button_row_layout.addStretch()

            # Добавляем контейнер в основной вертикальный layout
            cont_v.addWidget(button_row)

            # Связываем кнопку с функцией создания строки
            add_button.clicked.connect(
                lambda _, cn=cat_name, gs=groups, cv=cont_v, c=content:
                create_new_row(cn, gs, cv, c)
            )

            # Заголовки колонок
            colhdr = QWidget(content)
            hdr_layout = QHBoxLayout(colhdr)
            widths = [155, 500, 115]
            font = QFont()
            font.setPointSize(12)

            # Добавление заголовков колонок
            for text, w in zip(["Артикул", "Наименование", "Цена", ""], widths + [30]):
                lh = QLabel(text, colhdr)
                lh.setFixedWidth(w)
                lh.setAlignment(Qt.AlignCenter)
                lh.setFont(category_font)
                lh.setStyleSheet("color: #B1B1B1; font-size: 16px")
                hdr_layout.addWidget(lh)

            cont_v.addWidget(colhdr)


            # Существующие группы
            for grp in groups:
                #grp_sorted = sorted(grp, key=lambda x: x.get('name', ''))
                row = QWidget(content)
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(1, 10, 10, 10)  # Лево, Верх, Право, Низ
                row_layout.setSpacing(5)  # Расстояние между элементами
                combos = []

                for key, w in zip(['id', 'name', 'price'], widths):
                    cb = QComboBox(row)
                    for itm in grp:
                        val = itm.get(key, 'N/A')
                        txt = f"{val}" + (" руб." if key == 'price' else "")
                        cb.addItem(txt, itm)
                    cb.setFixedWidth(w)
                    cb.setStyleSheet(test3_styles())
                    # cb.setFont(category_font)
                    combos.append(cb)
                    row_layout.addWidget(cb)
                    if grp:  # Устанавливаем первый элемент по умолчанию
                        cb.setCurrentIndex(0)
                cont_v.addWidget(row)

                # Синхронизация комбобоксов
                def make_sync(a, b, c):
                    def sync():
                        src = QApplication.focusWidget()
                        data = src.currentData()
                        for cb in (a, b, c):
                            if cb is not src:
                                idx = next((i for i in range(cb.count()) if cb.itemData(i) == data), 0)
                                cb.blockSignals(True)
                                cb.setCurrentIndex(idx)
                                cb.blockSignals(False)

                    return sync

                a, b, c = combos
                fn = make_sync(a, b, c)
                a.currentIndexChanged.connect(fn)
                b.currentIndexChanged.connect(fn)
                c.currentIndexChanged.connect(fn)

            if cat_name != categories[-1][0]:
                separator = QFrame()
                separator.setFrameShape(QFrame.HLine)
                separator.setFrameShadow(QFrame.Sunken)
                separator.setStyleSheet("background-color: transparent; margin-top: 5px; margin-bottom: 5px;")
                cont_v.addWidget(separator)

        scroll.setWidget(content)

        # Кастомный скроллбар
        custom_scrollbar = CustomScrollBar(left)
        scrollbar_width = 15
        scrollbar_height = 760
        scrollbar_x = 930
        scrollbar_y = 20
        custom_scrollbar.setGeometry(scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height)
        internal_scrollbar = scroll.verticalScrollBar()
        internal_scrollbar.setSingleStep(3)
        custom_scrollbar.setSingleStep(1)
        custom_scrollbar.setRange(internal_scrollbar.minimum(), internal_scrollbar.maximum())
        custom_scrollbar.setPageStep(internal_scrollbar.pageStep())
        custom_scrollbar.valueChanged.connect(internal_scrollbar.setValue)
        internal_scrollbar.valueChanged.connect(custom_scrollbar.setValue)
        internal_scrollbar.rangeChanged.connect(lambda min, max: custom_scrollbar.setRange(min, max))

        # Позиционируем кнопки
        self.back_btn.move(50, 120 + 800 + 20)  # Под левой панелью
        pdf_btn.move(975 + 900 - 240, 120 + 800 + 20)  # Под правой панелью

        # Правая панель (контейнер для изображения)
        right_container = QWidget(self.page_result)
        right_container.setGeometry(1035, 120, 830, 800)
        right_container.setStyleSheet(
            "background-color: rgba(255,255,255,50); "
            "border-radius: 20px; "
            "border: 4px solid #006172;"
        )

        # Layout для правого контейнера
        right_layout = QVBoxLayout(right_container)
        right_layout.setAlignment(Qt.AlignCenter)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(20)

        # Контейнер для изображения и кнопки
        image_with_button = QWidget()
        image_with_button.setStyleSheet("background-color: transparent; border: none;")
        image_with_button.setMinimumSize(500, 400)

        # Layout с изображением и кнопкой
        stack_layout = QVBoxLayout(image_with_button)
        stack_layout.setContentsMargins(0, 0, 0, 0)
        stack_layout.setSpacing(0)

        # Обертка для кнопки в углу
        overlay_container = QWidget()
        overlay_container.setStyleSheet("background-color: transparent;")
        overlay_container.setMinimumHeight(70)
        overlay_layout = QHBoxLayout(overlay_container)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(0)
        overlay_layout.addStretch()

        # Кнопка просмотра
        expand_btn = QPushButton()
        expand_btn.setIcon(QIcon("icons/full-screen.png"))
        expand_btn.setIconSize(QSize(64, 64))
        expand_btn.setFixedSize(70, 70)
        expand_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                padding: 0px;
            }
            QPushButton:pressed {
                padding: 0px;
            }
        """)
        original_icon_size = QSize(64, 64)
        pressed_icon_size = QSize(50, 50)

        def on_press():
            icon_anim = QPropertyAnimation(expand_btn, b"iconSize")
            icon_anim.setDuration(200)
            icon_anim.setStartValue(original_icon_size)
            icon_anim.setEndValue(pressed_icon_size)
            icon_anim.start()
            expand_btn._icon_anim = icon_anim

        def on_release():
            icon_anim = QPropertyAnimation(expand_btn, b"iconSize")
            icon_anim.setDuration(200)
            icon_anim.setStartValue(pressed_icon_size)
            icon_anim.setEndValue(original_icon_size)
            icon_anim.start()
            expand_btn._icon_anim = icon_anim

        expand_btn.pressed.connect(on_press)
        expand_btn.released.connect(on_release)
        expand_btn.clicked.connect(self.show_fullscreen_image)

        overlay_layout.addWidget(expand_btn)
        stack_layout.addWidget(overlay_container)

        # Контейнер с изображением по центру
        image_container = QWidget()
        image_container.setStyleSheet("background-color: transparent; border: none;")
        image_layout = QVBoxLayout(image_container)
        image_layout.setAlignment(Qt.AlignCenter)

        if CURRENT_IMG_PATH and os.path.exists(CURRENT_IMG_PATH):
            pix = QPixmap(CURRENT_IMG_PATH)
            if not pix.isNull():
                img_label = QLabel()
                max_width = 800
                max_height = 600
                img_label.setPixmap(pix.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                img_label.setAlignment(Qt.AlignCenter)
                img_label.setStyleSheet("background-color: transparent;")
                image_layout.addWidget(img_label)
            else:
                placeholder = QLabel("Ошибка загрузки изображения")
                placeholder.setStyleSheet("color: red; font-size: 16px;")
                placeholder.setAlignment(Qt.AlignCenter)
                image_layout.addWidget(placeholder)
        else:
            placeholder = QLabel("ИЗОБРАЖЕНИЕ НЕ ЗАГРУЖЕНО")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("""
                color: #A8A8A8;
                font-size: 16px;
                background-color: rgba(255,255,255,50);
                border: 2px dashed #A8A8A8;
                border-radius: 10px;
                min-height: 400px;
                min-width: 600px;
            """)
            image_layout.addWidget(placeholder)

        image_container.setLayout(image_layout)
        stack_layout.addWidget(image_container, alignment=Qt.AlignCenter)

        # Добавляем финальный контейнер в правый layout
        right_layout.addWidget(image_with_button, alignment=Qt.AlignCenter)
        print("Контейнер с изображением добавлен в правое меню")

        self.stacked.setCurrentWidget(self.page_result)

    def show_fullscreen_image(self):
        """Показывает изображение на весь экран с плавной анимацией"""
        if not CURRENT_IMG_PATH or not os.path.exists(CURRENT_IMG_PATH):
            print("Нет изображения для отображения")
            return

        # Создаем полупрозрачный оверлей для всего окна
        self.fullscreen_overlay = QWidget(self)
        self.fullscreen_overlay.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.fullscreen_overlay.setStyleSheet("background-color: rgba(0, 0, 0, 220);")
        self.fullscreen_overlay.setGeometry(self.rect())
        self.fullscreen_overlay.setFocusPolicy(Qt.StrongFocus)

        # Создаем главный контейнер с вертикальным layout
        main_container = QWidget(self.fullscreen_overlay)
        main_container.setGeometry(50, 50, self.width() - 100, self.height() - 100)
        main_container.setStyleSheet("background-color: transparent; border: none;")

        # Вертикальный layout для изображения и кнопки
        layout = QVBoxLayout(main_container)

        # Создаем виджет для изображения (используем QScrollArea для возможности прокрутки)
        scroll_area = QScrollArea(main_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignCenter)
        scroll_area.setStyleSheet("background-color: transparent; border: none;")

        # Контейнер для изображения внутри QScrollArea
        image_widget = QWidget()
        image_widget.setStyleSheet("background-color: transparent;")
        image_layout = QVBoxLayout(image_widget)
        image_layout.setAlignment(Qt.AlignCenter)

        # Загружаем изображение
        self.fullscreen_img_label = QLabel(image_widget)
        pix = QPixmap(CURRENT_IMG_PATH)

        # Определяем минимальные размеры с учетом ориентации
        min_width = 400  # Минимальная ширина
        min_height = 300  # Минимальная высота
        original_width = pix.width()
        original_height = pix.height()
        aspect_ratio = original_width / original_height

        # Устанавливаем минимальный размер с сохранением пропорций
        if original_width < min_width or original_height < min_height:
            if aspect_ratio >= 1:  # Горизонтальная ориентация (ширина больше или равна высоте)
                scaled_width = max(min_width, original_width)
                scaled_height = int(scaled_width / aspect_ratio)
                scaled_height = max(min_height, scaled_height)  # Убеждаемся, что высота не меньше min_height
            else:  # Вертикальная ориентация (высота больше ширины)
                scaled_height = max(min_height, original_height)
                scaled_width = int(scaled_height * aspect_ratio)
                scaled_width = max(min_width, scaled_width)  # Убеждаемся, что ширина не меньше min_width
        else:
            scaled_width = original_width
            scaled_height = original_height

        # Устанавливаем изображение с учетом масштабирования
        scaled_pix = pix.scaled(
            scaled_width, scaled_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.fullscreen_img_label.setPixmap(scaled_pix)
        self.fullscreen_img_label.setAlignment(Qt.AlignCenter)
        image_layout.addWidget(self.fullscreen_img_label)
        scroll_area.setWidget(image_widget)

        # Добавляем scroll_area в основной layout
        layout.addWidget(scroll_area)

        # Контейнер для кнопок
        button_container = QWidget()
        button_container.setFixedHeight(50)
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)

        # Кнопка "Закрыть"
        close_btn = QPushButton("Закрыть (Esc)", button_container)
        close_btn.setFixedSize(150, 40)
        close_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                color: #006172;
                background-color: rgba(255,255,255,200);
                border-radius: 10px;
                border: 2px solid #006172;
            }
            QPushButton:hover {
                background-color: rgba(97,178,184,200);
                color: white;
            }
            QPushButton:pressed {
                background-color: rgba(0,97,114,200);
                color: white;
            }
        """)
        close_btn.clicked.connect(self.close_fullscreen_image)

        # Кнопки масштабирования
        zoom_in_btn = QPushButton("+", button_container)
        zoom_in_btn.setFixedSize(40, 40)
        zoom_in_btn.setStyleSheet("""
            QPushButton {
                font-size: 20px;
                font-weight: bold;
                color: #006172;
                background-color: rgba(255,255,255,200);
                border-radius: 20px;
                border: 2px solid #006172;
            }
            QPushButton:hover {
                background-color: rgba(97,178,184,200);
                color: white;
            }
            QPushButton:pressed {
                background-color: rgba(0,97,114,200);
                color: white;
            }
        """)

        zoom_out_btn = QPushButton("−", button_container)
        zoom_out_btn.setFixedSize(40, 40)
        zoom_out_btn.setStyleSheet("""
            QPushButton {
                font-size: 20px;
                font-weight: bold;
                color: #006172;
                background-color: rgba(255,255,255,200);
                border-radius: 20px;
                border: 2px solid #006172;
            }
            QPushButton:hover {
                background-color: rgba(97,178,184,200);
                color: white;
            }
            QPushButton:pressed {
                background-color: rgba(0,97,114,200);
                color: white;
            }
        """)

        # Добавляем кнопки в layout
        button_layout.addWidget(zoom_out_btn)
        button_layout.addWidget(close_btn)
        button_layout.addWidget(zoom_in_btn)

        # Добавляем контейнер с кнопками в основной layout
        layout.addWidget(button_container)

        # Устанавливаем обработчики событий для масштабирования
        self.current_scale = 1.0
        self.original_pixmap = pix

        def zoom_in():
            self.current_scale *= 1.2
            self.update_image_scale()

        def zoom_out():
            self.current_scale /= 1.2
            self.update_image_scale()

        def update_image_scale():
            min_scale = 0.1
            max_scale = 5.0
            self.current_scale = max(min_scale, min(self.current_scale, max_scale))
            scaled_width = int(self.original_pixmap.width() * self.current_scale)
            scaled_height = int(self.original_pixmap.height() * self.current_scale)
            scaled_pix = self.original_pixmap.scaled(
                scaled_width, scaled_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.fullscreen_img_label.setPixmap(scaled_pix)

        # Подключаем кнопки
        zoom_in_btn.clicked.connect(zoom_in)
        zoom_out_btn.clicked.connect(zoom_out)

        # Обработка колесика мыши для масштабирования
        def wheel_event(event):
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.ControlModifier:
                if event.angleDelta().y() > 0:
                    self.current_scale *= 1.1
                else:
                    self.current_scale *= 0.9
                update_image_scale()
                event.accept()
            else:
                event.ignore()

        scroll_area.wheelEvent = wheel_event

        # Обработка клавиш
        def key_press_event(event):
            if event.key() == Qt.Key_Escape:
                self.close_fullscreen_image()
            elif event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
                zoom_in()
            elif event.key() == Qt.Key_Minus:
                zoom_out()
            event.accept()

        self.fullscreen_overlay.keyPressEvent = key_press_event

        # Анимация появления
        self.fullscreen_overlay.setWindowOpacity(0.0)
        self.fullscreen_overlay.setWindowOpacity(0.0)
        self.fullscreen_overlay.setGeometry(self.geometry())
        self.fullscreen_overlay.show()

        # Анимация появления
        from PyQt5.QtCore import QParallelAnimationGroup

        start_rect = QRect(self.width() // 2, self.height() // 2, 10, 10)
        end_rect = QRect(0, 0, self.width(), self.height())

        geometry_anim = QPropertyAnimation(self.fullscreen_overlay, b"geometry")
        geometry_anim.setDuration(600)
        geometry_anim.setStartValue(start_rect)
        geometry_anim.setEndValue(end_rect)
        geometry_anim.setEasingCurve(QEasingCurve.InOutQuad)

        opacity_anim = QPropertyAnimation(self.fullscreen_overlay, b"windowOpacity")
        opacity_anim.setDuration(600)
        opacity_anim.setStartValue(0.0)
        opacity_anim.setEndValue(1.0)
        opacity_anim.setEasingCurve(QEasingCurve.InOutQuad)

        group = QParallelAnimationGroup()
        group.addAnimation(geometry_anim)
        group.addAnimation(opacity_anim)
        group.start()
        self.fullscreen_overlay._anim_group = group

    def keyPressEvent(self, event):
        """Обработчик нажатий клавиш для основного окна"""
        if event.key() == Qt.Key_Escape:
            if hasattr(self, 'fullscreen_overlay') and self.fullscreen_overlay.isVisible():
                self.close_fullscreen_image()
            else:
                # Обработка Escape для основного окна
                pass
        super().keyPressEvent(event)

    def close_fullscreen_image(self):
        """Закрывает полноэкранное изображение мгновенно"""
        if hasattr(self, 'fullscreen_overlay') and self.fullscreen_overlay.isVisible():
            print("Закрытие полноэкранного режима...")
            self._cleanup_fullscreen()

    def _cleanup_fullscreen(self):
        """Очистка после закрытия полноэкранного режима"""
        if hasattr(self, 'fullscreen_overlay') and self.fullscreen_overlay:
            self.fullscreen_overlay.deleteLater()
            del self.fullscreen_overlay
            print("Полноэкранный режим успешно закрыт")

    def update_image_scale(self):
        """Обновляет масштаб изображения в полноэкранном режиме"""
        if hasattr(self, 'fullscreen_img_label') and hasattr(self, 'original_pixmap'):
            scaled_width = int(self.original_pixmap.width() * self.current_scale)
            scaled_height = int(self.original_pixmap.height() * self.current_scale)
            scaled_pix = self.original_pixmap.scaled(
                scaled_width, scaled_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.fullscreen_img_label.setPixmap(scaled_pix)

    def load_data(self, content):
        """
        load_data _summary_
            Функция, обрабатывающая полученные
            данные
        Parameters
        ----------
        content : list
            Исходные громоздкие данные
        Returns
        -------
        flat : list
            Возвращает обработанный список
        (убрала открытие json-файла и извлечение
        из него данных)
        """
        try:
            print("Содержимое :", content)  # Отладка
            if isinstance(content, list):
                flat = []
                for cat in content:
                    if isinstance(cat, list):
                        for grp in cat:
                            if isinstance(grp, list): flat.append(grp)
                return flat
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
        return None

    def return_to_upload(self):
        self.stacked.setCurrentWidget(self.page_upload)

class CategoryManager:
    def __init__(self, category_name):
        self.category_name = category_name
        self.selected_items = []  # Список выбранных элементов
        self.available_items = []  # Все доступные элементы

    def add_item(self, item):
        """Добавляет новый элемент в список выбранных"""
        self.selected_items.append(item)

    def remove_item(self, index):
        """Удаляет элемент из списка выбранных"""
        if 0 <= index < len(self.selected_items):
            return self.selected_items.pop(index)
        return None

    def get_selected_items(self):
        """Возвращает список выбранных элементов"""
        return self.selected_items

    def set_available_items(self, items):
        """Устанавливает список доступных элементов"""
        self.available_items = items

    def get_available_items(self):
        """Возвращает список доступных элементов"""
        return self.available_items

def create_category_block(category_name, items_data, parent, saved_items=None):
    """Создает блок категории с всеми выбранными элементами и кнопкой добавления"""
    if saved_items is None:
        saved_items = []

    # Создаем менеджер категории
    category_manager = CategoryManager(category_name)
    category_manager.set_available_items(items_data)
    category_manager.selected_items = saved_items.copy()

    # Создаем контейнер для категории
    category_block = QWidget(parent)
    category_block.setObjectName(f"{category_name.lower().replace(' ', '_')}_block")
    layout = QVBoxLayout(category_block)

    # Заголовок категории
    header_label = QLabel(category_name)
    header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
    layout.addWidget(header_label)

    # Контейнер для строк элементов
    items_container = QWidget()
    items_layout = QVBoxLayout(items_container)
    items_layout.setAlignment(Qt.AlignTop)

    # Функция для добавления строки элемента
    def add_item_row(item_data=None):
        """Добавляет новую строку с QComboBox в контейнер"""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)

        # Создаем комбобоксы
        id_combo = QComboBox()
        name_combo = QComboBox()
        price_combo = QComboBox()

        # Заполняем комбобоксы уникальными элементами из категории
        for item in items_data:
            id_combo.addItem(item.get('id', ''), item)
            name_combo.addItem(item.get('name', ''), item)
            price_combo.addItem(str(item.get('price', '')), item)

        # Если передан item_data, устанавливаем его значения
        if item_data:
            index_id = id_combo.findText(item_data.get('id', ''))
            if index_id >= 0:
                id_combo.setCurrentIndex(index_id)
            index_name = name_combo.findText(item_data.get('name', ''))
            if index_name >= 0:
                name_combo.setCurrentIndex(index_name)
            price_text = str(item_data.get('price', ''))
            index_price = price_combo.findText(price_text)
            if index_price >= 0:
                price_combo.setCurrentIndex(index_price)

        # Добавляем кнопку удаления строки
        remove_button = QPushButton("−")
        remove_button.setFixedWidth(30)
        remove_button.clicked.connect(lambda: remove_row(row_widget, items_layout))

        # Добавляем виджеты в строку
        row_layout.addWidget(id_combo)
        row_layout.addWidget(name_combo)
        row_layout.addWidget(price_combo)
        row_layout.addWidget(remove_button)

        # Добавляем строку в контейнер
        items_layout.addWidget(row_widget)

        # Синхронизация комбобоксов
        def make_sync(a, b, c):
            def sync():
                src = QApplication.focusWidget()
                data = src.currentData()
                for cb in (a, b, c):
                    if cb is not src:
                        idx = next((i for i in range(cb.count()) if cb.itemData(i) == data), 0)
                        cb.blockSignals(True)
                        cb.setCurrentIndex(idx)
                        cb.blockSignals(False)
            return sync

        a, b, c = id_combo, name_combo, price_combo
        fn = make_sync(a, b, c)
        a.currentIndexChanged.connect(fn)
        b.currentIndexChanged.connect(fn)
        c.currentIndexChanged.connect(fn)

        return row_widget

    def remove_row(row_widget, layout):
        """Удаляет строку элемента из контейнера"""
        row_widget.setParent(None)
        row_widget.deleteLater()

    # Добавляем строки для каждого элемента в категории
    for item in saved_items:
        add_item_row(item)

    # Если нет сохраненных элементов, добавляем одну пустую строку
    if not saved_items and items_data:
        add_item_row(items_data[0] if items_data else None)

    return category_block


def add_custom_item(available_items, container, layout, add_item_row_func, category_manager):
    """Открывает диалог для добавления пользовательского элемента"""
    dialog = AddItemDialog(available_items)
    if dialog.exec_() == QDialog.Accepted:
        # Получаем данные из диалога
        item_data = dialog.get_item_data()

        # Проверяем, что все поля заполнены
        if item_data['id'] and item_data['name'] and item_data['price']:
            # Добавляем элемент в менеджер категории и интерфейс
            category_manager.add_item(item_data)
            add_item_row_func(item_data)
        else:
            QMessageBox.warning(
                None,
                "Недостаточно данных",
                "Пожалуйста, заполните все поля для нового элемента."
            )

class AddItemDialog(QDialog):
    def __init__(self, available_items=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить новый элемент")
        self.setModal(True)
        self.available_items = available_items or []
        self.selected_item = None

        layout = QVBoxLayout(self)

        # Вариант 1: Выбор из существующих элементов
        self.choice_group = QGroupBox("Выберите из существующих элементов")
        choice_layout = QVBoxLayout()

        self.existing_item_combo = QComboBox()
        for item in self.available_items:
            self.existing_item_combo.addItem(item.get('name', ''), item)

        choice_layout.addWidget(self.existing_item_combo)
        self.choice_group.setLayout(choice_layout)
        layout.addWidget(self.choice_group)

        # Вариант 2: Ввод нового элемента вручную
        self.custom_group = QGroupBox("Или добавьте новый элемент")
        custom_layout = QVBoxLayout()

        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("ID элемента")
        custom_layout.addWidget(QLabel("ID:"))
        custom_layout.addWidget(self.id_edit)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Название элемента")
        custom_layout.addWidget(QLabel("Название:"))
        custom_layout.addWidget(self.name_edit)

        self.price_edit = QLineEdit()
        self.price_edit.setPlaceholderText("Цена элемента")
        custom_layout.addWidget(QLabel("Цена:"))
        custom_layout.addWidget(self.price_edit)

        self.custom_group.setLayout(custom_layout)
        layout.addWidget(self.custom_group)

        # Кнопки OK и Cancel
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # При выборе элемента из списка заполняем поля формы
        self.existing_item_combo.currentIndexChanged.connect(self.update_custom_fields_from_selection)

    def update_custom_fields_from_selection(self, index):
        """Обновляет поля для ручного ввода при выборе элемента из списка"""
        if index >= 0:
            item_data = self.existing_item_combo.currentData()
            if item_data:
                self.id_edit.setText(item_data.get('id', ''))
                self.name_edit.setText(item_data.get('name', ''))
                self.price_edit.setText(str(item_data.get('price', '')))
                self.selected_item = item_data

    def get_item_data(self):
        """Возвращает данные нового элемента"""
        # Если выбран элемент из списка, используем его данные
        if self.selected_item:
            return self.selected_item.copy()

        # Иначе используем данные из полей ввода
        return {
            'id': self.id_edit.text(),
            'name': self.name_edit.text(),
            'price': self.price_edit.text()
        }

def test3_styles():
    return (
        "QComboBox {"
            "border:1px solid #A4A4A4; "
            "border-radius:10px; "
            "padding:5px;"
            "background-color:#F2F2F2; "
            "font-size:14px; "
            "color: black; "
            "font-weight: 400;"
        "}"
        "QComboBox::drop-down {"
            "subcontrol-origin:padding; "
            "subcontrol-position:right; "
            "width:20px;"
            "border-left:none; "
            "border-top-right-radius:5px; "
            "border-bottom-right-radius:10px;"
        "}"
        "QComboBox::down-arrow {"
            "image:url(icons/drop_down.png); "
            "width:10px; "
            "height:10px;"
        "}"
        "QComboBox QAbstractItemView { "
            "border:none; "
            "background:#fff; "
            "selection-background-color:#6CB9C4;"
        "}"
    )

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

    main_font_id = font_db.addApplicationFont("./font/Manrope-VariableFont_wght.ttf")
    if main_font_id != -1:
        main_font_family = font_db.applicationFontFamilies(main_font_id)[0]
        app.setFont(QFont(main_font_family, 10))  # Устанавливаем как шрифт по умолчанию

    header_font_id = font_db.addApplicationFont("./font/Manrope-SemiBold.ttf")
    if header_font_id != -1:
        header_font_family = font_db.applicationFontFamilies(header_font_id)[0]
    else:
        header_font_family = None
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())



