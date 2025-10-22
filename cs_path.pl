% --- cs_path.pl ------------------------------------------------------------
% Encontra o caminho mais curto (BFS) em um grid com obstáculos
% e zonas letais adjacentes a CTs.

:- module(cs_path, [
    shortest_path/7   % +W,+H,+Start,+Goal,+Obstaculos,+CTs,-Caminho
]).

% ------------------------ API ---------------------------------------------

% shortest_path(+W,+H,+Start,+Goal,+Obstaculos,+CTs,-Caminho)
% W,H           : dimensões do grid (1..W, 1..H)
% Start, Goal   : posições X-Y
% Obstaculos    : lista de X-Y bloqueados
% CTs           : lista de X-Y com contraterroristas
% Caminho       : lista [Start, ..., Goal] (o mais curto)
shortest_path(W, H, Start, Goal, Obst, CTs, Caminho) :-
    safe_cell(Start, W, H, Obst, CTs),
    safe_cell(Goal,  W, H, Obst, CTs),
    bfs([[Start]], Goal, W, H, Obst, CTs, [Start], RevPath),
    reverse(RevPath, Caminho).

% --------------------- Busca em Largura (BFS) -----------------------------

bfs([[Goal|Resto]|_], Goal, _W, _H, _Obst, _CTs, _Visitados, [Goal|Resto]) :- !.
bfs([[Atual|Resto]|Fila], Goal, W, H, Obst, CTs, Visitados, Solucao) :-
    findall( Prox,
             vizinho_valido(Atual, Prox, W, H, Obst, CTs, Visitados),
             Proxs ),
    estende_caminhos([Atual|Resto], Proxs, NovosCaminhos),
    append(Fila, NovosCaminhos, Fila2),
    append(Proxs, Visitados, Visitados2),
    bfs(Fila2, Goal, W, H, Obst, CTs, Visitados2, Solucao).

estende_caminhos(_Caminho, [], []).
estende_caminhos(Caminho, [N|Ns], [[N|Caminho]|Out]) :-
    estende_caminhos(Caminho, Ns, Out).

vizinho_valido(Atual, Prox, W, H, Obst, CTs, Visitados) :-
    move(Atual, Prox),
    \+ memberchk(Prox, Visitados),
    safe_cell(Prox, W, H, Obst, CTs).

% --------------------- Regras de movimento e segurança --------------------

move(X-Y, X1-Y) :- X1 is X+1.
move(X-Y, X1-Y) :- X1 is X-1.
move(X-Y, X-Y1) :- Y1 is Y+1.
move(X-Y, X-Y1) :- Y1 is Y-1.

safe_cell(X-Y, W, H, Obst, CTs) :-
    within_bounds(X, Y, W, H),
    \+ memberchk(X-Y, Obst),
    \+ memberchk(X-Y, CTs),
    \+ adjacente_a_algum_ct(X-Y, CTs).

within_bounds(X, Y, W, H) :-
    between(1, W, X),
    between(1, H, Y).

adjacente_a_algum_ct(Pos, CTs) :-
    member(CT, CTs),
    adjacente(Pos, CT), !.

adjacente(X1-Y1, X2-Y2) :-
    DX is abs(X1 - X2),
    DY is abs(Y1 - Y2),
    S is DX + DY,
    S =:= 1.

% --------------------------------------------------------------------------
