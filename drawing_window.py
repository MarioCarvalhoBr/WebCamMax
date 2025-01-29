from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap, QPainter, QPen, QImage, QColor
from PyQt5.QtWidgets import (
    QMainWindow,
    QAction,
    QMenuBar,
    QFileDialog,
    QMessageBox,
    QColorDialog,
    QToolBar
)

# Import QtWidgets
from PyQt5 import QtWidgets


class DrawingWindow(QMainWindow):
    """
    Janela dedicada ao desenho:
      - Canvas em branco (ou com imagem carregada).
      - Paleta de cores.
      - Funções de abrir, salvar, limpar.
      - Screenshot da tela para 'colar' no canvas.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Janela de Desenho")
        self.setGeometry(200, 100, 800, 600)

        # Imagem que usaremos como "canvas" para desenhar
        self.image = QImage(self.size(), QImage.Format_RGB32)
        self.image.fill(Qt.white)  # Preenche de branco

        # Propriedades do pincel
        self.drawing = False       # Se o mouse está pressionado
        self.brush_size = 3
        self.brush_color = Qt.black
        self.last_point = QPoint() # Último ponto usado para "ligar" as linhas

        # Cria barra de ferramentas com ações
        self.create_toolbar()

    def create_toolbar(self):
        toolbar = QToolBar("Ferramentas de Desenho")
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        # Ação para escolher cor
        action_color = QAction("Cor", self)
        action_color.triggered.connect(self.select_color)
        toolbar.addAction(action_color)

        # Ação para salvar
        action_save = QAction("Salvar", self)
        action_save.triggered.connect(self.save_drawing)
        toolbar.addAction(action_save)

        # Ação para abrir arquivo
        action_open = QAction("Abrir", self)
        action_open.triggered.connect(self.open_image)
        toolbar.addAction(action_open)

        # Ação para limpar
        action_clear = QAction("Limpar", self)
        action_clear.triggered.connect(self.clear_canvas)
        toolbar.addAction(action_clear)

        # Ação para fazer screenshot
        action_screenshot = QAction("Screenshot", self)
        action_screenshot.triggered.connect(self.take_screenshot)
        toolbar.addAction(action_screenshot)

    # ---------------------------------
    # Eventos de mouse
    # ---------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_point = event.pos()
            # Se quiser desenhar algo imediato ao clicar, pode chamar update()
            # mas normalmente só desenhamos no moveEvent.

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.LeftButton) and self.drawing:
            painter = QPainter(self.image)
            pen = QPen(self.brush_color, self.brush_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.last_point, event.pos())
            self.last_point = event.pos()
            self.update()  # Solicita o repaint() do widget

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False

    # ---------------------------------
    # paintEvent -> desenha o self.image
    # ---------------------------------
    def paintEvent(self, event):
        canvas_painter = QPainter(self)
        canvas_painter.drawImage(self.rect(), self.image, self.image.rect())

    # ---------------------------------
    # Funções de Toolbar
    # ---------------------------------
    def select_color(self):
        """Abre uma paleta de cores (QColorDialog) para escolher a cor do pincel."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.brush_color = color

    def save_drawing(self):
        """Salva o conteúdo do canvas em um arquivo de imagem."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Desenho",
            "",
            "Imagens (*.png *.jpg *.bmp);;Todos Arquivos (*)"
        )
        if file_path:
            if not self.image.save(file_path):
                QMessageBox.warning(self, "Salvar Desenho", "Não foi possível salvar a imagem.")

    def open_image(self):
        """Abre um arquivo de imagem e carrega no canvas."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir Imagem",
            "",
            "Imagens (*.png *.jpg *.bmp);;Todos Arquivos (*)"
        )
        if file_path:
            loaded_image = QImage(file_path)
            if loaded_image.isNull():
                QMessageBox.warning(self, "Abrir Imagem", "Não foi possível abrir a imagem.")
                return

            # Redimensiona o canvas para o tamanho da janela, se quiser.
            # Ou substitui a imagem direto e redimensiona a janela.
            self.image = loaded_image.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.update()

    def clear_canvas(self):
        """Limpa todo o canvas (preenche de branco)."""
        self.image.fill(Qt.white)
        self.update()

    def take_screenshot(self):
        """
        Faz um screenshot de toda a tela do computador,
        porém sem capturar esta janela de desenho.
        """
        # 1) Esconde a janela para que ela não apareça no screenshot
        self.hide()
        # Esconde a janela por 2 segundos. 
        from time import sleep
        

        # 2) Processa eventos pendentes para garantir que o sistema
        #    atualize a tela antes de capturar.
        QtWidgets.QApplication.processEvents()

        sleep(1)

        # 3) Captura a tela inteira (outra opção seria passar parâmetros
        #    x, y, w, h para capturar apenas uma região).
        screen = self.screen()
        pixmap = screen.grabWindow(0)

        # 4) Exibe a janela novamente
        self.show()

        # 5) Converte para QImage
        screenshot_image = pixmap.toImage()

        # 6) Desenha o screenshot no canvas (self.image)
        painter = QPainter(self.image)
        # Se quiser redimensionar proporcionalmente para caber no canvas:
        scaled_shot = screenshot_image.scaled(
            self.image.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        painter.drawImage(0, 0, scaled_shot)
        painter.end()

        self.update()
