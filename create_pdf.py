from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import tempfile

def create_pdf(self):
    """Создает PDF файл с изображением и таблицей данных"""
    # Создаем временный файл для PDF
    pdf_path = os.path.join(tempfile.gettempdir(), "result.pdf")

    # Создаем документ PDF
    doc = SimpleDocTemplate(pdf_path, pagesize=landscape(letter),
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=72)

    elements = []

    # 1. Добавляем изображение на первую страницу
    if CURRENT_IMG_PATH and os.path.exists(CURRENT_IMG_PATH):
        img = Image(CURRENT_IMG_PATH)
        img.drawWidth = 400  # Устанавливаем ширину изображения в пунктах (1/72 дюйма)
        img.drawHeight = 400  # Высота будет автоматически подобрана пропорционально

        # Добавляем заголовок
        styles = getSampleStyleSheet()
        title = Paragraph("Изображение", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.25*inch))
        elements.append(img)
        elements.append(PageBreak())  # Переход на новую страницу
    else:
        elements.append(Paragraph("Изображение не загружено", styles['Normal']))
        elements.append(PageBreak())

    # 2. Собираем данные для таблицы
    data = self.load_data('example/test.json')
    if not data:
        elements.append(Paragraph("Нет данных для отображения", styles['Normal']))
        return

    # Создаем список для таблицы
    table_data = []

    # Перебираем категории и их элементы
    categories = [
        ('Автоматические выключатели', switches),
        ('Трансформаторы', transformers),
        ("Счетчики 'Меркурий'", meters)
    ]

    # Функция для получения данных из выпадающих списков
    def get_selected_data(combo_boxes):
        """Получает выбранные данные из набора QComboBox"""
        selected_items = []
        for cb in combo_boxes:
            if cb.currentIndex() >= 0:
                data = cb.currentData()
                if isinstance(data, dict):
                    selected_items.append(data)
        return selected_items

    # Получаем все строки с комбобоксами
    combo_rows = []
    # Найдем все строки с комбобоксами в content
    for child in content.children():
        if isinstance(child, QWidget):
            for row_child in child.children():
                if isinstance(row_child, QWidget):
                    combos = []
                    for widget in row_child.children():
                        if isinstance(widget, QComboBox):
                            combos.append(widget)
                    if combos:
                        combo_rows.append(combos)

    # Создаем таблицу для каждой категории
    for cat_name, groups in categories:
        if not groups:
            continue

        # Добавляем заголовок категории
        elements.append(Paragraph(cat_name, styles['Heading2']))
        elements.append(Spacer(1, 0.2*inch))

        # Заголовки таблицы
        headers = ["Артикул", "Наименование", "Цена"]
        table_data = [headers]

        # Для каждой группы в категории получаем данные
        for grp in groups:
            if not grp:
                continue

            # Получаем выбранные элементы из комбобоксов
            # Но у нас нет прямого доступа к текущим значениям комбобоксов
            # Поэтому для примера просто добавим все элементы в таблицу
            for item in grp:
                if isinstance(item, dict):
                    row = [
                        item.get('id', ''),
                        item.get('name', ''),
                        str(item.get('price', '')) + " руб." if item.get('price', '') else ''
                    ]
                    table_data.append(row)

        # Создаем таблицу
        if len(table_data) > 1:  # Если есть данные помимо заголовков
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))

    # Генерируем PDF
    doc.build(elements)

    # Открываем PDF в системном просмотрщике
    if sys.platform == 'win32':
        os.startfile(pdf_path)
    elif sys.platform == 'darwin':
        subprocess.call(['open', pdf_path])
    else:
        subprocess.call(['xdg-open', pdf_path])
