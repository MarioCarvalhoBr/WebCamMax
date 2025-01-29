import cv2
import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QTimer, QPoint, QEvent
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QIcon, QRegion
from PyQt5.QtWidgets import QStyle, QToolButton, QShortcut
from PyQt5.QtGui import QKeySequence

from filters import (
    apply_sobel,
    apply_gaussian,
    apply_salt_pepper,
    apply_gray
)

class SecondWindow(QtWidgets.QWidget):
    """
    Exemplo de janela secundária (frameless) com webcam, modo caneta e vários botões em uma barra:
        (1) Minimizar
        (2) Exit (fecha a janela)
        (3) Ocultar Barra (Ctrl+N / Ctrl+M para mostrar)
        (4) Flip Horizontal da webcam
        (5) Maximizar/Restaurar
        (6,7,8) Placeholders
        (9) Travar/Destravar (janela sempre no topo)
        (10) Redimensionar (arrastando o botão)

    Possui 2 formatos:
        - "circle": janela arredondada, barra centralizada.
        - "square": janela quadrada, barra na base.
    """

    def __init__(
        self,
        filter_selected=None,
        shape_selected="circle",
        window_locked=False,
        pen_mode=False
    ):
        super().__init__()

        # Configurações iniciais
        self.setWindowTitle("Janela Secundária")
        self.resize(500, 500)
        self.setObjectName("Form")

        # Estados
        self.filter_selected = filter_selected
        self.shape_selected = shape_selected
        self.window_locked = window_locked
        self.pen_mode = pen_mode
        self.is_flipped = False

        # Controle de webcam
        self.cap = None
        self.timer = None

        # Superfície de desenho (caneta)
        self.drawing_surface = QtGui.QImage(self.size(), QtGui.QImage.Format_ARGB32)
        self.drawing_surface.fill(Qt.transparent)
        self.last_point = QPoint()
        self.pen_color = Qt.red
        self.pen_width = 3

        # Variáveis auxiliares para arrastar e redimensionar a janela
        self._is_dragging = False
        self._drag_offset = QtCore.QPoint()
        self._is_resizing = False
        self._resize_origin = QtCore.QPoint()
        self._initial_size = self.size()

        # Variável de controle para Maximizar/Restaurar
        self.is_maximized = False
        self.normalGeometryStored = None

        # Frame principal
        self.mainFrame = QtWidgets.QFrame(self)
        self.mainFrame.setObjectName("mainFrame")
        self.mainFrame.setGeometry(0, 0, self.width(), self.height())

        # Label de vídeo
        self.video_label = QtWidgets.QLabel(self.mainFrame)
        self.video_label.setScaledContents(True)
        self.video_label.setGeometry(0, 0, self.mainFrame.width(), self.mainFrame.height())

        # Barra de ferramentas
        self.toolBarFrame = QtWidgets.QFrame(self.mainFrame)
        self.toolBarFrame.setObjectName("toolBarFrame")
        self.toolBarFrame.setStyleSheet("background: rgb(64, 224, 208)")
        self.toolBarLayout = QtWidgets.QHBoxLayout(self.toolBarFrame)
        self.toolBarLayout.setContentsMargins(5, 5, 5, 5)
        self.toolBarLayout.setSpacing(5)

        # (1) Exit (fecha a janela)
        self.btnExit = QToolButton(self.toolBarFrame)
        self.btnExit.setFixedSize(50, 50)
        self.btnExit.setIcon(QIcon("ICONS/icon_exit.png"))
        self.btnExit.setToolTip("Sair / Fechar")
        self.btnExit.clicked.connect(self.close)
        self.toolBarLayout.addWidget(self.btnExit)

        # (2) Minimizar
        self.btnMinimize = QToolButton(self.toolBarFrame)
        self.btnMinimize.setFixedSize(50, 50)
        self.btnMinimize.setIcon(QIcon("ICONS/icon_minimize.png"))
        self.btnMinimize.setToolTip("Minimizar")
        self.btnMinimize.clicked.connect(self.showMinimized)
        self.toolBarLayout.addWidget(self.btnMinimize)

        # (3) Maximizar/Restaurar
        self.btnMaxRestore = QToolButton(self.toolBarFrame)
        self.btnMaxRestore.setFixedSize(50, 50)
        self.btnMaxRestore.setIcon(QIcon("ICONS/icon_maximize.png"))
        self.btnMaxRestore.setToolTip("Maximizar / Restaurar")
        self.btnMaxRestore.clicked.connect(self.toggle_maximize_restore)
        self.toolBarLayout.addWidget(self.btnMaxRestore)
        

        # (4) Ocultar Barra
        self.btnHideBar = QToolButton(self.toolBarFrame)
        self.btnHideBar.setFixedSize(50, 50)
        self.btnHideBar.setIcon(QIcon("ICONS/icon_hide.png"))
        self.btnHideBar.setToolTip("Ocultar Barra")
        self.btnHideBar.clicked.connect(self.hide_toolbar)
        self.toolBarLayout.addWidget(self.btnHideBar)

        # (5) Flip Webcam
        self.btnFlip = QToolButton(self.toolBarFrame)
        self.btnFlip.setFixedSize(50, 50)
        self.btnFlip.setIcon(QIcon("ICONS/icon_flip.png"))
        self.btnFlip.setToolTip("Flip Horizontal")
        self.btnFlip.clicked.connect(self.flip_webcam)
        self.toolBarLayout.addWidget(self.btnFlip)

        

        # (6,7,8) Placeholders
        placeholder_icons = [
            "ICONS/icon_placeholder1.png",
            "ICONS/icon_placeholder2.png",
            "ICONS/icon_placeholder3.png"
        ]
        self.placeholder_buttons = []
        for i in range(3):
            btn = QToolButton(self.toolBarFrame)
            btn.setFixedSize(50, 50)
            btn.setIcon(QIcon(placeholder_icons[i]))
            btn.setToolTip(f"Placeholder {i+1}")
            self.toolBarLayout.addWidget(btn)
            self.placeholder_buttons.append(btn)

        # (9) Travar/Destravar
        self.btnLock = QToolButton(self.toolBarFrame)
        self.btnLock.setFixedSize(50, 50)
        self.btnLock.setToolTip("Travar/Destravar")
        if window_locked:
            self.btnLock.setIcon(QIcon("ICONS/icon_lock.png"))
        else:
            self.btnLock.setIcon(QIcon("ICONS/icon_unlock.png"))
        self.btnLock.clicked.connect(self.toggle_lock_state)
        self.toolBarLayout.addWidget(self.btnLock)

        # (10) Botão mudar Círculo/Quadrado
        self.btnShape = QToolButton(self.toolBarFrame)
        self.btnShape.setFixedSize(50, 50)
        self.btnShape.setIcon(QIcon("ICONS/icon_shape_change.png"))
        self.btnShape.setToolTip("Formato (Círculo/Quadrado)")
        self.btnShape.clicked.connect(self.apply_shape_change)
        self.toolBarLayout.addWidget(self.btnShape)


        # (11) Botão de Redimensionar
        self.btnResize = QToolButton(self.toolBarFrame)
        self.btnResize.setFixedSize(50, 50)
        self.btnResize.setIcon(QIcon("ICONS/icon_resize.png"))
        self.btnResize.setToolTip("Redimensionar")
        self.toolBarLayout.addWidget(self.btnResize)

        # Atalhos (ocultar/mostrar barra)
        self.shortcut_hide = QShortcut(QKeySequence("Ctrl+N"), self)
        self.shortcut_hide.activated.connect(self.hide_toolbar)
        self.shortcut_show = QShortcut(QKeySequence("Ctrl+M"), self)
        self.shortcut_show.activated.connect(self.show_toolbar)

        # Instala event filters
        self.installEventFilter(self)
        self.btnResize.installEventFilter(self)

        # Inicia webcam
        self.start_webcam()

        # Aplica formato (circle ou square) e lock (janela sempre no topo)
        self.apply_shape()
        self.apply_lock()
        self.update_lock_icon()

    # --------------------------------------------------------
    # 1) Ocultar/Mostrar a Barra
    # --------------------------------------------------------
    def hide_toolbar(self):
        self.toolBarFrame.hide()

    def show_toolbar(self):
        self.toolBarFrame.show()

    # --------------------------------------------------------
    # 2) Webcam e Filtros
    # --------------------------------------------------------
    def start_webcam(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QtWidgets.QMessageBox.critical(self, "Erro", "Não foi possível acessar a webcam.")
            return
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                if self.is_flipped:
                    frame = cv2.flip(frame, 1)
                frame = self.apply_filter(frame)
                # Converte para QImage
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_img)
                # Sobrepõe o desenho (caneta)
                pixmap = self.overlay_drawing(pixmap)
                self.video_label.setPixmap(pixmap)

    def apply_filter(self, frame):
        if self.filter_selected == 'sobel':
            return apply_sobel(frame)
        elif self.filter_selected == 'gaussian':
            return apply_gaussian(frame)
        elif self.filter_selected == 'salt_pepper':
            return apply_salt_pepper(frame)
        elif self.filter_selected == 'gray':
            return apply_gray(frame)
        return frame

    def flip_webcam(self):
        self.is_flipped = not self.is_flipped

    # --------------------------------------------------------
    # 3) Desenho (Caneta)
    # --------------------------------------------------------
    def overlay_drawing(self, pixmap):
        painter = QPainter(pixmap)
        painter.drawImage(0, 0, self.drawing_surface)
        painter.end()
        return pixmap

    # --------------------------------------------------------
    # 4) Maximizar / Restaurar
    # --------------------------------------------------------
    def toggle_maximize_restore(self):
        """
        Alterna entre "maximizado" (cobre a tela inteira)
        e "restaurado" (volta ao tamanho original).
        """
        if not self.is_maximized:
            """
                screen = QtWidgets.QApplication.desktop().screenGeometry()
                screen_h = screen.height()
                screen_w = screen.width()

                current_width = self.width()
                new_x = (screen_w - current_width) // 2
                new_y = 0  # topo da tela

                self.setGeometry(new_x, new_y, current_width, screen_h)
                # Como mudamos o tamanho, precisamos reajustar a barra e a máscara:
                self._adjust_on_resize()
            """
            # Guardar a geometria atual
            self.normalGeometryStored = self.geometry()

            # Pegar tamanho da tela e ocupar tudo
            screen = QtWidgets.QApplication.desktop().screenGeometry()
            screen_h = screen.height()
            screen_w = screen.width()

            current_width = screen_w // 2
            new_x = (screen_w - current_width) // 2
            new_y = 0  # topo da tela

            self.setGeometry(new_x, new_y, current_width, screen_h)

            self.is_maximized = True
            self.btnMaxRestore.setIcon(QIcon("ICONS/icon_restore.png"))
        else:
            # Voltar para a geometria normal
            if self.normalGeometryStored is not None:
                self.setGeometry(self.normalGeometryStored)

            self.is_maximized = False
            self.btnMaxRestore.setIcon(QIcon("ICONS/icon_maximize.png"))

        # Ajustar barra/máscara ao novo tamanho
        self._adjust_on_resize()

    # --------------------------------------------------------
    # 5) Travar/Destravar (Janela sempre no topo)
    # --------------------------------------------------------
    def toggle_lock_state(self):
        self.window_locked = not self.window_locked
        self.update_lock_icon()
        self.apply_lock()

    def update_lock_icon(self):
        if self.window_locked:
            self.btnLock.setIcon(QIcon("ICONS/icon_lock.png"))
        else:
            self.btnLock.setIcon(QIcon("ICONS/icon_unlock.png"))

    def apply_lock(self):
        if self.window_locked:
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
        self.show()

    # --------------------------------------------------------
    # 6) Formato (Circle / Square)
    # --------------------------------------------------------
    def apply_shape(self):
        """
        Aplica o formato escolhido (circle ou square) e,
        em seguida, reposiciona a barra de ferramentas.
        """
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        if self.shape_selected == 'circle':
            self.set_circular_style()
        else:
            self.set_square_style()

        self._adjust_toolbar_position()
        self.show()

    # --------------------------------------------------------
    # 6) Formato (Circle / Square)
    # --------------------------------------------------------
    def apply_shape_change(self):
        """
        Aplica o formato escolhido (circle ou square) e,
        em seguida, reposiciona a barra de ferramentas.
        """
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        if self.shape_selected == 'circle':
            self.shape_selected = 'square'
            print("Mudando para square")
            self.set_square_style()
        else:
            self.shape_selected = 'circle'
            print("Mudando para circle")
            self.set_circular_style()

        self._adjust_toolbar_position()
        self.show()

    def set_circular_style(self):
        self.setStyleSheet(
            "QWidget#Form {"
            "    background-color: rgba(255, 255, 255, 0);"
            "    border: 5px solid grey;"
            "    border-radius: 250px;"
            "}"
            "QFrame#mainFrame {"
            "    border: 5px solid grey;"
            "    border-radius: 245px;"
            "    background-color: rgba(255, 0, 0, 50);"
            "}"
            "QFrame#toolBarFrame {"
            "    background-color: rgba(230, 230, 230, 180);"
            "    border-radius: 0px;"
            "}"
        )
        region = QRegion(self.rect(), QRegion.Ellipse)
        self.setMask(region)

    def set_square_style(self):
        self.setStyleSheet(
            "QWidget#Form {"
            "    background-color: rgba(255, 255, 255, 0);"
            "    border: 5px solid grey;"
            "    border-radius: 0px;"
            "}"
            "QFrame#mainFrame {"
            "    border: 5px solid grey;"
            "    border-radius: 0px;"
            "    background-color: rgba(255, 0, 0, 50);"
            "}"
            "QFrame#toolBarFrame {"
            "    background-color: rgba(230, 230, 230, 180);"
            "    border-radius: 0px;"
            "}"
        )
        region = QRegion(self.rect(), QRegion.Rectangle)
        self.setMask(region)

    def _adjust_toolbar_position(self):
        """
        Reposiciona a barra de ferramentas de acordo com
        o formato atual.
        """
        toolbar_height = 50
        if self.shape_selected == 'circle':
            # Centralizada
            bar_width = int(self.width() * 0.8)
            bar_x = (self.width() - bar_width) // 2
            bar_y = (self.height() - toolbar_height) // 2
            self.toolBarFrame.setGeometry(bar_x, bar_y, bar_width, toolbar_height)
            region = QRegion(self.rect(), QRegion.Ellipse)
            self.setMask(region)
        else:
            # Na base (rodapé)
            self.toolBarFrame.setGeometry(
                0, self.height() - toolbar_height,
                self.width(), toolbar_height
            )
            region = QRegion(self.rect(), QRegion.Rectangle)
            self.setMask(region)

    # --------------------------------------------------------
    # 7) Eventos de Mouse (Desenho, Arraste, Resize)
    # --------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.pen_mode:
                # Início do desenho
                label_pos = self.video_label.mapFromParent(event.pos())
                self.last_point = label_pos
            else:
                # Se não clicou no botão de resize => arrastar janela
                if not self._is_over_button(self.btnResize, event):
                    self._is_dragging = True
                    self._drag_offset = event.globalPos() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.pen_mode and (event.buttons() & Qt.LeftButton):
            # Desenhando
            label_pos = self.video_label.mapFromParent(event.pos())
            painter = QPainter(self.drawing_surface)
            pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.last_point, label_pos)
            painter.end()
            self.last_point = label_pos
        elif self._is_dragging and (event.buttons() & Qt.LeftButton):
            # Arrastando janela
            self.move(event.globalPos() - self._drag_offset)
        elif self._is_resizing and (event.buttons() & Qt.LeftButton):
            # Redimensionando
            delta = event.globalPos() - self._resize_origin
            new_w = self._initial_size.width() + delta.x()
            new_h = self._initial_size.height() + delta.y()
            # Força w == h para manter forma
            side = max(new_w, new_h, self.minimumWidth(), self.minimumHeight())
            self.resize(side, side)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.pen_mode and event.button() == Qt.LeftButton:
            # Finaliza o traço
            label_pos = self.video_label.mapFromParent(event.pos())
            painter = QPainter(self.drawing_surface)
            pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.last_point, label_pos)
            painter.end()
        else:
            if event.button() == Qt.LeftButton:
                self._is_dragging = False
                self._is_resizing = False
        super().mouseReleaseEvent(event)

    # --------------------------------------------------------
    # 8) eventFilter (Resize da janela e Resize do botão)
    # --------------------------------------------------------
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize and obj is self:
            self._adjust_on_resize()
        if obj is self.btnResize:
            if event.type() == QtCore.QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._is_resizing = True
                self._resize_origin = event.globalPos()
                self._initial_size = self.size()
                return True
            elif event.type() == QtCore.QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                self._is_resizing = False
                return True
        return super().eventFilter(obj, event)

    def _adjust_on_resize(self):
        """
        Ajusta frames, label e desenho ao redimensionar.
        Também reposiciona a barra conforme o formato atual.
        """
        self.mainFrame.setGeometry(0, 0, self.width(), self.height())
        self.video_label.setGeometry(0, 0, self.mainFrame.width(), self.mainFrame.height())

        new_image = QtGui.QImage(self.size(), QtGui.QImage.Format_ARGB32)
        new_image.fill(Qt.transparent)
        painter = QPainter(new_image)
        painter.drawImage(0, 0, self.drawing_surface)
        painter.end()
        self.drawing_surface = new_image

        # Reposiciona a barra e a máscara
        self._adjust_toolbar_position()

    # --------------------------------------------------------
    # 9) Métodos auxiliares
    # --------------------------------------------------------
    def _is_over_button(self, btn, event):
        """Verifica se o clique está sobre um botão específico."""
        pos_in_btn = btn.mapFromGlobal(event.globalPos())
        return (0 <= pos_in_btn.x() <= btn.width()) and (0 <= pos_in_btn.y() <= btn.height())

    # --------------------------------------------------------
    # 10) Métodos de configuração externos
    # --------------------------------------------------------
    def set_filter(self, filter_name):
        self.filter_selected = filter_name

    def set_shape(self, shape):
        self.shape_selected = shape
        self.apply_shape()

    def set_lock(self, locked):
        self.window_locked = locked
        self.apply_lock()

    def set_pen_mode(self, mode):
        self.pen_mode = mode

    def set_flip(self, flipped):
        self.is_flipped = flipped

    # --------------------------------------------------------
    # 11) Fechamento da Janela
    # --------------------------------------------------------
    def closeEvent(self, event):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        super().closeEvent(event)


    def testEvent(self, event):
        print("Teste de evento")
        print(event)
