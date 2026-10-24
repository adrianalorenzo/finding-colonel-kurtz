
#importamos nuestra base de conocimiento
from knowledgeBase import KnowledgeBase
import random




#definimos las acciones que vamos a poder realizar
actions = ['up', 'down', 'izq', 'dcha', 'granada_up', 'granada_down', 'granada_izqda', 'granada_dcha', 'salir']


#creamos el tablero nxn
class Environment:
    """Clase donde de forma aleatoria se colocan los precipicios, el soldado y Kurtz en cada iteración.
    Todoo en una cuadrícula nxn que en este caso será en una 6x6. """
    def __init__(self, n=6):
        self.n = n

        #estado del agente
        self.agente_pos = (0,0) #empezamos en el 0,0
        self.tener_kurtz = False #creamos una flag apra saber cuadno hemos encontrado a Kurtz

        #estado dinámico
        self.soldado_vivo = True
        self.ultimo_grito = False #para percibir Grito solo en el turno siguiente
        self.granada_disponible = True

        #generación aleatoria del mapa
        self.pits = set() #posiciones de los precipicios
        self.soldier_pos = None
        self.kurtz_pos = None
        self.exit_pos = None

        self._generate_random_map()
    
    def _generate_random_map(self):
        """Función para colocar de manera aleatoria los elementos
        """
        start = (0,0)
        all_cells = []

        #conjunto de celdas disponibles, todas menos start
        for i in range(self.n):
            for j in range(self.n):
                if (i,j) != start:
                    all_cells.append((i,j))
        
        random.shuffle(all_cells) #'barajeamos' (ponemos de forma aleatoria) las celdas para asignarlas a cada elemento de forma aleatoria

        #3 precipicios
        self.pits = set(all_cells[:3]) #cogemos los 3 primeros de esa lista aleatoria
        idx = 3 #los siguientes elementos ahora van a tener que empezar en las siguientes a esas (para que solo haya un elemento por celda)

        #soldado 
        while all_cells[idx] in self.pits: 
            idx +=1 #avanzamos hasta la siguiente celda libre
        self.soldier_pos = all_cells[idx] #asignamos celda al soldado
        idx +=1

        #kurtz
        while all_cells[idx] in self.pits or all_cells[idx] == self.soldier_pos:
            idx += 1 #avanzamos hasta la siguiente celda libre     
        self.kurtz_pos = all_cells[idx] #asignamos celda a kurtz

        #salida
        while all_cells[idx] in self.pits or all_cells[idx] == self.soldier_pos or all_cells[idx] == self.kurtz_pos:
            idx += 1 #avanzamos hasta la siguiente celda libre  
        self.exit_pos = all_cells[idx] #asignamos celda a la salida
    
    def plantilla_truth(self):
        """Función que imprime el mapa REAL (solo para saberlo).
        Vamos a definir los símbolos de cada elemento y asegurarnos de que en el tablero se imprime
        la coordeanda de la celda, y el símbolo si tiene.
        """

        map = [] #matriz de símbolos

        for i in range(self.n):
            row = []
            for j in range(self.n):
                cell = (i,j) #definimos una celda
                #definimos cada símbolo
                if cell == self.agente_pos:
                    symbol = 'A'
                elif cell in self.pits: #es uno de los precipicios:
                    symbol = 'P'
                elif self.soldado_vivo and cell == self.soldier_pos:
                    symbol = 'S'
                elif cell == self.kurtz_pos:
                    symbol = 'K'
                elif cell == self.exit_pos:
                    symbol = 'E'
                else:
                    symbol = '.'
                row.append(symbol)

            map.append(row)
        
        #imprimimos el mapa del palacio con coordenadas
        print("\nMAPA REAL DEL PALACIO:") 
        for i in range(self.n):
            for j in range(self.n):
                print(f"{map[i][j]} ({i},{j})", end="  ")   
            print()
        
    def plantilla_conocida (self, kb):
        """Función que imprime el mapa según lo que sabe la KB (modo juego literal).
        No muestra el mapa real; solo: 
        -la pos del agente
        -las celdas visitadas
        -las celdas seguras
        -posibles peligros
        -peligros confirmados
        """
        mapa = []
        for i in range(self.n):
            row = []
            for j in range(self.n):
                cell = (i,j)

                if cell == self.agente_pos:
                    symbol = 'A'
                elif cell in kb.confirmed_precipicios:
                    symbol = 'P!'
                elif kb.confirmed_soldier == cell:
                    symbol = 'S!'
                elif cell in kb.visited:
                    symbol = 'VIS'
                elif cell in kb.safe:
                    symbol = 's' #segura que hemos deducido, pero no visitado
                elif (cell in kb.possible_precipicios) or (cell in kb.possible_soldier):
                    symbol = '?' #posible peligro
                else:
                    symbol = '.' 
                row.append(symbol)
            mapa.append(row)

        print("\nMAPA CONOCIDO (según KB):")
        for i in range(self.n):
            for j in range(self.n):
                print(f"{mapa[i][j]} ({i}, {j})", end="  ")
            print()

    
    def get_adyacentes(self, cell):
        """Función qu devuelve los vecinos válidos (con dist de Manhattan =1) dentro del tablero.
        """
        i, j = cell
        ady = []
        if i > 0: 
            ady.append((i-1, j))
        if i < self.n -1:
            ady.append((i+1, j))
        if j >0:
            ady.append((i, j-1))
        if j < self.n -1:
            ady.append((i, j+1))
        return ady

    def get_percepciones(self):
        """Devuelve la percepción según la celda donde estemos cerca.
        lista: [Brisa, Ronquido, Resplandor, Pared↑, Pared↓, Pared←, Pared→, Grito]"""
        i, j = self.agente_pos

        #paredes
        par_u = (i == 0)
        par_d = (i == self.n -1)
        par_l = (j==0)
        par_r = (j == self.n -1)

        ady = self.get_adyacentes(self.agente_pos)

        #brisa: hay precipicio en alguna adyacente
        brisa = any(c in self.pits for c in ady)

        #ronquido, indica que hay soldado vivo en alguna adyacente
        ronq = self.soldado_vivo and (self.soldier_pos in ady)

        #resplandor, estamos en salida o adyacente a salida
        respl = (self.agente_pos == self.exit_pos) or (self.exit_pos in ady)

        #grito: solo inmediatamente después de matar con la granada
        grito = self.ultimo_grito
        self.ultimo_grito = False #se consume tras devolverlo

        return [brisa, ronq, respl, par_u, par_d, par_l, par_r, grito]
    
    def _move(self, direction):
        """Función que intenta mover al agente; si hay pared, no se mueve.
        """
        i, j = self.agente_pos
        ni, nj = i,j

        if direction == 'UP':
            ni -= 1
        elif direction == 'DOWN':
            ni += 1
        elif direction == 'LEFT':
            nj -=1
        elif direction == 'RIGHT':
            nj +=1
        else:
            return #direccion inválida, no hacemos nada
        
        if 0 <= ni < self.n and 0 <= nj < self.n:
            self.agente_pos = (ni, nj)

    def lanzar_granada (self, action):
        """Lanza la granada una celda en la dirección indicada.
        Si acierta al soldado y está vivo, lo elimina y activa último_grito.
        """
        if not self.granada_disponible:
            return None #no se lanzó
        
        self.granada_disponible = False

        i, j = self.agente_pos 
        target = None #en principio no hay objetivo para lanzarla

        if action == 'GRANADA_UP' and i > 0:
            target = (i-1, j)
        elif action == 'GRANADA_DOWN' and i < self.n -1:
            target = (i+1, j)
        if action == 'GRANADA_IZQ' and j > 0:
            target = (i, j-1)
        if action == 'GRANADA_DCHA' and j < self.n -1:
            target = (i, j+1)

        if target is None: #si tiramos contra la pared o target None, gastamos la granada igualmente
            return False
        
        if self.soldado_vivo and target == self.soldier_pos: #si le hemos lanzado correctamente al soldado
            self.soldado_vivo = False #matamos al soldado
            self.ultimo_grito = True
            return True #acierto
        
        return False #falló

    
    def step(self, action):
        """Función que ejecuta una acción y devuelve algo tipo: (done, info).
        Donde la info puede ser: {'muerto': bool, 'win': bool}
        """

        info = {'dead': False, 'win': False, 'granada': None}

        #los movimientos
        if action in ('UP', 'DOWN', 'LEFT', 'RIGHT'):
            self._move(action)

            #muerte por precipicio
            if self.agente_pos in self.pits: #si estamos en algún precipicio
                info['dead'] = True
                return True, info
            
            #muerte por soldado vivo
            if self.agente_pos == self.soldier_pos and self.soldado_vivo:
                info['dead'] = True
                return True, info
            
            #encontrar a Kurtz automáticamente al entrar
            if self.agente_pos == self.kurtz_pos:
                self.tener_kurtz = True #marcamos que lo tenemos

            return False, info
        
        #si lanzamos la granada
        if action in ('GRANADA_UP', 'GRANADA_DOWN', 'GRANADA_IZQ', 'GRANADA_DCHA'):
            hit = self.lanzar_granada(action) #lanzamos la granada
            info['granada'] = hit
            return False, info
        
        #salir del juego
        if action == 'EXIT':
            if self.agente_pos == self.exit_pos and self.tener_kurtz: #si tenemos a Kurt y estamos en la salida
                info['win'] = True
                return True, info
            return False, info
        
        #cualquier otra acccion desconocida:
        return False, info

#funciones auxiliares extras para probar el correcto funcionamiento del fichero en particular 
def probar_mapa_real():
    env = Environment(n=6)
    kb = KnowledgeBase(n=6)

    #para que muestre algo, marcamos la celda inicial como visitada/segura
    kb.mark_visited(env.agente_pos)

    #mostramos el mapa REAL
    env.plantilla_truth()
    print("\n")
    print("__________________________________________")
    print("\n")
    #mostramos el mapa según la KB
    env.plantilla_conocida(kb)


def test_perceptos():
    env = Environment(n=6)
    print("Agente:", env.agente_pos)
    env.plantilla_truth()
    print("Percepto inicial:", env.get_percepciones())

    #probar mover 2 pasos a la derecha si se puede
    done, info = env.step("RIGHT")
    print("Moved RIGHT:", env.agente_pos, "done/info:", done, info, "percept:", env.get_percepciones())
    done, info = env.step("RIGHT")
    print("Moved RIGHT:", env.agente_pos, "done/info:", done, info, "percept:", env.get_percepciones())

if __name__ == "__main__":
    #probar_mapa_real()

    test_perceptos()

