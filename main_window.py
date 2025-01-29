from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QMainWindow,
    QAction,
    QFileDialog,
    QMessageBox,
    QPushButton
)

from filters import (
    apply_sobel,
    apply_gaussian,
    apply_salt_pepper,
    apply_gray
)
from settings import save_mcam, load_mcam
from second_window import SecondWindow
from drawing_window import DrawingWindow


class MainWindow(QMainWindow):
    """
    Tela Principal:
      - Possui menus para filtros, borda (circular/quadrada), travar/destravar janela,
        caneta e salvar/carregar configurações.
      - Botão "Abrir Webcam" que lança a Tela Secundária (SecondWindow).
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Tela Principal - Projeto Webcam")
        self.resize(800, 600)

        # Variáveis de estado
        self.filter_selected = None     # 'sobel', 'gaussian', 'salt_pepper', 'gray', None
        self.shape_selected = 'square'  # 'square' ou 'circle'
        self.window_locked = True
        self.pen_mode = False
        self.is_flipped = False

        # Referência à Tela Secundária (inicialmente None)
        self.second_window = None

        # Botão "Abrir Webcam"
        self.btn_open_webcam = QPushButton("Abrir Webcam", self)
        self.btn_open_webcam.setGeometry(30, 50, 150, 40)
        self.btn_open_webcam.clicked.connect(self.open_second_window)


        # Botão "Fechar Webcam"
        self.btn_close_webcam = QPushButton("Fechar Webcam", self)
        self.btn_close_webcam.setGeometry(30, 100, 150, 40)
        self.btn_close_webcam.clicked.connect(self.close_second_window)

        # Cria os menus
        self.create_menus()

    def create_menus(self):
        menu_bar = self.menuBar()

        # Menu Arquivo
        menu_file = menu_bar.addMenu("Arquivo")
        action_save = QAction("Salvar Configurações", self)
        action_save.triggered.connect(self.save_config)
        menu_file.addAction(action_save)

        action_load = QAction("Carregar Configurações", self)
        action_load.triggered.connect(self.load_config)
        menu_file.addAction(action_load)

        menu_file.addSeparator()
        action_exit = QAction("Sair", self)
        action_exit.triggered.connect(self.close)
        menu_file.addAction(action_exit)

        # Menu Borda
        menu_borda = menu_bar.addMenu("Borda")
        action_square = QAction("Quadrado", self)
        action_square.triggered.connect(lambda: self.set_shape('square'))
        menu_borda.addAction(action_square)

        action_circle = QAction("Circular", self)
        action_circle.triggered.connect(lambda: self.set_shape('circle'))
        menu_borda.addAction(action_circle)

        # Menu Janela (Travar/Destravar)
        menu_window = menu_bar.addMenu("Janela")
        action_lock = QAction("Travar", self)
        action_lock.triggered.connect(self.lock_window)
        menu_window.addAction(action_lock)

        action_unlock = QAction("Destravar", self)
        action_unlock.triggered.connect(self.unlock_window)
        menu_window.addAction(action_unlock)

        # Menu Mostrar barra de ferramentas
        action_show_toolbar = QAction("Mostrar Barra de Ferramentas", self)
        action_show_toolbar.triggered.connect(self.show_toolbar)
        menu_window.addAction(action_show_toolbar)



        # Menu Filtros
        menu_filters = menu_bar.addMenu("Filtros")
        action_sobel = QAction("Sobel", self)
        action_sobel.triggered.connect(lambda: self.set_filter("sobel"))
        menu_filters.addAction(action_sobel)

        action_gauss = QAction("Gaussiano", self)
        action_gauss.triggered.connect(lambda: self.set_filter("gaussian"))
        menu_filters.addAction(action_gauss)

        action_salt = QAction("Sal e Pimenta", self)
        action_salt.triggered.connect(lambda: self.set_filter("salt_pepper"))
        menu_filters.addAction(action_salt)

        action_gray = QAction("Preto e Branco", self)
        action_gray.triggered.connect(lambda: self.set_filter("gray"))
        menu_filters.addAction(action_gray)

        menu_filters.addSeparator()
        action_reset = QAction("Resetar", self)
        action_reset.triggered.connect(lambda: self.set_filter(None))
        menu_filters.addAction(action_reset)

        # Menu Caneta
        menu_pen = menu_bar.addMenu("Desenho")
        action_pen_on = QAction("Abrir Desenho", self)
        action_pen_on.triggered.connect(lambda: self.set_whiteboard_mode(True))
        menu_pen.addAction(action_pen_on)

        action_pen_off = QAction("Sair do Desenho", self)
        action_pen_off.triggered.connect(lambda: self.set_whiteboard_mode(False))
        menu_pen.addAction(action_pen_off)

        # Menu Sobre
        menu_about = menu_bar.addMenu("Sobre")
        action_about = QAction("Sobre este projeto", self)
        action_about.triggered.connect(self.show_about)
        menu_about.addAction(action_about)

    # ----------------------------
    # Abertura da Tela Secundária
    # ----------------------------
    def open_second_window(self):
        if self.second_window is None:
            self.second_window = SecondWindow(
                filter_selected=self.filter_selected,
                shape_selected=self.shape_selected,
                window_locked=self.window_locked,
                pen_mode=self.pen_mode
            )
        else:
            # Atualiza as configurações da janela caso ela já exista
            self.second_window.set_filter(self.filter_selected)
            self.second_window.set_shape(self.shape_selected)
            self.second_window.set_lock(self.window_locked)
            self.second_window.set_whiteboard_mode(self.pen_mode)

        self.second_window.show()

    # ----------------------------
    # Fechamento da Tela Secundária
    # ----------------------------
    def close_second_window(self):
        if self.second_window:
            self.second_window.close()
            self.second_window = None

    # ----------------------------
    # Métodos para menus
    # ----------------------------
    def set_filter(self, filter_name):
        self.filter_selected = filter_name
        if self.second_window:
            self.second_window.set_filter(filter_name)

    def set_shape(self, shape):
        self.shape_selected = shape
        if self.second_window:
            self.second_window.set_shape(shape)

    def lock_window(self):
        self.window_locked = True
        if self.second_window:
            self.second_window.set_lock(True)

    def unlock_window(self):
        self.window_locked = False
        if self.second_window:
            self.second_window.set_lock(False)
    def show_toolbar(self):
        if self.second_window:
            self.second_window.show_toolbar()
            
    def set_whiteboard_mode(self, mode):
        if mode == True: 
            self.pen_mode = mode

            # Ao ativar a caneta, abrimos a nova janela de desenho
            if mode:
                self.open_drawing_window()
            else:
                self.close_drawing_window()

            # Se existir a janela secundária (webcam), podemos também atualizar o estado nela
            if self.second_window:
                self.second_window.set_whiteboard_mode(mode)
        else:
            self.pen_mode = mode
            self.close_drawing_window()

    def open_drawing_window(self):
        if not hasattr(self, 'drawing_window') or self.drawing_window is None:
            self.drawing_window = DrawingWindow()
        self.drawing_window.show()

    def close_drawing_window(self):
        if self.drawing_window:
            self.drawing_window.close()
            self.drawing_window = None

    # ----------------------------
    # Salvar/Carregar
    # ----------------------------
    def save_config(self):
        config_data = {
            "filter_selected": self.filter_selected,
            "shape_selected": self.shape_selected,
            "window_locked": self.window_locked,
            "pen_mode": self.pen_mode,
            "is_flipped": self.second_window.is_flipped
        }
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Salvar Configurações",
            "",
            "MCAM Files (*.mcam);;Todos Arquivos (*)"
        )
        if file_path:
            try:
                save_mcam(config_data, file_path)
                QtWidgets.QMessageBox.information(self, "Salvar Configurações", "Configurações salvas com sucesso!")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Erro", f"Erro ao salvar configurações:\n{e}")

    def load_config(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Carregar Configurações",
            "",
            "MCAM Files (*.mcam);;Todos Arquivos (*)"
        )
        if file_path:
            try:
                config_data = load_mcam(file_path)
                self.filter_selected = config_data.get("filter_selected", None)
                self.shape_selected = config_data.get("shape_selected", "square")
                self.window_locked = config_data.get("window_locked", False)
                self.pen_mode = config_data.get("pen_mode", False)
                self.is_flipped = config_data.get("is_flipped", False)

                # Se a segunda tela existir, atualiza:
                if self.second_window:
                    self.second_window.set_filter(self.filter_selected)
                    self.second_window.set_shape(self.shape_selected)
                    self.second_window.set_lock(self.window_locked)
                    self.second_window.set_whiteboard_mode(self.pen_mode)
                    self.second_window.set_flip(self.is_flipped)

                QtWidgets.QMessageBox.information(self, "Carregar Configurações", "Configurações carregadas com sucesso!")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Erro", f"Erro ao carregar configurações:\n{e}")

    # ----------------------------
    # Sobre
    # ----------------------------
    def show_about(self):
        msg = (
            "<b>Tela Principal - Projeto Webcam</b><br>"
            "Funcionalidades: <ul>"
            "<li>Menus para filtros, borda (circular/quadrada), travar/destravar janela</li>"
            "<li>Caneta para desenhar</li>"
            "<li>Salvar/Carregar .mcam</li>"
            "<li>Botão 'Abrir Webcam' -> abre a Tela Secundária</li>"
            "</ul>"
        )
        QtWidgets.QMessageBox.information(self, "Sobre", msg)

    # ----------------------------
    # Fechar
    # ----------------------------
    def closeEvent(self, event):
        if self.second_window:
            self.second_window.close()
        super().closeEvent(event)
