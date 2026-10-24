

from palacio_bayes import PalacioBayes
"""Algoritmo de búsqueda para Part2 (palacio Bayes).
Usamos en este caso A*: que usa como coste el riesgo estimado por los mapas de Bayes
"""


def cell_to_action(cur, nxt):
    ci, cj = cur
    ni, nj = nxt
    if ni == ci -1 and nj == cj:
        return 'UP'
    if ni == ci+1 and nj == cj:
        return 'DOWN'
    if ni == ci and nj == cj-1:
        return 'LEFT'
    if ni == ci and nj == cj+1:
        return 'RIGHT'
    raise ValueError(f"Moviemiento no adyacente: {cur} -> {nxt}")

def manhattan(a,b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1]) #calculamos la distancia de manhattan


def risk_plantilla(bayes: PalacioBayes, soldado_vivo=True):
    """
    Función que devuelve una matriz risk[i][j] = min(1, P_trampa + P_soldado).
    Si el soldado está muerto, P_soldado se considera 0
    """
    n = bayes.n
    trampa = bayes.trampa_cualquiera()
    risk = bayes.make_grid(0.0)
    for i in range(n):
        for j in range(n):
            if soldado_vivo:
                pm = bayes.PM[i][j]
            else:
                pm = 0.0
            r = trampa[i][j] + pm
            if r > 1.0:
                r= 1.0 #nos aseguramos de no pasarnos
            risk[i][j] = r
    return risk

def a_path(start, goal, bayes: PalacioBayes, p_treshold, soldado_vivo=True, allow_goal_over_treshold=True):
    """
    algoritmo A* sobre celdas con riesgo < p_treshold
    -Coste g: 1 + alpha *riesgo(celda_destino)
    -Heurística h: manhattan al objetivo

    Contamos como hemos estudiado, que:
    f(n) = g(n) + h(n)
    """

    n = bayes.n
    risk = risk_plantilla(bayes, soldado_vivo=soldado_vivo)

    def allowed(cell):
        if cell == goal and allow_goal_over_treshold:
            return True
        return risk[cell[0]][cell[1]] < p_treshold
    
    open_list = [start]
    parent = {start:None}
    g = {start: 0.0} #definimos la funcion g desde 0, coste real acumulado desde el inicio hasta n
    f = {start: manhattan(start,goal)} #definimos f según la distancia de manhattan

    alpha = 5.0

    while open_list:
        current = min(open_list, key=lambda c: f.get(c, 1e9)) #para evitar KeyError si c no está en f
        open_list.remove(current)


        if current==goal:
            path = [current]
            while parent[path[-1]] is not None:
                path.append(parent[path[-1]])
            path.reverse()
            return path
        

        for vecino in bayes.vecinos(current):
            if not allowed(vecino):
                continue

            coste_paso = 1.0 + alpha * risk[vecino[0]][vecino[1]]
            posible = g[current] + coste_paso

            if vecino not in g or posible<g[vecino]:
                g[vecino] = posible
                parent[vecino] = current
                f[vecino] = posible + manhattan(vecino, goal)
                if vecino not in open_list:
                    open_list.append(vecino)

    return None

def best_neighbor_fallback(cur, bayes: PalacioBayes, soldado_vivo=True):
    """Devuelve el vecino (adyacente) con menor riesgo total"""   
    risk = risk_plantilla(bayes, soldado_vivo=soldado_vivo)

    best = None
    best_r = 1e9

    for vecino in bayes.vecinos(cur):
        r = risk[vecino[0]][vecino[1]]
        if r < best_r:
            best_r = r
            best = vecino
    return best
    
