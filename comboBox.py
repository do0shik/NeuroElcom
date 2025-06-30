import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Интерфейс")
        self.setGeometry(100, 100, 400, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Секция "Трансформаторы"
        trans_label = QLabel("Трансформаторы")
        main_layout.addWidget(trans_label)

        trans_widget = QWidget()
        trans_layout = QHBoxLayout(trans_widget)

        trans_article = QComboBox()
        trans_article.addItems(["ART001", "ART002", "ART003"])
        trans_layout.addWidget(trans_article)

        trans_name = QComboBox()
        trans_name.addItems(["Тр-1", "Тр-2", "Тр-3"])
        trans_layout.addWidget(trans_name)

        main_layout.addWidget(trans_widget)

        # Секция "Счетчики"
        counters_label = QLabel("Счетчики")
        main_layout.addWidget(counters_label)

        counters_widget = QWidget()
        counters_layout = QHBoxLayout(counters_widget)

        counters_article = QComboBox()
        counters_article.addItems(["CNT001", "CNT002", "CNT003"])
        counters_layout.addWidget(counters_article)

        counters_name = QComboBox()
        counters_name.addItems(["Сч-1", "Сч-2", "Сч-3"])
        counters_layout.addWidget(counters_name)

        main_layout.addWidget(counters_widget)

        # Секция "Автоматические выключатели"
        breakers_label = QLabel("Автоматические выключатели")
        main_layout.addWidget(breakers_label)

        breakers_widget = QWidget()
        breakers_layout = QHBoxLayout(breakers_widget)

        breakers_article = QComboBox()
        breakers_article.addItems(["BRK001", "BRK002", "BRK003"])
        breakers_layout.addWidget(breakers_article)

        breakers_name = QComboBox()
        breakers_name.addItems(["АВ-1", "АВ-2", "АВ-3"])
        breakers_layout.addWidget(breakers_name)

        main_layout.addWidget(breakers_widget)

        self.apply_combobox_style(central_widget)
        self.set_background(central_widget)

    def apply_combobox_style(self, widget):
        # Стилизация всех QComboBox в окне
        style = """
            QComboBox {
                border: 1px solid #A4A4A4;
                border-radius: 10px;
                padding: 5px;
                background-color: #F2F2F2;
                font-size: 14px;
                color: #000000;
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
        """
        widget.setStyleSheet(style)

    def set_background(self, widget):
        # Установка белого фона для центрального виджета
        background_style = """
            QWidget {
                background-color: #FFFFFF;
                border: none;  /* Убираем возможные границы */
            }
        """
        # Применяем стиль, объединяя с существующим, если он есть
        current_style = widget.styleSheet()
        if current_style:
            widget.setStyleSheet(current_style + background_style)
        else:
            widget.setStyleSheet(background_style)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())