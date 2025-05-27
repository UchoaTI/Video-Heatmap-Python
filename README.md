# Video-Heatmap-Python

Uma aplicação simples desenvolvida em Python para analisar um vídeo e gerar um heatmap (mapa de calor) baseado nos movimentos detetados ou, mais especificamente, nas posições do cursor registadas ao longo do tempo.

## Visão Geral

Este projeto utiliza bibliotecas como OpenCV para processamento de vídeo, NumPy para manipulação de dados numéricos, Matplotlib para a geração do heatmap e PyQt5 para a construção da interface gráfica do utilizador (GUI). A aplicação permite carregar um ficheiro de vídeo, processá-lo para extrair informações de movimento (posições do cursor) e, em seguida, visualizar ou guardar um mapa de calor que representa as áreas de maior atividade ou permanência.

## Funcionalidades Principais

*   **Carregamento de Vídeo:** Permite ao utilizador selecionar e carregar um ficheiro de vídeo a partir do sistema local.
*   **Processamento de Vídeo:** Analisa o vídeo frame a frame para detetar e registar posições relevantes (neste caso, parece focar-se nas posições do cursor associadas a timestamps).
*   **Geração de Heatmap:** Cria uma imagem de mapa de calor com base nas posições registadas. As áreas com maior concentração de pontos ou maior tempo de permanência são representadas com cores mais "quentes".
*   **Interface Gráfica:** Oferece uma interface de utilizador intuitiva construída com PyQt5 para facilitar a interação, incluindo:
    *   Seleção de ficheiro de vídeo.
    *   Visualização do progresso do processamento.
    *   Possivelmente, ajuste de parâmetros como fator de decaimento (`decay_factor`) e tamanho do desfoque (`blur_size`) que influenciam a aparência do heatmap.
    *   Pré-visualização e opção para guardar o heatmap gerado.
*   **Otimização (Opcional):** Tenta aumentar a prioridade do processo para melhorar a performance durante o processamento do vídeo (utilizando `psutil` em sistemas Windows e `os.nice` em Linux).

## Dependências

Para executar este projeto, necessita das seguintes bibliotecas Python instaladas:

*   **opencv-python==4.7.0.72:** Para leitura e processamento de vídeo.
*   **numpy==1.24.3:** Para operações numéricas eficientes, especialmente com arrays.
*   **matplotlib==3.7.1:** Para gerar e visualizar o mapa de calor.
*   **PyQt5==5.15.9:** Para a interface gráfica do utilizador.
*   **psutil (Opcional):** Utilizado para tentar aumentar a prioridade do processo.

## Instalação

Siga estes passos para configurar o ambiente e instalar as dependências:

1.  **Clone o Repositório:**
    ```bash
    git clone https://github.com/UchoaTI/Video-Heatmap-Python.git
    cd Video-Heatmap-Python
    ```

2.  **Crie um Ambiente Virtual (Recomendado):**
    ```bash
    python -m venv venv
    # Ative o ambiente virtual
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Instale as Dependências:**
    ```bash
    pip install -r requirement.txt
    ```
    Se encontrar problemas com `psutil` ou não necessitar da otimização de prioridade, pode tentar instalar as outras dependências individualmente ou remover `psutil` do `requirement.txt` antes de executar o comando `pip install`.

## Utilização

Após a instalação bem-sucedida das dependências:

1.  **Execute a Aplicação:**
    Navegue até ao diretório raiz do projeto (onde se encontra o ficheiro `main.py`) e execute o seguinte comando no seu terminal (com o ambiente virtual ativado):
    ```bash
    python main.py
    ```

2.  **Interaja com a Interface:**
    *   A interface gráfica será iniciada.
    *   Utilize o botão apropriado (provavelmente "Abrir Vídeo" ou similar) para selecionar o ficheiro de vídeo que deseja analisar.
    *   Aguarde o processamento do vídeo. O progresso poderá ser indicado numa barra de progresso.
    *   Após o processamento, o heatmap gerado deverá ser exibido na interface ou disponibilizado para ser guardado como um ficheiro de imagem (provavelmente na pasta `heatmap` ou numa localização escolhida pelo utilizador).

## Configuração

O ficheiro `src/processor.py` define a classe `VideoHeatmapProcessor` com alguns parâmetros que podem influenciar o resultado:

*   `decay_factor` (padrão: 0.95): Controla como a intensidade dos pontos do heatmap diminui ao longo do tempo.
*   `blur_size` (padrão: 15): Define o tamanho do kernel de desfoque aplicado ao heatmap, suavizando a visualização.

Atualmente, estes parâmetros parecem estar definidos no código. Modificações futuras poderiam expô-los na interface gráfica para ajuste pelo utilizador.

## Estrutura do Projeto

```
Video-Heatmap-Python/
├── executavel/       # (Provavelmente para versões compiladas)
├── heatmap/          # (Provavelmente diretório de saída padrão para heatmaps)
├── src/
│   ├── __init__.py
│   ├── processor.py  # Lógica de processamento de vídeo e geração de heatmap
│   └── ui.py         # Código da interface gráfica (PyQt5)
├── .gitattributes
├── .gitignore
├── main.py           # Ponto de entrada da aplicação
├── README.md         # Este ficheiro
└── requirement.txt   # Lista de dependências Python
```

## Contribuições

Contribuições para melhorar o projeto são bem-vindas. Sinta-se à vontade para abrir *issues* para reportar bugs ou sugerir novas funcionalidades, ou submeter *pull requests* com as suas melhorias.

## Licença

O repositório não especifica uma licença. Por favor, contacte o autor (@UchoaTI) para obter informações sobre os termos de uso e distribuição.

