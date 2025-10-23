# Projeto de Pathfinding (IA) - CS2D com Prolog e Pygame

Este é um projeto de simulação de Inteligência Artificial que utiliza **Prolog** para a lógica de backend (busca de caminho) e **Pygame** (Python) para a interface gráfica e simulação.

O objetivo é simular um agente (Terrorista) que deve navegar em um grid 2D, encontrar o caminho mais curto até um objetivo (Bombsite), enquanto desvia de obstáculos e de zonas de perigo criadas por Contra-Terroristas (CTs).


## 1. Tecnologias Utilizadas

* **Backend (Lógica de IA):** **Prolog** (SWI-Prolog)
    * Utiliza um algoritmo de **Busca em Largura (BFS)** para garantir o caminho *mais curto* em um grafo não ponderado.
* **Frontend (GUI e Simulação):** **Python 3** com a biblioteca **Pygame**
    * Renderiza o grid, os assets (imagens), a animação do agente e a interface do usuário (HUD).
* **Integração:** Biblioteca **`pyswip`**
    * Atua como a ponte (bridge) que permite ao Python consultar o banco de dados e os predicados do Prolog em tempo real.

## 2. Funcionalidades

* **Lógica de Pathfinding em Prolog:** O predicado Prolog `shortest_path/7` recebe o estado do mundo e retorna o caminho mais curto e seguro.
* **Mundo Aleatório:** Cada clique em "Gerar Novo Grid" cria um novo mapa com posições aleatórias para o agente, objetivos, obstáculos e CTs.
* **IA Inimiga (CTs):** Os CTs são estáticos, mas projetam uma "zona de perigo" (representada por uma mira) nas 4 células adjacentes. O agente considera tanto o CT quanto suas zonas de perigo como letais.
* **Missão de Múltiplas Etapas:** O agente deve primeiro ir ao **Ponto A** (ex: pegar a bomba) e *depois* encontrar um novo caminho do Ponto A até o **Ponto B** (o bombsite final).
* **Animação do Agente:** Ao encontrar o caminho, o agente (Terrorista) percorre visualmente a rota calculada.
* **Mudança de Estado Dinâmica:**
    * Ao coletar o Ponto A, o item desaparece do mapa.
    * Após coletar o Ponto A, a velocidade de movimento do agente dobra.
* **Interface Gráfica (HUD):**
    * Botões para gerar um novo grid e para resolver o caminho.
    * Um **Visualizador de Passos** que mostra o progresso da animação (ex: "Passo: 5 / 20") ou o total de passos do caminho encontrado.
* **Assets Visuais Personalizados:** Todas as entidades (Agente, CT, Obstáculo, Miras, Chão, Bombas) são representadas por arquivos `.png` personalizados.

## 3. Como Funciona

A simulação é uma colaboração entre Python e Prolog:

1.  **Python (Pygame)**:
    * Gera o grid aleatório, posicionando o `Início` (T), `Ponto A`, `Ponto B`, `Obstáculos` e `CTs`.
    * Gerencia o loop do jogo, desenha os assets (chão, paredes, personagens) e o HUD.
    * Aguarda o clique no botão "Encontrar Caminho".

2.  **Integração (`pyswip`)**:
    * Ao clicar no botão, o Python formata o estado do mundo em uma consulta Prolog.
    * **Etapa 1:** Chama `shortest_path(Início, PontoA, ..., Caminho1)`.
    * **Etapa 2:** Se a Etapa 1 for bem-sucedida, chama `shortest_path(PontoA, PontoB, ..., Caminho2)`.

3.  **Backend (Prolog - `cs_path.pl`)**:
    * O predicado `shortest_path/7` recebe a consulta.
    * Ele usa `safe_cell/5` para determinar quais células são válidas (dentro dos limites, sem obstáculos, sem CTs e não adjacentes a CTs).
    * Ele executa uma Busca em Largura (BFS) para encontrar a lista de coordenadas do caminho mais curto.
    * O resultado (uma lista de coordenadas) é retornado ao Python.

4.  **Python (Animação)**:
    * O Python recebe a lista de caminho (combinando `Caminho1` e `Caminho2`).
    * Ele armazena o número total de passos para o HUD.
    * O loop `main` atualiza a posição do `agente_pos_atual` em intervalos de tempo (controlados por `VELOCIDADE_NORMAL` e `VELOCIDADE_RAPIDA`), animando o movimento.

## 4. Configuração e Instalação

Para rodar este projeto, você precisará do Python, Pygame, PySwip e, o mais importante, do **SWI-Prolog**.

1.  **Instale o SWI-Prolog:**
    * Faça o download no [site oficial do SWI-Prolog](https://www.swi-prolog.org/download/stable).
    * **Importante (Windows):** Durante a instalação, certifique-se de marcar a opção "Add swipl to the system PATH for all users". A biblioteca `pyswip` precisa disso para encontrar o Prolog.
    * **Importante (Linux/macOS):** Instale via gerenciador de pacotes (ex: `sudo apt install swi-prolog` ou `brew install swi-prolog`).

2.  **Clone ou baixe este repositório:**
    ```bash
    git clone https://github.com/HeitorPER/trbalhoIA
    cd trbalhoIA
    ```

3.  **Crie um Ambiente Virtual (Recomendado):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Em Linux/macOS
    .\venv\Scripts\activate   # Em Windows (PowerShell/CMD)
    ```

4.  **Instale as bibliotecas Python:**
    ```bash
    pip install pygame pyswip
    ```

## 5. Como Usar

1.  **Verifique os Arquivos:** Certifique-se de que todos os arquivos `.png` e o `cs_path.pl` estão na mesma pasta que o script Python (`gui_cs_pygame.py`), assim como na imagem da sua estrutura de arquivos.

2.  **Imagens PNG Necessárias:**
    * `chao.png` (lajota do chão)
    * `obstaculo.png` (caixa ou parede)
    * `terrorista.png` (agente)
    * `ct.png` (inimigo)
    * `crosshair.png` (mira para zona de perigo)
    * `bombsite_a.png` (Ponto A / Waypoint)
    * `bombsite_b.png` (Ponto B / Objetivo Final)

3.  **Execute o Script:**
    ```bash
    python ./versaoFuncionando1.py
    ```

4.  **Interaja com a Simulação:**
    * Clique em **"Gerar Novo Grid"** para criar um novo desafio aleatório.
    * Clique em **"Encontrar Caminho"** para o Prolog calcular a rota e o agente iniciar a animação.
