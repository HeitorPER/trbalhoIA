import pygame
import random
from pyswip import Prolog
import ast  # Usado para parsear a string do Prolog

# --- Configurações Pygame ---
GRID_DIM = 20       # Dimensão do grid (20x20)
CELL_SIZE = 30      # Tamanho de cada célula em pixels
HUD_HEIGHT = 60     # Espaço no rodapé para botões

WIDTH = GRID_DIM * CELL_SIZE
HEIGHT = GRID_DIM * CELL_SIZE
SCREEN_HEIGHT = HEIGHT + HUD_HEIGHT

# Cores
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GRID = (200, 200, 200)
COLOR_START = (0, 255, 0)       # Terrorista (Verde)
COLOR_GOAL = (255, 0, 0)        # Bombsite (Vermelho)
COLOR_WAYPOINT = (255, 165, 0)  # ### MUDANÇA ### Ponto A (Laranja)
COLOR_OBSTACLE = (100, 100, 100) # Obstáculo (Cinza)
COLOR_CT = (0, 0, 255)          # CT (Azul)
COLOR_DANGER = (255, 255, 150)  # Zona de Perigo (Amarelo claro)
COLOR_PATH = (128, 0, 128)      # Caminho (Roxo)
COLOR_BUTTON = (50, 50, 50)
COLOR_BUTTON_TEXT = (255, 255, 255)

# --- Inicialização Prolog ---
try:
    prolog = Prolog()
    prolog.consult("cs_path.pl")
    print("Arquivo 'cs_path.pl' carregado com sucesso.")
except Exception as e:
    print(f"Erro ao carregar 'cs_path.pl': {e}")
    print("Certifique-se que o arquivo está no mesmo diretório e que o SWI-Prolog está instalado.")
    exit()

# --- Variáveis Globais do Grid ---
grid_width = GRID_DIM
grid_height = GRID_DIM
start_pos_pygame = (0, 0)  # (linha, coluna)
waypoint_pos_pygame = (0, 0) # ### MUDANÇA ### Ponto A
bombsite_pos_pygame = (0, 0) # ### MUDANÇA ### Ponto B (antigo goal_pos)
obstacles_pygame = []      # lista de (linha, coluna)
cts_pygame = []            # lista de (linha, coluna)
danger_zones = set()       # set de (linha, coluna) para desenho rápido
path_pygame = []           # lista de (linha, coluna)

def generate_random_grid(dim=GRID_DIM):
    """
    Gera um novo grid aleatório e preenche as variáveis globais.
    Usa coordenadas Pygame (linha, coluna) base 0.
    """
    ### MUDANÇA ### Atualizado para gerar 3 pontos únicos
    global grid_width, grid_height, start_pos_pygame, waypoint_pos_pygame, bombsite_pos_pygame, \
           obstacles_pygame, cts_pygame, path_pygame, danger_zones

    grid_width = dim
    grid_height = dim
    
    # Limpa dados antigos
    obstacles_pygame = []
    cts_pygame = []
    path_pygame = []
    danger_zones = set()

    # 1. Escolhe Início, Ponto A e Ponto B (garante que sejam únicos)
    start_pos_pygame = (random.randint(0, dim - 1), random.randint(0, dim - 1))
    
    while True:
        waypoint_pos_pygame = (random.randint(0, dim - 1), random.randint(0, dim - 1))
        if waypoint_pos_pygame != start_pos_pygame:
            break
            
    while True:
        bombsite_pos_pygame = (random.randint(0, dim - 1), random.randint(0, dim - 1))
        if bombsite_pos_pygame != start_pos_pygame and bombsite_pos_pygame != waypoint_pos_pygame:
            break
            
    # 2. Popula Obstáculos e CTs
    pontos_chave = {start_pos_pygame, waypoint_pos_pygame, bombsite_pos_pygame}
    for r in range(dim):
        for c in range(dim):
            pos = (r, c)
            if pos in pontos_chave: # Não pode ter obstáculo/CT nos pontos chave
                continue
            
            roll = random.random() # 0.0 a 1.0
            if roll < 0.20: # 20% de chance de ser obstáculo
                obstacles_pygame.append(pos)
            elif roll < 0.25: # 5% de chance de ser CT (total 25%)
                cts_pygame.append(pos)

    # 3. Calcula Zonas de Perigo (para visualização)
    for (r_ct, c_ct) in cts_pygame:
        # Posições adjacentes
        neighbors = [(r_ct - 1, c_ct), (r_ct + 1, c_ct), (r_ct, c_ct - 1), (r_ct, c_ct + 1)]
        for (r, c) in neighbors:
            # Adiciona se estiver dentro dos limites
            if 0 <= r < dim and 0 <= c < dim:
                danger_zones.add((r, c))

    print(f"Grid gerado: Início={start_pos_pygame}, PontoA={waypoint_pos_pygame}, Bombsite={bombsite_pos_pygame}")
    print(f"Obstáculos: {len(obstacles_pygame)}, CTs: {len(cts_pygame)}")

def _parse_prolog_path(prolog_path_list):
    """
    Função auxiliar para converter a lista de strings '-(X,Y)' do Prolog
    em uma lista de tuplas (r,c) do Pygame.
    """
    pygame_path = []
    for pos_atom in prolog_path_list:
        try:
            val_str = str(pos_atom)
            if val_str.startswith('-'):
                val_str = val_str[1:]
            
            pos_tuple = ast.literal_eval(val_str)
            x_pl, y_pl = pos_tuple[0], pos_tuple[1]
            
            r_pygame = y_pl - 1
            c_pygame = x_pl - 1
            pygame_path.append((r_pygame, c_pygame))
        except (ValueError, SyntaxError):
            print(f"Erro ao parsear a posição do Prolog: '{pos_atom}'")
    return pygame_path

def _run_prolog_query(start_pygame_pos, goal_pygame_pos):
    """
    Função auxiliar que executa uma única consulta de pathfinding no Prolog.
    Retorna uma lista de tuplas (r,c) do Pygame em caso de sucesso, ou None em caso de falha.
    """
    
    # 1. Traduzir Coordenadas (Python -> Prolog)
    w_pl = grid_width
    h_pl = grid_height
    start_pl = f"{start_pygame_pos[1] + 1}-{start_pygame_pos[0] + 1}"
    goal_pl = f"{goal_pygame_pos[1] + 1}-{goal_pygame_pos[0] + 1}"
    
    obstacles_pl = [f"{c+1}-{r+1}" for r, c in obstacles_pygame]
    cts_pl = [f"{c+1}-{r+1}" for r, c in cts_pygame]
    obstacles_pl_str = f"[{','.join(obstacles_pl)}]"
    cts_pl_str = f"[{','.join(cts_pl)}]"

    # 2. Construir e Executar a Consulta
    query = (
        f"shortest_path({w_pl}, {h_pl}, {start_pl}, {goal_pl}, "
        f"{obstacles_pl_str}, {cts_pl_str}, Caminho)"
    )
    
    try:
        solutions = list(prolog.query(query))
        if solutions:
            # 3. Traduzir Resultado
            prolog_path_data = solutions[0]['Caminho']
            return _parse_prolog_path(prolog_path_data) # Retorna o caminho [ (r,c), ... ]
        else:
            return None # Nenhum caminho encontrado
    except Exception as e:
        print(f"Erro ao executar consulta Prolog: {e}")
        if "safe_cell" in str(e):
            print("Verifique: Posição inicial ou final pode ser insegura.")
        return None # Falha na consulta

def solve_path():
    """
    ### MUDANÇA ###
    Encontra o caminho em duas etapas:
    1. De Início -> PontoA (Waypoint)
    2. De PontoA -> PontoB (Bombsite)
    """
    global path_pygame
    path_pygame = [] # Limpa o caminho anterior
    
    print("Consultando Prolog (Etapa 1: Início -> Ponto A)...")
    path1 = _run_prolog_query(start_pos_pygame, waypoint_pos_pygame)
    
    if not path1:
        print("Prolog: Nenhum caminho seguro encontrado para a Etapa 1 (Início -> Ponto A).")
        return # Para a execução se a primeira etapa falhar

    print(f"Etapa 1 encontrada. Consultando Prolog (Etapa 2: Ponto A -> Bombsite)...")
    path2 = _run_prolog_query(waypoint_pos_pygame, bombsite_pos_pygame)

    if not path2:
        print("Prolog: Nenhum caminho seguro encontrado para a Etapa 2 (Ponto A -> Bombsite).")
        return # Para a execução se a segunda etapa falhar

    # Sucesso! Combinar caminhos.
    # path2[1:] remove o primeiro elemento (o PontoA) para evitar
    # que o agente "pare" por um frame no PontoA (pois ele é o fim de path1 e o início de path2)
    path_pygame = path1 + path2[1:] 
    
    print(f"Caminho completo de duas etapas encontrado ({len(path_pygame)} passos).")

def draw_grid(screen):
    """Desenha o estado atual do grid."""
    
    for r in range(grid_height):
        for c in range(grid_width):
            pos = (r, c)
            rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            
            # Define a cor de fundo
            color = COLOR_WHITE
            if pos in danger_zones:
                color = COLOR_DANGER
            
            # Desenha o fundo
            pygame.draw.rect(screen, color, rect)
            
            # ### MUDANÇA ### Desenha os itens por cima (com PontoA)
            if pos == start_pos_pygame:
                color = COLOR_START
            elif pos == waypoint_pos_pygame: # Ponto A
                color = COLOR_WAYPOINT
            elif pos == bombsite_pos_pygame: # Ponto B
                color = COLOR_GOAL
            elif pos in obstacles_pygame:
                color = COLOR_OBSTACLE
            elif pos in cts_pygame:
                color = COLOR_CT
            
            # Redesenha se for um item (para sobrescrever o fundo)
            if color != COLOR_WHITE and color != COLOR_DANGER:
                 pygame.draw.rect(screen, color, rect)
            
            # Desenha a borda da célula
            pygame.draw.rect(screen, COLOR_GRID, rect, 1)

def draw_path(screen):
    """Desenha o caminho encontrado pelo Prolog."""
    if len(path_pygame) > 1:
        # Converte posições (r, c) em pixels no centro da célula
        points = []
        for (r, c) in path_pygame:
            x_pix = c * CELL_SIZE + CELL_SIZE // 2
            y_pix = r * CELL_SIZE + CELL_SIZE // 2
            points.append((x_pix, y_pix))
        
        # Desenha linhas conectando os pontos
        pygame.draw.lines(screen, COLOR_PATH, False, points, 4)

def draw_hud(screen, font):
    """Desenha os botões e retorna seus Rects para detecção de clique."""
    
    # Fundo do HUD
    hud_rect = pygame.Rect(0, HEIGHT, WIDTH, HUD_HEIGHT)
    pygame.draw.rect(screen, COLOR_BUTTON, hud_rect)

    # Botão "Gerar Novo Grid"
    btn_generate = pygame.Rect(10, HEIGHT + 10, 180, 40)
    pygame.draw.rect(screen, COLOR_GRID, btn_generate)
    text_gen = font.render("Gerar Novo Grid", True, COLOR_BLACK)
    text_gen_rect = text_gen.get_rect(center=btn_generate.center)
    screen.blit(text_gen, text_gen_rect)
    
    # Botão "Encontrar Caminho"
    btn_solve = pygame.Rect(200, HEIGHT + 10, 180, 40)
    pygame.draw.rect(screen, COLOR_GRID, btn_solve)
    text_solve = font.render("Encontrar Caminho", True, COLOR_BLACK)
    text_solve_rect = text_solve.get_rect(center=btn_solve.center)
    screen.blit(text_solve, text_solve_rect)
    
    return btn_generate, btn_solve

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("CS Pathfinding - Prolog + Pygame (Duas Etapas)")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)

    # Gera o primeiro grid
    generate_random_grid(GRID_DIM)

    running = True
    while running:
        # --- Processamento de Eventos ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Clique esquerdo
                    # Obtém os Rects dos botões (desenhando-os)
                    btn_gen_rect, btn_solve_rect = draw_hud(screen, font)
                    
                    if btn_gen_rect.collidepoint(event.pos):
                        print("Botão 'Gerar' clicado.")
                        generate_random_grid(GRID_DIM)
                    
                    elif btn_solve_rect.collidepoint(event.pos):
                        print("Botão 'Resolver' clicado.")
                        solve_path()

        # --- Lógica de Desenho ---
        screen.fill(COLOR_WHITE)
        
        draw_grid(screen)
        draw_path(screen)
        
        # Desenha o HUD por último (por cima de tudo)
        btn_gen_rect, btn_solve_rect = draw_hud(screen, font) # Retorna os Rects para o próximo loop

        pygame.display.flip()
        
        clock.tick(60) # Limita a 60 FPS

    pygame.quit()

if __name__ == "__main__":
    main()