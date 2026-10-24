from palacio_environment import Environment
from palacio_bayes import PalacioBayes
from palacio_search import a_path, cell_to_action, best_neighbor_fallback, risk_plantilla

"""Script principal donde  resolvemos el problema según el tipo que elijamos.
Caso A: manualmente con lógica
Caso B: con búsqueda A*/ BFS"""

movimiento_keys = {'W': 'UP', 'S': 'DOWN', 'A': 'LEFT', 'D': 'RIGHT'}
granada_keys = {'I': 'GRANADA_UP', 'K': 'GRANADA_DOWN', 'J': 'GRANADA_IZQ', 'L': 'GRANADA_DCHA' }
percept_nombres = ['eF', 'eP', 'eD', 'eM', 'eS', 'Pared↑', 'Pared↓', 'Pared←', 'Pared→', 'Grito']


def print_percept(percepcion):
    for name, val in zip(percept_nombres, percepcion):
        print(f"{name}: {val}")
        

#2.1 modo manual
def run_manual(n=6, debug_truth=True):
    env = Environment(n=n)
    bayes = PalacioBayes(n=n, start=(0,0))

    if debug_truth:
        env.plantilla_truth()

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

        #2.Razonamiento bayesiano: actualizamos las creencias
        bayes.update(env.agente_pos, percepcion=percepcion)

        #3.Mostramos los 3 mapas obligatorios
        bayes.print_required_maps(pos=env.agente_pos)

        #TEMPORAL
        print("MAPA REAL NO PARA EL JUGADOR:")
        env.plantilla_truth()

        #4.Pedimos una acción
        print("\nAcciones: WASD mover el agente ; IJKL lanzar la granada; E salir")
        if env.agente_pos == env.salida_pos and env.tener_kurtz:
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

        if not info.get('dead', False):
            bayes.descartar_celdas_visitadas_seguras(env.agente_pos)

        if info.get('granada') is True:
            print("Has lanzado la granada y HAS MATADO al soldado")
        elif info.get('granada') is False:
            print("Has lanzado la granada y No has acertado, ya no tienes mas granadas")
        
        if info.get('dead', False):
            print("Has muerto. El mapa real del palacio era:")
            env.plantilla_truth()
    

        elif info.get('win', False):
            print("¡HAs ganado! Has rescatado a Kurtz y encontrado la salida. Muy bien!")
            env.plantilla_truth()

#algoritmo de búsqueda
def run_auto_a(n=6, p=0.2, max_pasos=200):
    env = Environment(n=n)
    bayes = PalacioBayes(n=n, start=(0,0))

    visited = set()
    visited.add(env.agente_pos) #guardamos en visitadas al pos del agente

    done = False
    turno = 0

    while not done and turno < max_pasos:
        turno += 1
        print("\n")
        print("________________________________________________")
        print(f"\nTurno: {turno}")
        print(f"Posición actual: {env.agente_pos}")

        percepcion = env.get_percepciones()
        print(f"Percepción actual: {percepcion}")
        print_percept(percepcion)

        

        #actualizamos bayes y mostramos los mapas como siempre
        bayes.update(pos=env.agente_pos, percepcion=percepcion)
        bayes.print_required_maps(pos=env.agente_pos)

        #definimos objetivo, que será tener a kurtz y luego ir a la salida
        if env.tener_kurtz:
            goal, pv = argmax_cell(bayes.PS, n) #si ta lo tenemos, vamos a la salida
        else:
            risk = risk_plantilla(bayes=bayes, soldado_vivo=env.soldado_vivo)
            goal = None
            best_r = 1e9
            for i in range(n):
                for j in range(n):
                    cell = (i,j)
                    if cell == env.agente_pos:
                        continue
                    if cell in visited:
                        continue

                    r = risk[i][j]
                    #solo consideramos celdas bajo el umbral
                    if r >= p:
                        continue
                    if r < best_r:
                        best_r = r
                        goal = cell
            if goal is None: #si no hay ninguna celda bajo el umbral, intentamos ir a la salida
                goal, pv = argmax_cell(bayes.PS, n) 

        if goal == env.agente_pos:
            #si ya estamos donde creemos que esta la salida, intentamos salir
            done, info = env.step('EXIT')
            if info.get('win'):
                print("¡Has ganado! Has rescatado a Kurtz y encontrado la salida. Muy bien!")
                env.plantilla_truth()
                return
            #si no, nos movemos a un vecino
            nb = best_neighbor_fallback(env.agente_pos, bayes, soldado_vivo=env.soldado_vivo)
            action = cell_to_action(env.agente_pos, nb)

        else:
            path = a_path(env.agente_pos, goal=goal, bayes=bayes, p_treshold=p, soldado_vivo=env.soldado_vivo, allow_goal_over_treshold=False)
            if path is None or len(path) < 2:
                print("A* no tenemos una ruta bajo el umbral propuesto")
                nb = best_neighbor_fallback(env.agente_pos, bayes, soldado_vivo=env.soldado_vivo)
                action = cell_to_action(env.agente_pos, nb)
                
            else:
                print("A* path:", path[:6], "... " if len(path)> 6 else "")
                action = cell_to_action(env.agente_pos, path[1])
        
        print("Acción elegida:", action)
        done, info = env.step(action)

        visited.add(env.agente_pos)

        if done:
            if info.get("dead", False):
                print("\nHas muerto. Fin.")
                print("El mapa real del palacio era:")
                env.plantilla_truth()
            
            elif info.get("win", False):
                print("\n¡Has ganado! Has rescatado a Kurtz y encontrado la salida.")
                env.plantilla_truth()
            return

    if turno >= max_pasos:
        print("Corte por max_steps.")


def argmax_cell(P, n):
    best = (0,0) #partimos de lo mínimo
    best_val = -1.0
    for i in range(n): #recorremos todos los valores
        for j in range(n):
            if P[i][j] > best_val:
                best_val = P[i][j] #actualizamos el mejor valor si hay alguno mejor
                best = (i,j) #y su celda asociada
            
    return best, best_val



if __name__ == "__main__":
    print("Elige cómo jugar: ")
    print("\nA) Manual, guiado por ti")
    print("B) A* automático con umbral p= 0,2")

    modo = input("A/B:  ").strip().upper()
    if modo == 'A':
        run_manual(n=6, debug_truth=True)
    else:
        run_auto_a(n=6, p =0.2, max_pasos=200)
