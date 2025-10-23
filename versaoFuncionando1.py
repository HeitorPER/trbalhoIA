import pygame
import random
from pyswip import Prolog
import ast 
import os  

# --- Configurações Pygame ---
GRID_DIM = 20      # Altere para o tamnho desejado
CELL_SIZE = 40    # Tamanho de cada célula em pixels
HUD_HEIGHT = 60     # Espaço no rodapé para botões

WIDTH = GRID_DIM * CELL_SIZE
HEIGHT = GRID_DIM * CELL_SIZE
SCREEN_HEIGHT = HEIGHT + HUD_HEIGHT

# --- Configuração da Animação ---
VELOCIDADE_NORMAL = 150 
VELOCIDADE_RAPIDA = 75  

# Cores (usadas como fallback se as imagens falharem)
COLOR_WHITE = (255, 255, 255) 
COLOR_BLACK = (0, 0, 0)
COLOR_GRID = (200, 200, 200)
COLOR_START = (0, 255, 0)       
COLOR_GOAL = (255, 0, 0)        
COLOR_WAYPOINT = (255, 165, 0)  
COLOR_OBSTACLE = (100, 100, 100) 
COLOR_CT = (0, 0, 255)          
COLOR_DANGER = (255, 255, 150)  
COLOR_PATH = (128, 0, 128)      
COLOR_BUTTON = (50, 50, 50)
COLOR_BUTTON_TEXT = (255, 255, 255) 

# --- Função de Carregamento de Imagem ---

def carregar_imagem(filename, size):
    """
    Carrega um arquivo de imagem .png, converte (com transparência)
    e redimensiona para o tamanho da célula.
    """
    if not os.path.exists(filename):
        print(f"AVISO: Arquivo de imagem nao encontrado: '{filename}'")
        return None
    try:
        imagem = pygame.image.load(filename)
        imagem = imagem.convert_alpha()
        imagem_redimensionada = pygame.transform.scale(imagem, (size, size))
        return imagem_redimensionada
    except pygame.error as e:
        print(f"AVISO: Nao foi possivel carregar a imagem '{filename}'. Erro: {e}")
        return None

# --- Inicialização Prolog ---
try:
    prolog = Prolog()
    prolog.consult("cs_path.pl")
    print("Arquivo 'cs_path.pl' carregado com sucesso.")
except Exception as e:
    print(f"Erro ao carregar 'cs_path.pl': {e}")
    print("Certifique-se que o arquivo está no mesmo diretório e que o SWI-Prolog está instalado.")
    exit()

# --- Variáveis Globais ---
grid_width = GRID_DIM
grid_height = GRID_DIM
start_pos_pygame = (0, 0)  
waypoint_pos_pygame = (0, 0)
bombsite_pos_pygame = (0, 0)
obstacles_pygame = []
cts_pygame = []
danger_zones = set()
path_pygame = [] 

# --- Variáveis de Estado da Animação ---
agente_pos_atual = (0, 0)    
animando_caminho = False      
indice_caminho_atual = 0    
ultimo_movimento_tempo = 0  
ponto_a_coletado = False      
indice_ponto_a = -1
total_passos_caminho = 0 

# Variáveis globais para armazenar as superfícies (imagens) dos assets
ASSET_T = None
ASSET_CT = None 
ASSET_OBSTACLE = None
ASSET_BOMBSITE_A = None
ASSET_BOMBSITE_B = None
ASSET_CHAO = None
ASSET_CROSSHAIR = None 

def generate_random_grid(dim=GRID_DIM):
    """
    Gera um novo grid aleatório e preenche as variáveis globais.
    """
    global grid_width, grid_height, start_pos_pygame, waypoint_pos_pygame, bombsite_pos_pygame, \
           obstacles_pygame, cts_pygame, path_pygame, danger_zones, \
           agente_pos_atual, animando_caminho, indice_caminho_atual, \
           ponto_a_coletado, indice_ponto_a, total_passos_caminho 

    grid_width = dim
    grid_height = dim
    
    obstacles_pygame = []
    cts_pygame = []
    path_pygame = []
    danger_zones = set()

    # 1. Escolhe Início, Ponto A e Ponto B
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
            if pos in pontos_chave:
                continue
            roll = random.random()
            if roll < 0.20:
                obstacles_pygame.append(pos)
            elif roll < 0.25:
                cts_pygame.append(pos)

    # 3. Calcula Zonas de Perigo (APENAS adjacentes)
    danger_zones_temp = set()
    for (r_ct, c_ct) in cts_pygame:
        neighbors = [(r_ct - 1, c_ct), (r_ct + 1, c_ct), (r_ct, c_ct - 1), (r_ct, c_ct + 1)]
        for (r, c) in neighbors:
            if 0 <= r < dim and 0 <= c < dim:
                danger_zones_temp.add((r, c))
    
    danger_zones = {pos for pos in danger_zones_temp if pos not in cts_pygame and pos not in obstacles_pygame}

    # --- Resetar estado da animação e missão ---
    agente_pos_atual = start_pos_pygame
    animando_caminho = False
    indice_caminho_atual = 0
    ponto_a_coletado = False
    indice_ponto_a = -1
    total_passos_caminho = 0 


    print(f"Grid gerado: Início={start_pos_pygame}, PontoA={waypoint_pos_pygame}, Bombsite={bombsite_pos_pygame}")
    print(f"Obstáculos: {len(obstacles_pygame)}, CTs: {len(cts_pygame)}")

def _parse_prolog_path(prolog_path_list):
    """Converte a lista de strings '-(X,Y)' do Prolog para tuplas (r,c) do Pygame."""
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
    """Executa uma única consulta de pathfinding no Prolog."""
    
    w_pl = grid_width
    h_pl = grid_height
    start_pl = f"{start_pygame_pos[1] + 1}-{start_pygame_pos[0] + 1}"
    goal_pl = f"{goal_pygame_pos[1] + 1}-{goal_pygame_pos[0] + 1}"
    
    obstacles_pl = [f"{c+1}-{r+1}" for r, c in obstacles_pygame]
    cts_pl = [f"{c+1}-{r+1}" for r, c in cts_pygame]
    obstacles_pl_str = f"[{','.join(obstacles_pl)}]"
    cts_pl_str = f"[{','.join(cts_pl)}]"

    query = (
        f"shortest_path({w_pl}, {h_pl}, {start_pl}, {goal_pl}, "
        f"{obstacles_pl_str}, {cts_pl_str}, Caminho)"
    )
    
    try:
        solutions = list(prolog.query(query))
        if solutions:
            prolog_path_data = solutions[0]['Caminho']
            return _parse_prolog_path(prolog_path_data)
        else:
            return None
    except Exception as e:
        print(f"Erro ao executar consulta Prolog: {e}")
        if "safe_cell" in str(e):
            print("Verifique: Posição inicial ou final pode ser insegura.")
        return None

def solve_path():
    """
    Encontra o caminho em duas etapas e INICIA a animação.
    """
    global path_pygame, agente_pos_atual, animando_caminho, indice_caminho_atual, ultimo_movimento_tempo, \
           ponto_a_coletado, indice_ponto_a, total_passos_caminho 
    
    path_pygame = []
    agente_pos_atual = start_pos_pygame
    animando_caminho = False
    indice_caminho_atual = 0
    ponto_a_coletado = False
    indice_ponto_a = -1
    total_passos_caminho = 0 
    
    print("Consultando Prolog (Etapa 1: Início -> Ponto A)...")
    path1 = _run_prolog_query(start_pos_pygame, waypoint_pos_pygame)
    
    if not path1:
        print("Prolog: Nenhum caminho seguro encontrado para a Etapa 1 (Início -> Ponto A).")
        return
    
    indice_ponto_a = len(path1) - 1

    print(f"Etapa 1 encontrada. Consultando Prolog (Etapa 2: Ponto A -> Bombsite)...")
    path2 = _run_prolog_query(waypoint_pos_pygame, bombsite_pos_pygame)

    if not path2:
        print("Prolog: Nenhum caminho seguro encontrado para a Etapa 2 (Ponto A -> Bombsite).")
        return

    path_pygame = path1 + path2[1:] 
    
    if path_pygame:   
        total_passos_caminho = len(path_pygame) - 1 
        animando_caminho = True
        ultimo_movimento_tempo = pygame.time.get_ticks()
        print(f"Caminho completo encontrado. Iniciando animação ({total_passos_caminho} passos).")

def draw_grid(screen):
    """
    Desenha o grid e todos os itens ESTÁTICOS (sem o agente).
    """
    global ASSET_T, ASSET_CT, ASSET_CROSSHAIR, ASSET_OBSTACLE, ASSET_BOMBSITE_A, ASSET_BOMBSITE_B, ASSET_CHAO, \
           ponto_a_coletado

    for r in range(grid_height):
        for c in range(grid_width):
            pos = (r, c)
            rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            
            # 1. Desenha o chão primeiro
            if ASSET_CHAO:
                screen.blit(ASSET_CHAO, rect)
            else: 
                pygame.draw.rect(screen, COLOR_WHITE, rect)
            
            # 2. Desenha os assets estáticos por CIMA do chão
            asset_para_desenhar = None
            fallback_color = None

            if pos == waypoint_pos_pygame and not ponto_a_coletado: 
                asset_para_desenhar = ASSET_BOMBSITE_A
                fallback_color = COLOR_WAYPOINT
            elif pos == bombsite_pos_pygame: 
                asset_para_desenhar = ASSET_BOMBSITE_B
                fallback_color = COLOR_GOAL
            elif pos in obstacles_pygame:
                asset_para_desenhar = ASSET_OBSTACLE
                fallback_color = COLOR_OBSTACLE
            
            # --- CT no centro, mira ao redor ---
            elif pos in cts_pygame:
                asset_para_desenhar = ASSET_CT      
                fallback_color = COLOR_CT
            elif pos in danger_zones:
                asset_para_desenhar = ASSET_CROSSHAIR 
                fallback_color = COLOR_DANGER

            if asset_para_desenhar:
                screen.blit(asset_para_desenhar, rect)
            elif fallback_color:
                pygame.draw.rect(screen, fallback_color, rect)



def draw_path(screen):
    """
    Desenha a linha do caminho completo (para o agente seguir).
    """
    if len(path_pygame) > 1:
        points = []
        for (r, c) in path_pygame:
            x_pix = c * CELL_SIZE + CELL_SIZE // 2
            y_pix = r * CELL_SIZE + CELL_SIZE // 2
            points.append((x_pix, y_pix))
        pygame.draw.lines(screen, COLOR_PATH, False, points, 4)

def draw_hud(screen, font):
    """Desenha os botões e o visualizador de passos."""
    
    global total_passos_caminho, indice_caminho_atual, animando_caminho 

    hud_rect = pygame.Rect(0, HEIGHT, WIDTH, HUD_HEIGHT)
    pygame.draw.rect(screen, COLOR_BUTTON, hud_rect)

    # --- Botões (Esquerda) ---
    btn_generate = pygame.Rect(10, HEIGHT + 10, 180, 40)
    pygame.draw.rect(screen, COLOR_GRID, btn_generate)
    text_gen = font.render("Gerar Novo Grid", True, COLOR_BLACK)
    text_gen_rect = text_gen.get_rect(center=btn_generate.center)
    screen.blit(text_gen, text_gen_rect)
    
    btn_solve = pygame.Rect(200, HEIGHT + 10, 180, 40)
    pygame.draw.rect(screen, COLOR_GRID, btn_solve)
    text_solve = font.render("Encontrar Caminho", True, COLOR_BLACK)
    text_solve_rect = text_solve.get_rect(center=btn_solve.center)
    screen.blit(text_solve, text_solve_rect)
    
    # Visualizador de Passos (Direita)  ---
    texto_passos_str = ""
    if animando_caminho:
        texto_passos_str = f"Passo: {indice_caminho_atual + 1} / {total_passos_caminho}"
    elif total_passos_caminho > 0:
        texto_passos_str = f"Total: {total_passos_caminho} Passos"
    else:
        texto_passos_str = "Passos: --"
        
    # Renderiza o texto
    texto_passos_surf = font.render(texto_passos_str, True, COLOR_BUTTON_TEXT) 
    texto_passos_rect = texto_passos_surf.get_rect(midright=(WIDTH - 20, HEIGHT + (HUD_HEIGHT // 2)))
    screen.blit(texto_passos_surf, texto_passos_rect)
    
    return btn_generate, btn_solve

def main():
    global ASSET_T, ASSET_CT, ASSET_OBSTACLE, ASSET_BOMBSITE_A, ASSET_BOMBSITE_B, ASSET_CHAO, \
           ASSET_CROSSHAIR 
    # ### MUDANÇA: Adiciona total_passos_caminho ###
    global agente_pos_atual, animando_caminho, indice_caminho_atual, ultimo_movimento_tempo, \
           ponto_a_coletado, indice_ponto_a, total_passos_caminho

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("CS Pathfinding - CTs e Miras")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)

    # --- Carregar assets PNG ---
    print("Carregando imagens PNG...")
    ASSET_T = carregar_imagem("terrorista.png", CELL_SIZE)
    ASSET_OBSTACLE = carregar_imagem("obstaculo.png", CELL_SIZE)
    ASSET_BOMBSITE_A = carregar_imagem("bombsite_a.png", CELL_SIZE)
    ASSET_BOMBSITE_B = carregar_imagem("bombsite_b.png", CELL_SIZE)
    ASSET_CHAO = carregar_imagem("chao.png", CELL_SIZE)
    ASSET_CROSSHAIR = carregar_imagem("crosshair.png", CELL_SIZE)
    ASSET_CT = carregar_imagem("ct.png", CELL_SIZE) 
    print("-------------------------------------------------")
    
    generate_random_grid(GRID_DIM)

    running = True
    while running:
        # --- Processamento de Eventos ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: 
                    if not animando_caminho:
                        btn_gen_rect, btn_solve_rect = draw_hud(screen, font)
                        
                        if btn_gen_rect.collidepoint(event.pos):
                            print("Botão 'Gerar' clicado.")
                            generate_random_grid(GRID_DIM)
                        
                        elif btn_solve_rect.collidepoint(event.pos):
                            print("Botão 'Resolver' clicado.")
                            solve_path() 

        # --- Lógica de Animação e Velocidade ---
        if animando_caminho:
            
            velocidade_atual = VELOCIDADE_NORMAL
            if ponto_a_coletado: 
                velocidade_atual = VELOCIDADE_RAPIDA
                
            agora = pygame.time.get_ticks()
            
            if agora - ultimo_movimento_tempo > velocidade_atual:
                ultimo_movimento_tempo = agora 
                
                if indice_caminho_atual < len(path_pygame) - 1:
                    indice_caminho_atual += 1
                    agente_pos_atual = path_pygame[indice_caminho_atual]

                    if indice_caminho_atual == indice_ponto_a:
                        if not ponto_a_coletado: 
                            print("Ponto A coletado! Aumentando velocidade.")
                            ponto_a_coletado = True
                else:
                    animando_caminho = False
                    print("Animação concluída.")


        # --- Lógica de Desenho ---
        screen.fill(COLOR_WHITE) 
        
        # 1. Desenha o grid estático (chão, cts, miras, bombas, obstáculos)
        draw_grid(screen) 
        
        # 2. Desenha a linha do caminho (se houver)
        draw_path(screen)
        
        # 3. Desenha o agente na sua posição ATUAL
        agente_rect = pygame.Rect(agente_pos_atual[1] * CELL_SIZE, agente_pos_atual[0] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        if ASSET_T:
            screen.blit(ASSET_T, agente_rect)
        else:
            pygame.draw.rect(screen, COLOR_START, agente_rect) 
        
        # 4. Desenha o HUD (botões e contador de passos)
        draw_hud(screen, font)

        pygame.display.flip()
        
        clock.tick(60) 

    pygame.quit()

if __name__ == "__main__":
    main()