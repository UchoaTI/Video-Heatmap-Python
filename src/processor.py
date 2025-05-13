import cv2
import numpy as np
import matplotlib.cm as cm
from matplotlib.colors import Normalize
import time

class VideoHeatmapProcessor:
    """Classe responsável pelo processamento do vídeo e geração do heatmap baseado em cursor"""
    
    def __init__(self, decay_factor=0.95, blur_size=15):
        self.decay_factor = decay_factor
        self.blur_size = blur_size
        self.cap = None
        self.width = 0
        self.height = 0
        self.colormap = 'hot'
        
        # Para armazenar os movimentos do cursor com timestamps
        self.cursor_positions = []  # Lista de (timestamp, x, y)
        self.video_duration = 0
        self.start_time = 0
        self.current_frame_pos = 0
        self.total_frames = 0
        self.fps = 0
        
    def open_video(self, source):
        """Abre a fonte de vídeo (arquivo)"""
        if self.cap is not None:
            self.cap.release()
            
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            return False
            
        # Obter informações do vídeo
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.video_duration = self.total_frames / self.fps
        
        ret, frame = self.cap.read()
        if not ret:
            return False
            
        self.height, self.width = frame.shape[:2]
        return True
    
    def detect_cursor_from_difference(self, frame, prev_frame=None, threshold=15, min_area=3, max_area=500):
        """
        Detecta cursor baseado na diferença entre frames consecutivos com precisão melhorada
        e redução de falsos positivos
        """
        if prev_frame is None or frame is None:
            return -1, -1
            
        # Converter para escala de cinza
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        
        # Aplicar blur leve para reduzir ruído antes da diferença (melhor redução de ruído)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        prev_gray = cv2.GaussianBlur(prev_gray, (5, 5), 0)
        
        # Calcular diferença
        diff = cv2.absdiff(gray, prev_gray)
        
        # Aplicar limiar - ajustado para reduzir falsos positivos
        _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
        
        # Aplicar operações morfológicas para melhorar detecção
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filtrar por área e forma - filtros mais restritivos
        valid_contours = []
        for c in contours:
            area = cv2.contourArea(c)
            if min_area <= area <= max_area:
                # Calcular circularidade - cursor tende a ser mais circular
                perimeter = cv2.arcLength(c, True)
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    # Aumentado o limite de circularidade para reduzir falsos positivos
                    if circularity > 0.35:  # Valor original era 0.2
                        # Adicional: verificar compacidade do objeto
                        x, y, w, h = cv2.boundingRect(c)
                        aspect_ratio = float(w) / h if h > 0 else 0
                        # Filtro adicional: cursores geralmente têm proporção próxima de 1:1
                        if 0.5 <= aspect_ratio <= 2.0:
                            valid_contours.append((c, area, circularity))
        
        if valid_contours:
            # Ordenar por uma combinação de área e circularidade (priorizar objetos pequenos e circulares)
            valid_contours.sort(key=lambda x: (x[1] * x[2]), reverse=True)
            
            # Pegar o melhor contorno
            contour = valid_contours[0][0]
            
            # Calcular centroide
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                return cx, cy
        
        return -1, -1
        
    def generate_heatmap(self, start_time, end_time, resolution=100):
        """
        Gera um mapa de calor baseado nas posições do cursor no intervalo de tempo especificado
        com otimização de performance
        """
        # Criar mapa de calor em branco
        heatmap = np.zeros((self.height, self.width), dtype=np.float32)
        
        # Se não houver posições, retornar mapa vazio
        if not self.cursor_positions:
            return heatmap
        
        # Otimização: pré-filtrar posições no intervalo de tempo para evitar verificação em loop
        positions_in_range = []
        for t, x, y in self.cursor_positions:
            if start_time <= t <= end_time:
                # Converter coordenadas para inteiros
                x, y = int(x), int(y)
                # Verificar se está dentro dos limites
                if 0 <= x < self.width and 0 <= y < self.height:
                    positions_in_range.append((x, y))
        
        # Adicionar cada posição do cursor ao mapa de calor
        for x, y in positions_in_range:
            # Adicionar ponto de calor
            cv2.circle(heatmap, (x, y), resolution//4, (1.0), -1)
        
        # Aplicar desfoque gaussiano para suavizar (se houver pontos)
        if positions_in_range:
            heatmap = cv2.GaussianBlur(heatmap, (self.blur_size, self.blur_size), 0)
        
        return heatmap
        
    def apply_heatmap_to_frame(self, frame, heatmap, alpha_max=0.7):
        """Aplica o mapa de calor a um frame de vídeo"""
        # Normalizar o heatmap
        norm = Normalize(vmin=0, vmax=np.max(heatmap) if np.max(heatmap) > 0 else 1)
        normalized_heatmap = norm(heatmap)
        
        # Aplicar mapa de cores
        cmap = getattr(cm, self.colormap)
        colored_heatmap = cmap(normalized_heatmap)
        colored_heatmap = (colored_heatmap[:, :, :3] * 255).astype(np.uint8)
        colored_heatmap_bgr = cv2.cvtColor(colored_heatmap, cv2.COLOR_RGB2BGR)
        
        # Criar máscara alpha
        alpha = normalized_heatmap * alpha_max
        
        # Aplicar heatmap sobre o frame
        result = frame.copy()
        for c in range(3):
            result[:, :, c] = frame[:, :, c] * (1 - alpha) + colored_heatmap_bgr[:, :, c] * alpha
            
        return result.astype(np.uint8)
        
    def get_frame_at_time(self, time_pos):
        """Obtém o frame do vídeo em um determinado momento"""
        if self.cap is None or not self.cap.isOpened():
            return None
            
        # Converter tempo para número de frame
        frame_pos = int(time_pos * self.fps)
        
        # Posicionar o vídeo nesse frame
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
        
        # Ler o frame
        ret, frame = self.cap.read()
        
        # Restaurar a posição anterior
        self.current_frame_pos = frame_pos
        
        if not ret:
            return None
            
        return frame
        
    def set_colormap(self, colormap_name):
        """Define o mapa de cores a ser usado"""
        self.colormap = colormap_name
        
    def set_blur_size(self, value):
        """Define o tamanho do desfoque (deve ser ímpar)"""
        self.blur_size = value if value % 2 == 1 else value + 1
        
    def release(self):
        """Libera os recursos de vídeo"""
        if self.cap is not None:
            self.cap.release()