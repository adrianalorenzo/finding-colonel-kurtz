#utilidades de búsqueda
def bfs_path(start, goal, kb):
    """Devuelve path como lista de celdas usando BFS.
    neighbors_fn (cell) -> lista de vecinos transitables.
    """
    if start == goal:
        return [start]
    
    queue = [start] #cola FIFO
    parent = {start: None} #para reconstruir el camino
    while queue:
        current = queue.pop(0) #sacamos el primero

        #vecinos seguros según la kb
        vecinos = kb.get_safe_neighbors(current)
        
        for nb in vecinos: 
            if nb not in parent:
                parent[nb] = current

                if nb == goal:
                    #reconstruimos el camino
                    path = [goal]
                    while parent[path[-1]] is not None:
                        path.append(parent[path[-1]])
                    path.reverse() #hacia atrás
                    return path   
                queue.append(nb)
    return None #si no hay camino seguro, devuelve None
                    

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
