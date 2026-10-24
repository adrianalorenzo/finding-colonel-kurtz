from map import Environment
from knowledgeBase import KnowledgeBase
from search import bfs_path, cell_to_action, manhattan

"""Script principal donde  resolvemos el problema según el tipo que elijamos.
Caso A: manualmente con lógica
Caso B: con búsqueda A*/ BFS"""

movimiento_keys = {'W': 'UP', 'S': 'DOWN', 'A': 'LEFT', 'D': 'RIGHT'}
granada_keys = {'I': 'GRANADA_UP', 'K': 'GRANADA_DOWN', 'J': 'GRANADA_IZQ', 'L': 'GRANADA_DCHA' }
percept_nombres = ['Brisa', 'Ronquido', 'Resplandor', 'Pared↑', 'Pared↓', 'Pared←', 'Pared→', 'Grito']


def print_percept(percepcion):
    for name, val in zip(percept_nombres, percepcion):
        print(f"{name}: {val}")
        

#5.1 modo manual
def run_manual(n=6):
    env = Environment(n=n)
    kb = KnowledgeBase(n=n)

    #marcamos inicio
    kb.mark_visited(env.agente_pos)

    done = False
    turno = 0

    while not done: #mientras no hayamos teminado
        turno +=1 
        print("\n")
        print("________________________________________________")
        print(f"\nTurno: {turno}")
        print(f"Posición actual: {env.agente_pos}")

        #1.PErcibimos el entorno
        percepcion = env.get_percepciones()
        print(f"Percepción actual: {percepcion}")
        print_percept(percepcion)
        print(f"Tenemos a Kurtz: {env.tener_kurtz}")
        print(f"Granada disponible: {env.granada_disponible}")

        #2.Razonamos sobre él
        kb.update_with_percept(env.agente_pos, percepcion)

        #3.Mostramos el mapa conocido
        env.plantilla_conocida(kb)

        #modo opcional: mostrar los vecinos seguros sugeridos:
        print(f"Vecinos seguros no visitados: {kb.get_safe_unvisited_neighbors(env.agente_pos)}")

        #4.Pedimos una acción
        print("\nAcciones: WASD mover el agente ; IJKL lanzar la granada; E salir")
        if env.agente_pos == env.exit_pos and env.tener_kurtz:
            print("Estás en la salida con Kurtz. Pulsa E para salir y ganar")
        accion = input("Elige una acción: ").strip().upper()

        if accion == 'E':
            action = 'EXIT'
        elif accion in movimiento_keys:
            action = movimiento_keys[accion]
        elif accion in granada_keys:
            if not env.granada_disponible:
                print("Ya has usado la granada.")
            action = granada_keys[accion]
        else: 
            print("Acción no registrada")

        #5. Ejecutamos la acción
        done, info = env.step(action)
        if info.get('granada') is True:
            print("Has lanzado la granada y HAS MATADO al soldado")
        elif info.get('granada') is False:
            print("Has lanzado la granada y No has acertado, ya no tienes mas granadas")
        if info.get('dead', False):
            print("Has muerto. El mapa real del palacio era:")
            env.plantilla_truth()

        if info.get('win', False):
            print("¡HAs ganado! Has rescatado a Kurtz y encontrado la salida. Muy bien!")
            env.plantilla_truth()

#5.2: modo búsqueda
def choose_goal_safe_unvisited(env: Environment, kb: KnowledgeBase):
    """
    Función que elige una celda objetivo: segura y no visitada, priorizando la más cercana según la distancia Manhattan.
    """
    curr = env.agente_pos

    #priorizamos vecinos seguros no visitados
    local = kb.get_safe_unvisited_neighbors(curr)
    if local:
        return local[0]
    
    #si no hay vecinos, buscamos celdas seguras no visitadas globales
    candidatas = []
    for cell in kb.safe:
        if cell not in kb.visited:
            candidatas.append(cell) #agrupamos las seguras que no hayamos visitado aún

    #eliminamos peligros confirmados por seguridad
    candidatas_buenas = []
    for cell in candidatas:
        if (cell not in  kb.confirmed_precipicios and cell != kb.confirmed_soldier and cell not in kb.possible_soldier):
            candidatas_buenas.append(cell)
    
    if not candidatas_buenas:
        return None
    
    candidatas_buenas.sort(key= lambda c: manhattan(curr, c))
    return candidatas_buenas[0]

def run_search_bfs(n=6, max_pasos=500):
    #luego lo conectamos con BFS/A*
    env = Environment(n=n)
    kb = KnowledgeBase(n=n)
    kb.mark_visited(env.agente_pos)

    for turno in range(1, max_pasos+1):
        print(f"\nTurno BFS: {turno}")
        print(f"Posición actual: {env.agente_pos}")

        #1.PErcibimos el entorno
        percepcion = env.get_percepciones()
        print(f"Percepción actual: {percepcion}")
        print_percept(percepcion)
        print(f"Tenemos a Kurtz: {env.tener_kurtz}")

        #2.Razonamos sobre él
        kb.update_with_percept(env.agente_pos, percepcion)

        #3.Mostramos el mapa conocido
        env.plantilla_conocida(kb)

        #si tengo Kurtz y hay resplandor pruebo a salir
        if env.tener_kurtz and percepcion[2]:
            done_try, info_try = env.step('EXIT')
            if info_try.get('win', False):
                print("HAs ganado! Has salido correctamente")
                env.plantilla_truth()
                return
            
        #elegimos un objetivo seguro no visitado
        goal = choose_goal_safe_unvisited(env, kb)
        if goal is None:
            print("No hay celdas seguras no visitadas. Salimos sin arriesgar")
            env.plantilla_truth()
            return
        
        #Grafo: solo celdas seguras
        path = bfs_path(env.agente_pos, goal, kb)
        if path is None or len(path)<2:
            print(f"NO hay ruta segura conocida al objetivo: {goal}")
            env.plantilla_truth()
            return
        

        next_cell = path[1]
        action = cell_to_action(env.agente_pos, next_cell)
        print(f"Objetivo: {goal}; Accion: {action}")

        #vemos ahora posibles outcomes
        done, info = env.step(action)
        if info.get('dead', False):
            print("Has muerto. El mapa real del palacio era:")
            env.plantilla_truth()
            return
        if info.get('win', False):
            print("¡HAs ganado! Has rescatado a Kurtz y encontrado la salida. Muy bien!")
            env.plantilla_truth()
            return
    print("Max pasos alcanzados. MApa real: ")
    env.plantilla_truth()


if __name__ == "__main__":
    print("Elige cómo jugar: ")
    print("\nA) Manual, guiado por ti")
    print("B) BFS sobre celdas seguras")

    modo = input("A/B:  ").strip().upper()
    if modo == 'A':
        run_manual(n=6)
    else:
        run_search_bfs(n=6)
