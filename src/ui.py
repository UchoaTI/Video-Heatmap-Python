import cv2
import sys
import json
import numpy as np
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QSlider, QComboBox, 
                           QFileDialog, QGroupBox, QCheckBox, QSpinBox, QToolBar,
                           QProgressBar, QMessageBox, QDoubleSpinBox, QTabWidget,
                           QSplitter, QTreeWidget, QTreeWidgetItem, QAction, QFrame,
                           QToolButton, QMenu, QStatusBar, QStyle, QStyleFactory,
                           QSizePolicy)
from PyQt5.QtCore import (Qt, QTimer, pyqtSlot, QThread, pyqtSignal, QRect, QSize, 
                        QPoint)
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QBrush, QIcon, QPalette, QFont
from .processor import VideoHeatmapProcessor

class TimelineWidget(QWidget):
    """Widget customizado para timeline com marcadores de início e fim (estilo DaVinci Resolve)"""
    
    rangeChanged = pyqtSignal(float, float)  # Emitido quando o intervalo é alterado (start, end)
    positionChanged = pyqtSignal(float)      # Emitido quando a posição atual muda
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.total_duration = 100.0  # Duração total em segundos
        self.start_marker = 0.0      # Posição inicial em segundos
        self.end_marker = 10.0       # Posição final em segundos
        self.current_pos = 0.0       # Posição atual em segundos
        
        self.dragging_start = False
        self.dragging_end = False
        self.dragging_current = False
        
        self.setMinimumHeight(60)  # Altura suficiente para interação
        self.setMouseTracking(True)  # Para detectar movimento do mouse
        
        # Gerar dados falsos de heatmap para visualização
        self.heatmap_data = None
        
    def setTotalDuration(self, duration):
        """Define a duração total do vídeo"""
        self.total_duration = duration
        if self.end_marker > duration:
            self.end_marker = duration
        self.update()
        
    def setRange(self, start, end):
        """Define o intervalo selecionado"""
        self.start_marker = max(0, min(start, self.total_duration))
        self.end_marker = min(max(end, self.start_marker), self.total_duration)
        self.update()
        
    def setCurrentPosition(self, pos):
        """Define a posição atual na timeline"""
        old_pos = self.current_pos
        self.current_pos = max(0, min(pos, self.total_duration))
        if old_pos != self.current_pos:
            self.positionChanged.emit(self.current_pos)
        self.update()
        
    def setHeatmapData(self, data):
        """Define os dados de heatmap para visualização na timeline"""
        self.heatmap_data = data
        self.update()
        
    def getCurrentPosition(self):
        """Retorna a posição atual em segundos"""
        return self.current_pos
        
    def getSelectedRange(self):
        """Retorna o intervalo selecionado (início, fim) em segundos"""
        return (self.start_marker, self.end_marker)
        
    def secondsToPixels(self, seconds):
        """Converte tempo em segundos para posição em pixels"""
        return int((seconds / self.total_duration) * (self.width() - 20)) + 10
        
    def pixelsToSeconds(self, pixels):
        """Converte posição em pixels para tempo em segundos"""
        return ((pixels - 10) / (self.width() - 20)) * self.total_duration
        
    def mousePressEvent(self, event):
        """Manipular clique do mouse"""
        x = event.x()
        
        # Verificar se clicou em um dos marcadores
        start_x = self.secondsToPixels(self.start_marker)
        end_x = self.secondsToPixels(self.end_marker)
        current_x = self.secondsToPixels(self.current_pos)
        
        # Tolerância para clique
        tolerance = 10
        
        if abs(x - start_x) <= tolerance:
            self.dragging_start = True
        elif abs(x - end_x) <= tolerance:
            self.dragging_end = True
        elif abs(x - current_x) <= tolerance:
            self.dragging_current = True
        else:
            # Clicou em algum outro ponto da timeline
            new_pos = self.pixelsToSeconds(x)
            self.setCurrentPosition(new_pos)
            
    def mouseMoveEvent(self, event):
        """Manipular movimento do mouse"""
        if any([self.dragging_start, self.dragging_end, self.dragging_current]):
            x = event.x()
            new_pos = self.pixelsToSeconds(x)
            new_pos = min(max(0, new_pos), self.total_duration)
            
            if self.dragging_start:
                if new_pos < self.end_marker:
                    self.start_marker = new_pos
                    self.rangeChanged.emit(self.start_marker, self.end_marker)
            elif self.dragging_end:
                if new_pos > self.start_marker:
                    self.end_marker = new_pos
                    self.rangeChanged.emit(self.start_marker, self.end_marker)
            elif self.dragging_current:
                self.setCurrentPosition(new_pos)
                
            self.update()
            
    def mouseReleaseEvent(self, event):
        """Manipular liberação do clique do mouse"""
        self.dragging_start = False
        self.dragging_end = False
        self.dragging_current = False
        
    def paintEvent(self, event):
        """Desenhar a timeline com estilo DaVinci Resolve"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Desenhar fundo
        painter.fillRect(0, 0, width, height, QColor(42, 42, 42))
        
        # Desenhar marcações de tempo (10% do tempo total cada)
        painter.setPen(QPen(QColor(70, 70, 70), 1))
        for i in range(11):  # 0% a 100%
            x = 10 + (i * (width - 20) / 10)
            painter.drawLine(int(x), 5, int(x), height - 5)
            
            # Adicionar texto de tempo nas marcações
            if i % 2 == 0:  # Mostrar apenas marcações pares para evitar sobreposição
                time_seconds = (i / 10) * self.total_duration
                mins, secs = divmod(int(time_seconds), 60)
                time_text = f"{mins:02d}:{secs:02d}"
                painter.setPen(QColor(220, 220, 220))  # Texto CLARO
                painter.drawText(int(x - 15), height - 8, 30, 15, Qt.AlignCenter, time_text)
                
        # Desenhar "heatmap" na timeline (representação visual da intensidade)
        if self.heatmap_data is not None:
            # Simulação de dados de heatmap
            for i in range(len(self.heatmap_data)):
                time_point, intensity = self.heatmap_data[i]
                if time_point <= self.total_duration:
                    x = self.secondsToPixels(time_point)
                    # Usar cor verde para visualizar intensidade (estilo forma de onda DaVinci)
                    painter.setPen(Qt.NoPen)
                    color = QColor(32, 217, 75, 200)  # Verde DaVinci com transparência
                    painter.setBrush(QBrush(color))
                    bar_height = int(intensity * (height * 0.4))
                    y_start = (height // 2) - (bar_height // 2)
                    painter.drawRect(x-1, y_start, 2, bar_height)
        
        # Desenhar área selecionada (entre marcadores início/fim)
        start_x = self.secondsToPixels(self.start_marker)
        end_x = self.secondsToPixels(self.end_marker)
        
        # Fundo da área selecionada
        painter.setPen(Qt.NoPen)
        selection_brush = QBrush(QColor(0, 90, 160, 80))  # Azul semitransparente
        painter.setBrush(selection_brush)
        painter.drawRect(start_x, 5, end_x - start_x, height - 10)
        
        # Linha de tempo principal (estilo DaVinci)
        painter.setPen(QPen(QColor(50, 120, 200), 2))
        painter.drawLine(10, height // 2, width - 10, height // 2)
        
        # Marcadores
        # Início (azul)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 140, 255)))
        painter.drawRect(start_x - 4, 5, 8, height - 10)
        
        # Fim (vermelho)
        painter.setBrush(QBrush(QColor(255, 60, 60)))
        painter.drawRect(end_x - 4, 5, 8, height - 10)
        
        # Posição atual (verde/branco)
        painter.setBrush(QBrush(QColor(220, 220, 220)))
        current_x = self.secondsToPixels(self.current_pos)
        
        # Linha vertical na posição atual
        painter.setPen(QPen(QColor(220, 220, 220), 1))
        painter.drawLine(current_x, 0, current_x, height)
        
        # Marcador triangular na posição atual (estilo cabeçote DaVinci)
        points = [
            QPoint(current_x, 0),
            QPoint(current_x - 8, 8),
            QPoint(current_x + 8, 8)
        ]
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(220, 220, 220)))
        painter.drawPolygon(points)
        
        # Desenhar tempos nos marcadores início/fim
        painter.setPen(QColor(220, 220, 220))  # Texto CLARO
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        
        # Formato min:seg
        start_min, start_sec = divmod(int(self.start_marker), 60)
        end_min, end_sec = divmod(int(self.end_marker), 60)
        cur_min, cur_sec = divmod(int(self.current_pos), 60)
        cur_frame = int((self.current_pos % 1) * 30)  # Assumindo 30fps
        
        # Textos de tempo estilo DaVinci (00:00:00:00)
        start_text = f"{start_min:02d}:{start_sec:02d}:00"
        end_text = f"{end_min:02d}:{end_sec:02d}:00"
        current_text = f"{cur_min:02d}:{cur_sec:02d}:{cur_frame:02d}"
        
        # Posicionar textos
        painter.drawText(start_x - 30, height - 8, 60, 15, Qt.AlignCenter, start_text)
        painter.drawText(end_x - 30, height - 8, 60, 15, Qt.AlignCenter, end_text)
        painter.drawText(current_x - 30, 15, 60, 15, Qt.AlignCenter, current_text)

class WaveformWidget(QWidget):
    """Widget para visualização de forma de onda de atividade do cursor"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cursor_positions = []
        self.width_seconds = 100.0  # Largura em segundos
        self.setMinimumHeight(80)
        
    def setCursorPositions(self, positions):
        """Define as posições do cursor para visualização"""
        self.cursor_positions = positions
        self.update()
        
    def setWidthSeconds(self, seconds):
        """Define a largura em segundos"""
        self.width_seconds = seconds
        self.update()
        
    def paintEvent(self, event):
        """Desenhar forma de onda estilo DaVinci"""
        if not self.cursor_positions:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Fundo
        painter.fillRect(0, 0, width, height, QColor(30, 30, 30))
        
        # Linha central
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.drawLine(0, height // 2, width, height // 2)
        
        # Calcular histograma de atividade
        max_time = self.width_seconds
        bins = width // 2  # Número de bins para o histograma
        bin_size = max_time / bins
        histogram = [0] * bins
        
        for time, _, _ in self.cursor_positions:
            if time <= max_time:
                bin_idx = min(int(time / bin_size), bins - 1)
                histogram[bin_idx] += 1
        
        # Normalizar histograma
        max_value = max(histogram) if histogram else 1
        normalized = [h / max_value for h in histogram]
        
        # Desenhar forma de onda (estilo DaVinci)
        points_top = []
        points_bottom = []
        
        for i, value in enumerate(normalized):
            x = i * 2  # Espaçamento de 2 pixels por bin
            y_center = height // 2
            y_offset = int(value * (height // 2 - 5))
            
            points_top.append(QPoint(x, y_center - y_offset))
            points_bottom.append(QPoint(x, y_center + y_offset))
        
        # Completar o polígono
        points = points_top + list(reversed(points_bottom))
        
        # Desenhar forma de onda preenchida
        painter.setPen(Qt.NoPen)
        gradient = QColor(32, 217, 75, 150)  # Verde DaVinci com transparência
        painter.setBrush(QBrush(gradient))
        
        if points:
            painter.drawPolygon(points)

class CursorDetectionThread(QThread):
    """Thread para processamento em segundo plano da detecção de cursor"""
    progress_updated = pyqtSignal(int)
    finished_processing = pyqtSignal(bool)
    
    def __init__(self, processor, min_area=3, max_area=500, threshold=15):
        super().__init__()
        self.processor = processor
        self.min_area = min_area
        self.max_area = max_area
        self.threshold = threshold
        
    def run(self):
        # Processar todo o vídeo para detectar cursores
        total_frames = self.processor.total_frames
        self.processor.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        frame_count = 0
        self.processor.cursor_positions = []
        prev_frame = None
        
        while True:
            ret, frame = self.processor.cap.read()
            if not ret:
                break
                
            # Timestamp do frame em segundos
            timestamp = frame_count / self.processor.fps
            
            # Detectar posição do cursor usando diferença entre frames
            x, y = -1, -1
            
            if prev_frame is not None:
                x, y = self.processor.detect_cursor_from_difference(
                    frame, prev_frame,
                    threshold=self.threshold,
                    min_area=self.min_area, 
                    max_area=self.max_area
                )
            
            # Armazenar posição se o cursor for detectado
            if x >= 0 and y >= 0:
                self.processor.cursor_positions.append((timestamp, x, y))
                
            # Armazenar frame para próxima comparação
            prev_frame = frame.copy()
            
            frame_count += 1
            
            # Emitir progresso
            progress = int((frame_count / total_frames) * 100)
            self.progress_updated.emit(progress)
            
        # Resetar o vídeo para o início
        self.processor.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.finished_processing.emit(True)

class VideoHeatmapApp(QMainWindow):
    """Interface gráfica para o aplicativo de heatmap de vídeo (estilo DaVinci Resolve)"""
    
    def __init__(self):
        super().__init__()
        
        self.processor = VideoHeatmapProcessor()
        
        # Removida a conexão do timer que estava causando o erro
        # self.timer = QTimer()
        # self.timer.timeout.connect(self.update_frame)
        
        # Para a linha do tempo
        self.current_time = 0
        self.start_time_window = 0
        self.end_time_window = 10  # 10 segundos iniciais
        
        # Aplicar estilo visual escuro
        self.apply_dark_style()
        
        # Inicializar UI
        self.init_ui()
        
    def apply_dark_style(self):
        """Aplica estilo visual escuro similar ao DaVinci Resolve"""
        self.setStyle(QStyleFactory.create("Fusion"))
        
        # Criar paleta escura
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(40, 40, 40))
        dark_palette.setColor(QPalette.WindowText, QColor(220, 220, 220))  # Texto mais claro
        dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.ToolTipText, QColor(220, 220, 220))  # Texto mais claro
        dark_palette.setColor(QPalette.Text, QColor(220, 220, 220))  # Texto mais claro
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))  # Texto mais claro
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, QColor(220, 220, 220))  # Texto mais claro
        
        # Aplicar paleta
        self.setPalette(dark_palette)
        
        # Adicionar stylesheet para mais elementos
        self.setStyleSheet("""
            QMainWindow {
                background-color: #282828;
            }
            QTabWidget::pane {
                border: 1px solid #303030;
                background-color: #232323;
            }
            QTabBar::tab {
                background-color: #353535;
                color: #DDDDDD;
                min-width: 80px;
                padding: 5px 10px;
            }
            QTabBar::tab:selected, QTabBar::tab:hover {
                background-color: #505050;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #424242;
                color: #DDDDDD;
                border: 1px solid #555555;
                border-radius: 2px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #4C4C4C;
                border: 1px solid #666666;
            }
            QPushButton:pressed {
                background-color: #2E5286;
            }
            QSlider::groove:horizontal {
                border: 1px solid #828282;
                height: 4px;
                background: #383838;
                margin: 0px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #5F5F5F;
                border: 1px solid #AAAAAA;
                width: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover {
                background: #6E6E6E;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #323232;
                color: #DDDDDD;
                border: 1px solid #555555;
                padding: 2px 4px;
            }
            QTreeWidget {
                background-color: #282828;
                color: #DDDDDD;
                border: 1px solid #555555;
            }
            QTreeWidget::item {
                color: #DDDDDD; /* Garantir que itens da árvore tenham texto claro */
            }
            QTreeWidget::item:selected {
                background-color: #2E5286;
            }
            QGroupBox {
                border: 1px solid #555555;
                margin-top: 12px;
                font-weight: bold;
                color: #DDDDDD;  /* Texto mais claro nos títulos */
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 3px;
                color: #DDDDDD;  /* Texto mais claro nos títulos */
            }
            QStatusBar {
                background-color: #323232;
                color: #BBBBBB;
            }
            QToolBar {
                background-color: #282828;
                border-bottom: 1px solid #444444;
            }
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 2px;
                text-align: center;
                background-color: #282828;
                color: #DDDDDD;  /* Texto mais claro */
            }
            QProgressBar::chunk {
                background-color: #2E5286;
            }
            QLabel {
                color: #DDDDDD;  /* Texto mais claro para todos os QLabel */
            }
            QHeaderView::section {
                background-color: #353535;
                color: #DDDDDD;  /* Texto mais claro */
                padding: 4px;
                border: 1px solid #555555;
            }
            QMenuBar {
                background-color: #282828;
                color: #FFFFFF;
            }
            QMenuBar::item {
                background-color: transparent;
                color: #FFFFFF;
                padding: 4px 10px;
            }
            QMenuBar::item:selected {
                background-color: #2E5286;
            }
            QMenu {
                background-color: #353535;
                color: #DDDDDD;
                border: 1px solid #555555;
            }
            QMenu::item:selected {
                background-color: #2E5286;
            }
            
            /* Corrigir botões do topo */
            QToolBar QPushButton, QToolBar QToolButton, QToolBar QAction {
                color: #FFFFFF;
                background-color: #353535;
                font-weight: bold;
            }
            
            /* Corrigir dropdown com texto claro em fundo claro */
            QComboBox QAbstractItemView {
                background-color: #353535;
                color: #FFFFFF;
                selection-background-color: #2E5286;
            }
            
            QToolBar QToolButton {
                color: #FFFFFF;
                background-color: transparent;
                border: none;
                padding: 6px 10px;
            }
            
            QToolBar QToolButton:hover {
                background-color: #3a3a3a;
            }
            
            QToolBar QToolButton:checked, QToolBar QToolButton:pressed {
                background-color: #2E5286;
            }
        """)
        
    def init_ui(self):
        """Inicializa a interface do usuário no estilo DaVinci Resolve"""
        self.setWindowTitle("Video Heatmap Analyzer Professional")
        self.resize(1280, 720)  # Tamanho inicial adequado para 1920x1080
        
        # Criar barra de ferramentas principal
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)
        
        # Ações da barra de ferramentas (com texto claro)
        open_action = QAction("Abrir", self)
        open_action.triggered.connect(self.browse_file)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        process_action = QAction("Processar", self)
        process_action.triggered.connect(self.process_video)
        toolbar.addAction(process_action)
        
        export_action = QAction("Exportar", self)
        export_action.triggered.connect(self.export_data)
        toolbar.addAction(export_action)
        
        toolbar.addSeparator()
        
        # Widget principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(2)  # Espaçamento mínimo
        
        # Painel superior: navegador de arquivos e visualização
        top_splitter = QSplitter(Qt.Horizontal)
        
        # ==============================================
        # Painel esquerdo: navegador de arquivos estilo DaVinci
        # ==============================================
        files_widget = QWidget()
        files_layout = QVBoxLayout(files_widget)
        files_layout.setContentsMargins(5, 5, 5, 5)
        
        # Título do painel
        files_header = QLabel("Arquivos de Mídia")
        files_header.setStyleSheet("font-weight: bold; color: #DDDDDD;")  # Texto claro
        files_layout.addWidget(files_header)
        
        # TreeWidget para arquivos (simplificado)
        self.files_tree = QTreeWidget()
        self.files_tree.setHeaderLabel("Nome")
        self.files_tree.setColumnCount(1)
        self.files_tree.setStyleSheet("color: #DDDDDD;")  # Texto claro
        
        # Adicionar apenas categorias principais
        videos_item = QTreeWidgetItem(["VÍDEOS"])
        videos_item.setForeground(0, QColor(220, 220, 220))
        
        processed_item = QTreeWidgetItem(["PROCESSADOS"])
        processed_item.setForeground(0, QColor(220, 220, 220))
        
        self.files_tree.addTopLevelItem(videos_item)
        self.files_tree.addTopLevelItem(processed_item)
        self.files_tree.expandAll()
        
        files_layout.addWidget(self.files_tree)
        
        # ==============================================
        # Painel central: visualização
        # ==============================================
        viewer_widget = QWidget()
        viewer_layout = QVBoxLayout(viewer_widget)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        
        # Área de visualização do vídeo
        self.video_view = QLabel()
        self.video_view.setAlignment(Qt.AlignCenter)
        self.video_view.setMinimumSize(640, 360)
        self.video_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Permitir expansão
        self.video_view.setStyleSheet("background-color: #111111; border: 1px solid #555555;")
        viewer_layout.addWidget(self.video_view)
        
        # Nome do arquivo atual
        self.current_file_label = QLabel("Nenhum arquivo aberto")
        self.current_file_label.setAlignment(Qt.AlignCenter)
        self.current_file_label.setStyleSheet("color: #DDDDDD;")  # Texto claro
        viewer_layout.addWidget(self.current_file_label)
        
        # Configurar política de dimensionamento para permitir ajuste automático
        central_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # ==============================================
        # Painel direito: propriedades e configurações
        # ==============================================
        props_widget = QWidget()
        props_layout = QVBoxLayout(props_widget)
        props_layout.setContentsMargins(5, 5, 5, 5)
        
        # Título do painel
        props_header = QLabel("Propriedades")
        props_header.setStyleSheet("font-weight: bold; color: #DDDDDD;")  # Texto claro
        props_layout.addWidget(props_header)
        
        # Configurações de detecção em um GroupBox
        detection_group = QGroupBox("Detecção de Cursor")
        detection_group.setStyleSheet("color: #DDDDDD;")  # Texto claro
        detection_layout = QVBoxLayout(detection_group)
        
        # Sensibilidade
        sensitivity_layout = QHBoxLayout()
        sensitivity_label = QLabel("Sensibilidade:")
        sensitivity_label.setStyleSheet("color: #DDDDDD;")  # Texto claro
        sensitivity_layout.addWidget(sensitivity_label)
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(5, 30)  # Valores menores para melhor sensibilidade
        self.threshold_slider.setValue(15)
        self.threshold_value = QLabel("15")
        self.threshold_value.setStyleSheet("color: #DDDDDD;")  # Texto claro
        self.threshold_slider.valueChanged.connect(lambda v: self.threshold_value.setText(str(v)))
        sensitivity_layout.addWidget(self.threshold_slider)
        sensitivity_layout.addWidget(self.threshold_value)
        detection_layout.addLayout(sensitivity_layout)
        
        # Tamanho mínimo/máximo
        size_layout = QHBoxLayout()
        size_label = QLabel("Min/Max:")
        size_label.setStyleSheet("color: #DDDDDD;")  # Texto claro
        size_layout.addWidget(size_label)
        self.min_size_spin = QSpinBox()
        self.min_size_spin.setRange(1, 50)
        self.min_size_spin.setValue(3)  # Valor menor para detectar cursores menores
        self.min_size_spin.setStyleSheet("color: #DDDDDD;")  # Texto claro
        size_layout.addWidget(self.min_size_spin)
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(10, 1000)
        self.max_size_spin.setValue(500)
        self.max_size_spin.setStyleSheet("color: #DDDDDD;")  # Texto claro
        size_layout.addWidget(self.max_size_spin)
        detection_layout.addLayout(size_layout)
        
        # Botão de processamento e progresso
        self.process_button = QPushButton("Processar Vídeo")
        self.process_button.setStyleSheet("color: #DDDDDD;")  # Texto claro
        self.process_button.clicked.connect(self.process_video)
        detection_layout.addWidget(self.process_button)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("color: #DDDDDD;")  # Texto claro
        detection_layout.addWidget(self.progress_bar)
        
        props_layout.addWidget(detection_group)
        
        # Configurações de visualização do heatmap
        heatmap_group = QGroupBox("Configurações de Heatmap")
        heatmap_group.setStyleSheet("color: #DDDDDD;")  # Texto claro
        heatmap_layout = QVBoxLayout(heatmap_group)
        
        # Resolução
        resolution_layout = QHBoxLayout()
        resolution_label = QLabel("Resolução:")
        resolution_label.setStyleSheet("color: #DDDDDD;")  # Texto claro
        resolution_layout.addWidget(resolution_label)
        self.resolution_slider = QSlider(Qt.Horizontal)
        self.resolution_slider.setRange(10, 200)
        self.resolution_slider.setValue(100)
        self.resolution_slider.valueChanged.connect(self.update_resolution)
        self.resolution_value = QLabel("100")
        self.resolution_value.setStyleSheet("color: #DDDDDD;")  # Texto claro
        resolution_layout.addWidget(self.resolution_slider)
        resolution_layout.addWidget(self.resolution_value)
        heatmap_layout.addLayout(resolution_layout)
        
        # Blur
        blur_layout = QHBoxLayout()
        blur_label = QLabel("Suavização:")
        blur_label.setStyleSheet("color: #DDDDDD;")  # Texto claro
        blur_layout.addWidget(blur_label)
        self.blur_slider = QSlider(Qt.Horizontal)
        self.blur_slider.setRange(3, 31)
        self.blur_slider.setValue(15)
        self.blur_slider.setSingleStep(2)
        self.blur_slider.valueChanged.connect(self.update_blur)
        self.blur_value = QLabel("15")
        self.blur_value.setStyleSheet("color: #DDDDDD;")  # Texto claro
        blur_layout.addWidget(self.blur_slider)
        blur_layout.addWidget(self.blur_value)
        heatmap_layout.addLayout(blur_layout)
        
        # Color Map
        colormap_layout = QHBoxLayout()
        colormap_label = QLabel("Esquema:")
        colormap_label.setStyleSheet("color: #DDDDDD;")  # Texto claro
        colormap_layout.addWidget(colormap_label)
        self.colormap_combo = QComboBox()
        self.colormap_combo.addItems(["hot", "jet", "inferno", "plasma", "viridis"])
        self.colormap_combo.setStyleSheet("color: #DDDDDD;")  # Texto claro
        self.colormap_combo.currentIndexChanged.connect(self.update_colormap)
        colormap_layout.addWidget(self.colormap_combo)
        heatmap_layout.addLayout(colormap_layout)
        
        # Botão para atualizar visualização
        self.update_view_button = QPushButton("Atualizar Visualização")
        self.update_view_button.setStyleSheet("color: #DDDDDD;")  # Texto claro
        self.update_view_button.clicked.connect(self.update_heatmap_view)
        heatmap_layout.addWidget(self.update_view_button)
        
        props_layout.addWidget(heatmap_group)
        
        # Botões de exportação
        export_group = QGroupBox("Exportação")
        export_group.setStyleSheet("color: #DDDDDD;")  # Texto claro
        export_layout = QVBoxLayout(export_group)
        
        self.screenshot_button = QPushButton("📷 Capturar Imagem")
        self.screenshot_button.setStyleSheet("color: #DDDDDD;")  # Texto claro
        self.screenshot_button.clicked.connect(self.take_screenshot)
        export_layout.addWidget(self.screenshot_button)
        
        self.export_button = QPushButton("💾 Exportar Dados")
        self.export_button.setStyleSheet("color: #DDDDDD;")  # Texto claro
        self.export_button.clicked.connect(self.export_data)
        export_layout.addWidget(self.export_button)
        
        props_layout.addWidget(export_group)
        
        # Adicionar stretch para preencher espaço vazio
        props_layout.addStretch(1)
        
        # Adicionar painéis ao splitter superior
        top_splitter.addWidget(files_widget)
        top_splitter.addWidget(viewer_widget)
        top_splitter.addWidget(props_widget)
        
        # Configurar proporções 20/60/20
        top_splitter.setSizes([200, 600, 200])
        
        # ==============================================
        # Painel inferior: timeline e controles
        # ==============================================
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        # Barra de ferramentas de transporte (controles de reprodução)
        transport_toolbar = QHBoxLayout()
        
        self.play_button = QPushButton("▶")
        self.play_button.setFixedSize(32, 32)
        self.play_button.setStyleSheet("color: #DDDDDD;")  # Texto claro
        self.play_button.clicked.connect(self.toggle_play)
        transport_toolbar.addWidget(self.play_button)
        
        self.stop_button = QPushButton("■")
        self.stop_button.setFixedSize(32, 32)
        self.stop_button.setStyleSheet("color: #DDDDDD;")  # Texto claro
        self.stop_button.clicked.connect(self.stop_playback)
        transport_toolbar.addWidget(self.stop_button)
        
        transport_toolbar.addSpacing(20)
        
        self.time_display = QLabel("00:00:00.00")
        self.time_display.setStyleSheet("font-family: monospace; font-size: 14px; color: #DDDDDD;")  # Texto claro
        self.time_display.setFixedWidth(120)
        transport_toolbar.addWidget(self.time_display)
        
        transport_toolbar.addStretch(1)
        
        bottom_layout.addLayout(transport_toolbar)
        
        # Visualização de forma de onda de atividade
        self.waveform_widget = WaveformWidget()
        bottom_layout.addWidget(self.waveform_widget)
        
        # Timeline customizada com estilo DaVinci
        self.timeline_widget = TimelineWidget()
        self.timeline_widget.rangeChanged.connect(self.timeline_range_changed)
        self.timeline_widget.positionChanged.connect(self.update_current_position)
        bottom_layout.addWidget(self.timeline_widget)
        
        # Adicionar splitter vertical (divide parte superior/inferior)
        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(bottom_widget)
        
        # Configurar proporções 70/30
        main_splitter.setSizes([700, 300])
        
        # Adicionar splitter ao layout principal
        main_layout.addWidget(main_splitter)
        
        # Barra de status
        status_bar = QStatusBar()
        status_bar.setStyleSheet("color: #DDDDDD;")  # Texto claro
        self.status_label = QLabel("Pronto")
        self.status_label.setStyleSheet("color: #DDDDDD;")  # Texto claro
        status_bar.addWidget(self.status_label)
        self.setStatusBar(status_bar)
        
        # Desabilitar controles inicialmente
        self.disable_controls()
        
    def disable_controls(self):
        """Desabilita controles que requerem vídeo carregado"""
        self.process_button.setEnabled(False)
        self.timeline_widget.setEnabled(False)
        self.waveform_widget.setEnabled(False)
        self.play_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.update_view_button.setEnabled(False)
        self.screenshot_button.setEnabled(False)
        self.export_button.setEnabled(False)
        
    def enable_controls(self):
        """Habilita controles após vídeo ser carregado"""
        self.process_button.setEnabled(True)
        
    def enable_time_controls(self):
        """Habilita controles após processamento"""
        self.timeline_widget.setEnabled(True)
        self.waveform_widget.setEnabled(True)
        self.play_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.update_view_button.setEnabled(True)
        self.screenshot_button.setEnabled(True)
        self.export_button.setEnabled(True)
        
    def browse_file(self):
        """Abrir diálogo para selecionar arquivo de vídeo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Arquivo de Vídeo", "", 
            "Arquivos de Vídeo (*.mp4 *.avi *.mov *.mkv *.wmv);;Todos os Arquivos (*)"
        )
        
        if file_path:
            # Extrair apenas o nome do arquivo
            file_name = file_path.split("/")[-1]
            self.current_file_label.setText(file_name)
            
            # Tentar abrir o vídeo
            if self.processor.open_video(file_path):
                self.status_label.setText(f"Vídeo carregado: {file_name}")
                
                # Configurar timeline
                duration = self.processor.video_duration
                self.timeline_widget.setTotalDuration(duration)
                self.timeline_widget.setRange(0, min(10, duration))
                
                # Atualizar variáveis de tempo
                self.start_time_window = 0
                self.end_time_window = min(10, duration)
                
                # Atualizar exibição de tempo
                self.update_time_display(0)
                
                # Habilitar controles
                self.enable_controls()
                
                # Mostrar o primeiro frame
                frame = self.processor.get_frame_at_time(0)
                if frame is not None:
                    self.display_frame(frame)
                    
                # Adicionar ao tree widget como item atual na categoria VÍDEOS
                new_video_item = QTreeWidgetItem(["◉ " + file_name])
                new_video_item.setForeground(0, QColor(0, 200, 255))
                
                # Encontrar o item VÍDEOS
                for i in range(self.files_tree.topLevelItemCount()):
                    if self.files_tree.topLevelItem(i).text(0) == "VÍDEOS":
                        self.files_tree.topLevelItem(i).addChild(new_video_item)
                        self.files_tree.expandItem(self.files_tree.topLevelItem(i))
                        break
            else:
                self.status_label.setText("Erro ao abrir o vídeo")
        
    def process_video(self):
        """Inicia o processamento do vídeo para detecção de cursor"""
        # Verificar se já existe uma thread em execução
        if hasattr(self, 'detection_thread') and self.detection_thread.isRunning():
            QMessageBox.warning(self, "Processamento em Andamento", 
                              "Já existe um processamento em execução. Aguarde.")
            return
            
        # Desabilitar controles durante o processamento
        self.process_button.setEnabled(False)
        self.process_button.setText("Processando...")
        
        # Configurar processador com base nas configurações atuais
        threshold = self.threshold_slider.value()
        min_area = self.min_size_spin.value()
        max_area = self.max_size_spin.value()
        
        # Se o vídeo estiver sendo reproduzido, pare primeiro
        if hasattr(self, 'play_timer') and self.play_timer.isActive():
            self.play_timer.stop()
            self.play_button.setText("▶")
        
        # Configurar e iniciar thread de processamento
        self.detection_thread = CursorDetectionThread(
            self.processor, 
            min_area=min_area, 
            max_area=max_area,
            threshold=threshold
        )
        self.detection_thread.progress_updated.connect(self.update_progress)
        self.detection_thread.finished_processing.connect(self.processing_finished)
        
        # Iniciar processamento
        self.status_label.setText("Processando vídeo para detecção de cursor...")
        self.progress_bar.setValue(0)
        self.detection_thread.start()
        
    def update_progress(self, value):
        """Atualiza a barra de progresso"""
        self.progress_bar.setValue(value)
        
    def processing_finished(self, success):
        """Chamado quando o processamento do vídeo termina"""
        if success:
            num_positions = len(self.processor.cursor_positions)
            self.status_label.setText(f"Processamento concluído. {num_positions} posições de cursor detectadas.")
            
            # Preparar dados de intensidade para visualização na timeline
            if num_positions > 0:
                # Ordenar por tempo
                sorted_positions = sorted(self.processor.cursor_positions, key=lambda x: x[0])
                
                # Gerar dados de heatmap para timeline
                timeline_data = []
                max_time = self.processor.video_duration
                bin_size = max_time / 100  # 100 bins
                bins = [0] * 100
                
                for time, _, _ in sorted_positions:
                    bin_idx = min(int(time / bin_size), 99)
                    bins[bin_idx] += 1
                
                # Normalizar
                max_bin = max(bins) if bins else 1
                for i, count in enumerate(bins):
                    intensity = count / max_bin
                    time_point = i * bin_size + (bin_size / 2)  # Centro do bin
                    timeline_data.append((time_point, intensity))
                
                # Definir dados na timeline
                self.timeline_widget.setHeatmapData(timeline_data)
                
                # Configurar widget de forma de onda
                self.waveform_widget.setCursorPositions(sorted_positions)
                self.waveform_widget.setWidthSeconds(max_time)
            
            # Habilitar controles de tempo
            self.enable_time_controls()
            
            # Atualizar visualização
            self.update_heatmap_view()
            
            # Adicionar ao tree widget como item processado na categoria PROCESSADOS
            processed_file_name = "Heatmap_" + self.current_file_label.text()
            processed_item = QTreeWidgetItem(["✓ " + processed_file_name])
            processed_item.setForeground(0, QColor(0, 255, 100))
            
            # Encontrar o item PROCESSADOS
            for i in range(self.files_tree.topLevelItemCount()):
                if self.files_tree.topLevelItem(i).text(0) == "PROCESSADOS":
                    self.files_tree.topLevelItem(i).addChild(processed_item)
                    self.files_tree.expandItem(self.files_tree.topLevelItem(i))
                    break
        else:
            self.status_label.setText("Erro durante o processamento.")
            
        # Reabilitar controles
        self.process_button.setEnabled(True)
        self.process_button.setText("Processar Vídeo")
    
    def timeline_range_changed(self, start, end):
        """Atualiza o intervalo de tempo quando alterado na timeline"""
        self.start_time_window = start
        self.end_time_window = end
        self.update_heatmap_view()
        
    def update_current_position(self, pos):
        """Atualiza a posição atual quando alterada na timeline"""
        self.current_time = pos
        self.update_time_display(pos)
        
        # Atualizar frame
        frame = self.processor.get_frame_at_time(pos)
        if frame is not None:
            if self.processor.cursor_positions:
                # Gerar heatmap
                heatmap = self.processor.generate_heatmap(
                    self.start_time_window, 
                    self.end_time_window,
                    self.resolution_slider.value()
                )
                
                # Aplicar heatmap ao frame
                result = self.processor.apply_heatmap_to_frame(frame, heatmap)
                
                # Exibir resultado
                self.display_frame(result)
            else:
                # Se não houver posições, apenas exibir o frame
                self.display_frame(frame)
                
    def update_time_display(self, seconds):
        """Atualiza a exibição de tempo no formato DaVinci Resolve (HH:MM:SS.FF)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        frames = int((seconds % 1) * 30)  # Assumindo 30fps
        
        self.time_display.setText(f"{hours:02d}:{minutes:02d}:{secs:02d}.{frames:02d}")
        
    def toggle_play(self):
        """Inicia ou pausa a reprodução com melhor taxa de frames"""
        if hasattr(self, 'play_timer') and self.play_timer.isActive():
            self.play_timer.stop()
            self.play_button.setText("▶")
        else:
            # Configurar timer para avançar a timeline
            self.play_timer = QTimer()
            self.play_timer.timeout.connect(self.advance_timeline)
            
            # Resetar o tempo da última atualização
            self.last_update_time = time.time()
            
            # Usar um intervalo menor para atualização mais frequente
            self.play_timer.start(16)  # Aproximadamente 60fps (~16.67ms)
            self.play_button.setText("⏸")
            
            # Desativar o processamento pesado durante a reprodução
            if hasattr(self, 'play_mode_original'):
                self.play_mode_original = True
            
    def stop_playback(self):
        """Para a reprodução e volta ao início"""
        if hasattr(self, 'play_timer') and self.play_timer.isActive():
            self.play_timer.stop()
            self.play_button.setText("▶")
            
        # Voltar para o início
        self.timeline_widget.setCurrentPosition(0)
        self.current_time = 0
        self.update_time_display(0)
        
        # Atualizar frame
        frame = self.processor.get_frame_at_time(0)
        if frame is not None:
            if self.processor.cursor_positions:
                # Gerar heatmap
                heatmap = self.processor.generate_heatmap(
                    self.start_time_window, 
                    self.end_time_window,
                    self.resolution_slider.value()
                )
                
                # Aplicar heatmap ao frame
                result = self.processor.apply_heatmap_to_frame(frame, heatmap)
                
                # Exibir resultado
                self.display_frame(result)
            else:
                # Se não houver posições, apenas exibir o frame
                self.display_frame(frame)
            
    def advance_timeline(self):
        """Avança a posição atual na timeline com melhor performance"""
        if not hasattr(self, 'last_update_time'):
            self.last_update_time = time.time()
            
        # Calcular tempo real decorrido desde a última atualização
        current_time = time.time()
        elapsed = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Usar o tempo real decorrido para avançar a timeline
        # multiplicado pelo FPS do vídeo para reprodução em velocidade correta
        current_pos = self.timeline_widget.getCurrentPosition()
        next_pos = current_pos + (elapsed * 1.0)  # Fator 1.0 para velocidade normal
        
        if next_pos >= self.processor.video_duration:
            # Chegou ao fim do vídeo, parar reprodução
            self.play_timer.stop()
            self.play_button.setText("▶")
            return
            
        # Atualizar posição
        self.timeline_widget.setCurrentPosition(next_pos)
        
    def update_heatmap_view(self):
        """Atualiza a visualização do heatmap"""
        # Obter frame na posição atual
        current_pos = self.timeline_widget.getCurrentPosition()
        frame = self.processor.get_frame_at_time(current_pos)
        if frame is None:
            return
            
        # Verificar se há dados de cursor
        if not self.processor.cursor_positions:
            # Apenas exibir o frame sem heatmap
            self.display_frame(frame)
            self.status_label.setText("Nenhuma posição de cursor detectada. Execute o processamento primeiro.")
            return
            
        # Gerar heatmap para a janela de tempo atual
        heatmap = self.processor.generate_heatmap(
            self.start_time_window, 
            self.end_time_window,
            self.resolution_slider.value()
        )
        
        # Aplicar heatmap ao frame
        result = self.processor.apply_heatmap_to_frame(frame, heatmap)
        
        # Exibir resultado
        self.display_frame(result)
        
        # Atualizar status
        num_points = sum(1 for t, _, _ in self.processor.cursor_positions 
                        if self.start_time_window <= t <= self.end_time_window)
        
        self.status_label.setText(
            f"Exibindo heatmap de {self.start_time_window:.1f}s a {self.end_time_window:.1f}s "
            f"({num_points} pontos)"
        )
        
    def display_frame(self, frame):
        """Exibe um frame na interface com redimensionamento adequado"""
        if frame is None:
            return
            
        h, w, c = frame.shape
        
        # Converter BGR para RGB (importante para cores corretas)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Converter para QImage com formato correto
        q_img = QImage(frame_rgb.data, w, h, w * c, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        
        # Obter tamanho do widget
        label_width = self.video_view.width()
        label_height = self.video_view.height()
        
        # Obter tamanho da área visível (considerando o layout)
        available_width = max(label_width, 640)  # Garantir largura mínima
        available_height = max(label_height, 360)  # Garantir altura mínima
        
        # Ajustar ao tamanho disponível mantendo proporção
        scaled_pixmap = pixmap.scaled(
            available_width, 
            available_height,
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation  # Qualidade alta
        )
        
        # Limpar qualquer pixmap anterior para garantir inicialização correta
        self.video_view.clear()
        
        # Centralizar a imagem no label
        self.video_view.setAlignment(Qt.AlignCenter)
        self.video_view.setPixmap(scaled_pixmap)
        
        # Forçar atualização da interface para garantir que o frame seja exibido corretamente
        self.video_view.update()
        
        # Salvar o frame atual para possível uso posterior
        self.current_frame = frame.copy()  # Criar uma cópia para evitar problemas de referência
        
    def update_blur(self, value):
        """Atualizar tamanho do blur"""
        # Garantir que é ímpar
        if value % 2 == 0:
            value += 1
            self.blur_slider.setValue(value)
        self.blur_value.setText(str(value))
        self.processor.set_blur_size(value)
        self.update_heatmap_view()
        
    def update_resolution(self, value):
        """Atualizar resolução do heatmap"""
        self.resolution_value.setText(str(value))
        self.update_heatmap_view()
        
    def update_colormap(self, index):
        """Atualizar esquema de cores do heatmap"""
        colormap = self.colormap_combo.currentText()
        self.processor.set_colormap(colormap)
        self.update_heatmap_view()
        
    def take_screenshot(self):
        """Capturar um frame e salvar como imagem"""
        # Solicitar local para salvar a imagem
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Captura", "", 
            "Imagens (*.png *.jpg *.jpeg);;Todos os Arquivos (*)"
        )
        
        if file_path:
            # Obter imagem atual
            pixmap = self.video_view.pixmap()
            if pixmap and not pixmap.isNull():
                pixmap.save(file_path)
                self.status_label.setText(f"Captura salva em {file_path}")
                
                # Adicionar ao tree widget
                capture_file_name = file_path.split("/")[-1]
                capture_item = QTreeWidgetItem(["📷 " + capture_file_name])
                capture_item.setForeground(0, QColor(220, 220, 100))
                
                # Encontrar o item PROCESSADOS
                for i in range(self.files_tree.topLevelItemCount()):
                    if self.files_tree.topLevelItem(i).text(0) == "PROCESSADOS":
                        self.files_tree.topLevelItem(i).addChild(capture_item)
                        self.files_tree.expandItem(self.files_tree.topLevelItem(i))
                        break
            
    def export_data(self):
        """Exportar dados de cursor para arquivo JSON"""
        # Verificar se há dados para exportar
        if not self.processor.cursor_positions:
            QMessageBox.warning(self, "Sem Dados", 
                              "Não há dados de cursor para exportar. Execute o processamento primeiro.")
            return
            
        # Solicitar local para salvar o arquivo
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Dados", "", 
            "Arquivos JSON (*.json);;Todos os Arquivos (*)"
        )
        
        if file_path:
            # Preparar dados para exportação
            data = {
                "video_info": {
                    "width": self.processor.width,
                    "height": self.processor.height,
                    "duration": self.processor.video_duration,
                    "fps": self.processor.fps,
                    "filename": self.current_file_label.text()
                },
                "cursor_positions": self.processor.cursor_positions,
                "heatmap_range": {
                    "start": self.start_time_window,
                    "end": self.end_time_window
                },
                "heatmap_settings": {
                    "resolution": self.resolution_slider.value(),
                    "blur_size": self.blur_slider.value(),
                    "colormap": self.colormap_combo.currentText()
                }
            }
            
            # Salvar como JSON
            try:
                with open(file_path, 'w') as f:
                    json.dump(data, f)
                self.status_label.setText(f"Dados exportados para {file_path}")
                
                # Adicionar ao tree widget
                export_file_name = file_path.split("/")[-1]
                export_item = QTreeWidgetItem(["💾 " + export_file_name])
                export_item.setForeground(0, QColor(100, 200, 255))
                
                # Encontrar o item PROCESSADOS
                for i in range(self.files_tree.topLevelItemCount()):
                    if self.files_tree.topLevelItem(i).text(0) == "PROCESSADOS":
                        self.files_tree.topLevelItem(i).addChild(export_item)
                        self.files_tree.expandItem(self.files_tree.topLevelItem(i))
                        break
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Exportar", f"Erro ao salvar arquivo: {str(e)}")
    
    def resizeEvent(self, event):
        """Lidar com redimensionamento da janela com atualização imediata"""
        super().resizeEvent(event)
        
        # Aguardar um momento para que o layout seja atualizado
        QTimer.singleShot(50, self.update_after_resize)
        
    def update_after_resize(self):
        """Atualiza o frame após o redimensionamento da janela"""
        # Atualizar frame se houver algum exibido
        if hasattr(self, 'current_frame') and self.current_frame is not None:
            self.display_frame(self.current_frame)
    
    def safe_release_resources(self):
        """Libera recursos de forma segura para prevenir erros de thread"""
        # Primeiro pare o timer, se existir
        if hasattr(self, 'play_timer') and self.play_timer.isActive():
            self.play_timer.stop()
        
        # Espere um pouco para garantir que os timers pararam
        QApplication.processEvents()
        
        # Se tiver uma thread rodando, termine e espere
        if hasattr(self, 'detection_thread') and self.detection_thread.isRunning():
            # Espera com timeout de 1 segundo
            self.detection_thread.wait(1000)
            if self.detection_thread.isRunning():
                self.detection_thread.terminate()
        
        # Liberar recursos de vídeo por último
        if hasattr(self, 'processor') and self.processor and hasattr(self.processor, 'cap') and self.processor.cap:
            self.processor.cap.release()
            
    def closeEvent(self, event):
        """Lidar com o fechamento da janela com segurança"""
        self.safe_release_resources()
        event.accept()