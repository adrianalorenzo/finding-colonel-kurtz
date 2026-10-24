"""Script inspirado entorno del palacio para parte 2"""
import random


class Environment:


    def __init__(self, n=6):
        self.n = n

        #estado del agente 
        self.agente_pos = (0,0)
        self.tener_kurtz = False 

        #estado dinámico
        self.done = False
        self.soldado_vivo = True
        self.ultimo_grito = False #para percibir Grito solo en el turno siguiente
        self.granada_disponible = True

        #elementos del palacio
        self.fire_pos = None #F
        self.pinchos_pos = None #P
        self.dardos_pos = None #D
        self.enemy_pos  = None #M
        self.salida_pos = None #S
        self.kurtz_pos = None #CK
        

        self._generate_random_map()
    
    def _generate_random_map(self):
        """Función para colocar de manera aleatoria los elementos
        A diferencia de la parte 1, ahora:
        -F,P,D: pueden coincidir entre sí
        -M, S, CK: pueden coincidir entre sí
        """
        start = (0,0)
        all_cells = []

        #conjunto de celdas disponibles, todas menos start
        for i in range(self.n):
            for j in range(self.n):
                if (i,j) != start:
                    all_cells.append((i,j))

        #1. Trampas con remplazo, pueden coincidir
        self.fire_pos = random.choice(all_cells)
        self.pinchos_pos = random.choice(all_cells)
        self.dardos_pos = random.choice(all_cells)
        celdas_trampas = set([self.fire_pos, self.pinchos_pos, self.dardos_pos])
        
        celdas_seguras = [] #ahora contamos con el resto de celdas para S, CK, M
        for c in all_cells:
            if c not in celdas_trampas:
                celdas_seguras.append(c)
        
        if not celdas_seguras: #caso extremo, reintentamos
            return self._generate_random_map()
        
       
        self.enemy_pos = random.choice(celdas_seguras)   
        self.kurtz_pos = random.choice(celdas_seguras)
        self.salida_pos = random.choice(celdas_seguras) 
    
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
                else: 
                    parts = []
                    #trampas, pueden coincidir
                    if cell == self.fire_pos: #es uno de los precipicios:
                        parts.append('F')
                    if cell == self.pinchos_pos:
                        parts.append('P')
                    if cell == self.dardos_pos:
                        parts.append('D')

                    #M, S, CK pueden coincidir
                    if cell == self.enemy_pos:
                        parts.append('M' if self.soldado_vivo else 'm') #para indicar que esta muerto
                    if cell == self.kurtz_pos:
                        parts.append('CK')
                    if cell == self.salida_pos:
                        parts.append('S')
                    
                    symbol = ''.join(parts) if parts else '.'
                row.append(symbol)

            map.append(row)
        
        #imprimimos el mapa del palacio con coordenadas
        print("\nMAPA REAL DEL PALACIO:") 
        for i in range(self.n):
            for j in range(self.n):
                print(f"{map[i][j]} ({i},{j})", end="  ")   
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
        lista: [eF, eP, eD, eM, eS, Pared↑, Pared↓, Pared←, Pared→, Grito]
        """
        i, j = self.agente_pos

        #paredes
        par_u = (i == 0)
        par_d = (i == self.n -1)
        par_l = (j==0)
        par_r = (j == self.n -1)

        ady = self.get_adyacentes(self.agente_pos)
        zona = set(ady)
        zona.add(self.agente_pos)
        
        eF = (self.fire_pos in zona)
        eP = (self.pinchos_pos in zona)
        eD = (self.dardos_pos in zona)
        eM = (self.enemy_pos in zona )
        eS = (self.salida_pos in zona)

        
        #grito: solo inmediatamente después de matar con la granada
        grito = self.ultimo_grito
        self.ultimo_grito = False #se consume tras devolverlo

        return [eF, eP, eD, eM, eS, par_u, par_d, par_l, par_r, grito]
    
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
        elif action == 'GRANADA_IZQ' and j > 0:
            target = (i, j-1)
        elif action == 'GRANADA_DCHA' and j < self.n -1:
            target = (i, j+1)

        if target is None: #si tiramos contra la pared o target None, gastamos la granada igualmente
            return False
        
        if self.soldado_vivo and target == self.enemy_pos: #si le hemos lanzado correctamente al soldado
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

            #muerte por trampa o soldado
            if self.agente_pos in (self.fire_pos, self.pinchos_pos, self.dardos_pos): #si estamos en alguna trampa
                info['dead'] = True
                return True, info
            
            #muerte por soldado vivo
            if self.agente_pos == self.enemy_pos and self.soldado_vivo:
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
            if self.agente_pos == self.salida_pos and self.tener_kurtz: #si tenemos a Kurt y estamos en la salida
                info['win'] = True
                return True, info
            return False, info
        
        #cualquier otra acccion desconocida:
        return False, info
