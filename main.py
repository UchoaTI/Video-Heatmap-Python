#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Video Heatmap - Aplicativo para análise de movimento em vídeos
"""

import os
os.environ["OPENCV_VIDEOIO_MMAP_ENABLE"] = "0"  # Impede erros de sincronização de threads

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication, Qt
from src.ui import VideoHeatmapApp

# Aumenta a prioridade do processo para melhorar performance
def increase_process_priority():
    try:
        if sys.platform == 'win32':
            import psutil
            p = psutil.Process(os.getpid())
            p.nice(psutil.HIGH_PRIORITY_CLASS)
        elif sys.platform == 'linux':
            os.nice(-10)
    except:
        pass  # Se não conseguir aumentar prioridade, continua sem erro

def main():
    """Função principal do aplicativo com otimizações de performance"""
    # Aumentar prioridade do processo
    increase_process_priority()
    
    # Habilitar cache de OpenGL para melhorar renderização
    QCoreApplication.setAttribute(Qt.AA_UseDesktopOpenGL)
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    
    # Permitir escala de alta DPI para exibição adequada em monitores modernos
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # Criar aplicação
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Estilo moderno
    
    # Configurar atributos globais para otimização
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)
    
    # Criar instância da aplicação
    window = VideoHeatmapApp()
    window.show()
    
    # Executar loop da aplicação
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()