
#base de conocimiento
class KnowledgeBase:
    def __init__ (self, n=6):
        self.n = n
        #conocimiento cierto  
        self.visited = set() #celdas visitadas
        self.safe = set() #celdas seguras confirmadas
        self.confirmed_precipicios = set() #celdas donde hay precipicios seguro
        self.confirmed_soldier = None #celda real del soldado
        #conocimiento posible:
        self.possible_precipicios = set() #celdas donde podría haber precipicios
        self.possible_soldier = set() #celdas donde podría estar el soldado
        
        #estado especial
        self.kurtz_encontrado = False
        self.salida_encontrada = False

        #constraintsa adicionales para deducción por descarte
        self.brisa_constraints = {} 
        self.sold_constraints = {}

    
    def update_with_percept(self, position, percept):
        """Función principal que va analizando la lógica de cada celda y actualizando su estado (a visitada/segura)
        Argumentos:
        -position: (i,j) posición actual del Capitán
        -percept: lista [Brisa, Ronquido, Resplandor, Pared↑, Pared↓, Pared←, Pared→, Grito]
        """
        #definimos cada percepción recibida
        brisa, ronq, respl, par_u, par_d, par_l, par_r, grito = percept

        #marcamos la celda como vistada y segura
        self.mark_visited(position)

        #calculamos las adyacentes:
        ady = self.get_celdas_adyacentes(position)

        #si NO hay brisa, entonces ningún vecino es precipicio
        if not brisa:
            for c in ady:
                #la sacamos del set de posible precipicio
                if c in self.possible_precipicios:
                    self.possible_precipicios.remove(c)

                #si además no es posible soldado, la marcamos segura
                if (not ronq)  and (c != self.confirmed_soldier) and (c not in self.confirmed_precipicios):
                    self.safe.add(c) #la añadimos al set de seguras

        #si SÍ hay brisa, algun vecino tiene precipicio
        else:
            candidatos = set()
            for c in ady:
                #solo tiene sentido si aún no sabemos que es segura/no precipicio
                if (c not in self.safe) and (c not in self.confirmed_precipicios):
                    candidatos.add(c)
                    self.possible_precipicios.add(c)
            self.brisa_constraints[position] = candidatos #añadimos el set como valor asociado a la posicion dada


        #si NO hay ronquido, entonces ningún vecino tiene al soldado
        if not ronq:
            for c in ady:
                #la sacamos del set de posible soldado
                if c in self.possible_soldier:
                    self.possible_soldier.remove(c)
                #si además no es posible precipicio, la marcamos como segura
                if (c not in self.possible_precipicios) and (c not in self.confirmed_precipicios):
                    self.safe.add(c) #la añadimos al set de seguras

        #si SÍ hay ronquido, entonces algún vecino tiene que tener al soldado
        else:
            candidatos = set()
            for c in ady:
                #solo tiene sentido si aún no sabemos que es segura/no soldado
                if (c not in self.safe) and (self.confirmed_soldier != c):
                    candidatos.add(c)
                    self.possible_soldier.add(c)
            self.sold_constraints[position] = candidatos #añadimos el set como valor asociado a la posicion dada

        #si hay un resplandor, estamos en salida o en adyacente
        if respl:
            self.salida_encontrada = True

        #si hay un grito, el soldado se eliminó (acertamos con la granada)
        if grito:
            self.confirmed_soldier = None #lo eliminamos
            self.possible_soldier.clear() #vaciamos el set de posibles soldados
            self.sold_constraints.clear() #vaciamos el dicc

        #inferencias por descarte (después de actualizar todo), llamamos a las funciones de inferencia designadas
        self.infer_precipicios()
        self.infer_soldado() 




    def get_celdas_adyacentes(self, position):
        """Función que devuelve la lista de adyacentes válidas dentro del map.
        Argumentos:
        -position: (i,j) posición actual del Capitán
        """
        i, j = position
        adyacentes = [] #creamos la lista de adyacentes a devolver

        posibles = [(i-1, j), #arriba
                     (i+1, j), #abajo 
                     (i,j-1), #izq
                     (i, j+1) #dcha
            ] 
        
        for (x,y) in posibles:
            if 0 <= x < self.n and 0<=y <self.n: #si estamos dentro de la cuadrícula
                adyacentes.append((x,y))
        
        return adyacentes

    def mark_safe(self, cell):
        """Función que marca una celda como segura. La elimina de posibles precipicios/posible soldado.
        Argumentos:
        -cell: (i,j) coordenadas de la celda que estamos tratando.
        """
        self.safe.add(cell)
        
        if cell in self.possible_precipicios: #si era un posible precipicio
            self.possible_precipicios.remove(cell) #la eliminamos del set
            
        if cell in self.possible_soldier: #si era una posible celda que contenía al soldado
            self.possible_soldier.remove(cell) #la eliminamos del set


    def mark_visited(self, cell):
        """Función que marca una celda como visitada. Automáticamente se vuelve segura
        -cell: (i,j) coordenadas de la celda que estamos tratando.
        """
        self.visited.add(cell) #la añadimos al set de celdas visitadas
        self.mark_safe(cell) #y al de seguras si no estaba ya

    def infer_precipicios(self):
        """Función que aplica deducción por descarte: 
        Si solo queda una celda posible para un precicipio, la confirmamos.
        Actualiza: 
        -confirmed_precipicios
        -safe del resto
        """
        #recorremos constraints de brisa
        por_confirmar = set()

        for pos, cand in list(self.brisa_constraints.items()):
            #limpiamos candidatos imposibles
            cleaned = set()
            for c in cand:
                if (c not in self.safe) and (c not in self.visited): #si ya la hemos visitdo, ya sabemos que no era precipicio
                    cleaned.add(c)
            
            self.brisa_constraints[pos] = cleaned #los nuevos valores de posibles precipicios de la posicion

            if len(cleaned) == 1: # si queda solo uno, confirmamos que es precipicio
                only = next(iter(cleaned))
                por_confirmar.add(only) 
        
        #aplicamos confirmaciones
        for pit in por_confirmar:
            self.confirmed_precipicios.add(pit)
            self.possible_precipicios.discard(pit) #usamos discard para que no pete si no está
            #un precipicio no puede ser seguro, así que lo quitamos si estuivera en el set de seguras
            self.safe.discard(pit)

            #y lo quitamos como candidato de otras constraints
            for pos in list(self.brisa_constraints.keys()):
                self.brisa_constraints[pos].discard(pit)
        
        #nos aseguramos de que si una celda está en safe, no debe estar como posible precipicio
        for cell in list(self.safe):
            self.possible_precipicios.discard(cell)

    def infer_soldado(self):
        """Función que aplica deducción por descarte: 
        Si solo queda una celda posible para el soldado:
        -la guardamos en self.confirmed_soldier.
        -eliminamos el resto de self.possible_soldier.
        """
        if self.confirmed_soldier is not None: #si ya está confirmado, no inferimos más
            return
        
        posibles_confirmados = set()

        for pos, cand in list(self.sold_constraints.items()):
            cleaned = set()
            for c in cand: 
                if (c not in self.safe) and (c not in self.visited):
                    cleaned.add(c)

            self.sold_constraints[pos] = cleaned

            if len(cleaned) == 1:
                posibles_confirmados.add(next(iter(cleaned)))

        #si varias constrains apuntan al mismo candidato, lo confirmamos como tal
        if len(posibles_confirmados) == 1:
            self.confirmed_soldier = next(iter(posibles_confirmados))
            self.possible_soldier = set([self.confirmed_soldier])
            self.safe.discard(self.confirmed_soldier)

            #limpiamos constrains quitando todo lo que no sea esa celda
            for pos in list(self.sold_constraints.keys()):
                candidatos = self.sold_constraints[pos]

                if self.confirmed_soldier in candidatos: #esta constraint sigue siendo váñida, pero ahora el único candidato posible es el soldado confirmado
                    self.sold_constraints[pos] = {self.confirmed_soldier}
                else: #esta constraint ya no tien sentido
                    self.sold_constraints[pos] = set() #la vacíamos

    def is_safe(self, cell):
        """Función booleana que devuelve True si la KB está segura de que no hay peligro en esa celda.
        Argumentos:
        -cell: celda donde vemos si es segura
        """
        return cell in self.safe #devuelve True si está en el set de seguras


    def get_safe_unvisited_neighbors(self, position):
        """Función que devuelve una lista de celdas adyacentes marcando las seguras y no visitadas.
        Argumentos:
        -position: posición actual de donde ver sus lista de adyacentes.
        """
        celdas = []
        for c in self.get_celdas_adyacentes(position): #para cada adyacente comprobamos su seguridad y si no esta visitada
            if c in self.safe and c not in self.visited:
                #si tampoco es posible precipicio o soldado
                if c not in self.confirmed_precipicios and c!=self.confirmed_soldier:
                    celdas.append(c)
        return celdas
    
    def get_safe_neighbors(self, position):
        """Función que devuelve una lista de celdas adyacentes marcando las seguras (pueden haber sido ya visitadas).
        Argumentos:
        -position: posición actual de donde ver sus lista de adyacentes.
        """
         
        celdas = []
        for c in self.get_celdas_adyacentes(position):
            if c in self.safe and c not in self.confirmed_precipicios and c!=self.confirmed_soldier and c not in self.possible_soldier:
                celdas.append(c)

        return celdas





