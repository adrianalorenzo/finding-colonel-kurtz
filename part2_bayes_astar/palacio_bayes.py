#SCRIPT DE RESOLUCIÓN DE LA PARTE II:

"""
Script principal de la parte 2.1 donde se estudia la probabilidad de los mapas según Bayes
"""


class PalacioBayes:
    def __init__(self, n=6, start=(0,0)):
        #tamaño del tablero
        self.n = n

        #posición inical (CW)
        self.start = start
        self.PCK = None #CK

        #guardamos las creencias de cada elemento
        self.PF = None #trampa fuego
        self.PP = None #trampa pinchos
        self.PD = None #trampa dardos
        self.PM = None #estímulo militar
        self.PS = None #estímulo salida

        #inicalizamos priors (uniformes 1/(N-1))
        self._init_priors()



    #métodos relacionados con las utilidades del tablero
    def dentro_tablero(self, i, j):
        """Función que devuelve True si (i,j) está dentron del tablero.
        """
        return 0 <= i < self.n and 0 <= j < self.n
    
    def vecinos(self, cell):
        """Devuelve als celdas adyacentes (las de dist de Manhattan =1) dentro del tablero.
        """
        i, j = cell
        cand = [(i-1, j), (i+1, j), (i, j-1), (i, j+1)]
        buenas = []
        for (a,b) in cand:
            if self.dentro_tablero(a,b):
                buenas.append((a,b)) #añadimos las que están dentro del tablero
        return buenas
    
    def adj_y_mismo (self, cell):
        """Función que devuelve la unión de los adyacentes y sí mismo. 
        En el enunciado, hemos visto como el estímulo se percibe tanto si estás en la celda o adyacente.
        """
        junto = [cell] #partimos de la principal
        junto.extend(self.vecinos(cell)) #añadimos los adyacentes
        return junto
    
    def make_grid(self, val):
        """Función para crear una matriz general nxn que iremos rellenando.
        """
        tablero = []
        for _ in range(self.n):
            row = []
            for _ in range(self.n):
                row.append(float(val))
            tablero.append(row)
        return tablero
        
    #priors uniforme
    def _init_uniform_prior(self):
        """
        Prior uniforme del enunciado:
        -0 en start (porque ya estamos en esa celda)
        -1/(N-1) en el resto
        """

        P = self.make_grid(0.0)
        N = self.n * self.n
        denom = N-1 #sera 36-1 = 35

        for i in range(self.n):
            for j in range(self.n):
                if (i,j) == self.start: #menos la inicial
                    P[i][j] = 0.0
                else:
                    P[i][j] = 1.0 / denom
        
        return P
    
    def _init_priors(self):
        """
        Función que inicializa los posteriors PF, PP, PD, PM, PS con el prior uniforme.
        """
        self.PF = self._init_uniform_prior()
        self.PP = self._init_uniform_prior()
        self.PD = self._init_uniform_prior()
        self.PM = self._init_uniform_prior()
        self.PS = self._init_uniform_prior()
        self.PCK = self._init_uniform_prior()
    
    #visualización 
    def print_map(self, P, title, pos= None):
        """
        Imprime el mapa P como 'heatmap' general, para cada uno de los que tenemos que visualizar
        Si pos está definido, marcamos la celda con 'CW'
        """
        print(f"\n-----{title}------")
        for i in range(self.n):
            row = []
            for j in range(self.n):
                if pos is not None and (i,j) == pos:
                    row.append(' CW ')
                else:
                    row.append("{:0.2f}".format(P[i][j]))
            print(" ".join(row))

    #bayes
    def normalize(self, P):
        """Función que normaliza un grid para que sume 1
        """
        s = 0.0
        for i in range(self.n):
            for j in range(self.n):
                s += P[i][j]
        
        if s > 0.0:
            for i in range(self.n):
                for j in range(self.n):
                    P[i][j] = P[i][j]/s #normalizamos cada celda
        
        return P #grid actualizado ya normalizado
    
    def update_with_evidence(self, P_prior, pos, e_tau):
        """
        Función que actualiza Bayes con cada likehood 0/1 tal y como decía el enunciado.
        Establecemos la evidencia:
        -e_tau = TRue: si el elemento está en los adyacentes o en la pos
        -e_tau = False: el elemento NO está en esa zona
        """
        zona = set(self.adj_y_mismo(pos)) #zona válida donde afectan los estímulos

        P_post = self.make_grid(0.0)

        #recorremos todo el tablero
        for i in range(self.n):
            for j in range(self.n):
                en_zona = ((i,j) in zona)
                if e_tau:
                    ok = en_zona #si la celda es compatible con la evidencia
                else:
                    ok = not en_zona
                
                #aplicamos bayes: prior * likehood(0 o 1)
                if ok:
                    P_post[i][j] = P_prior[i][j]
                else:
                    P_post[i][j] = 0.0 #descartamos hipótesis
        
        #normalizamos para que sea una distribución válida
        return self.normalize(P_post)

    def update(self, pos, percepcion):
        """
        Nuevas percepciones: percept_nombres = [eF, eP, eD, eM, eS, Pared↑, Pared↓, Pared←, Pared→, Grito]
        """

        eF = percepcion[0]
        eP = percepcion[1]
        eD = percepcion[2]
        eM = percepcion[3]
        eS = percepcion[4]
                    
        self.PF = self.update_with_evidence(self.PF, pos, eF)
        self.PP = self.update_with_evidence(self.PP, pos, eP)
        self.PD = self.update_with_evidence(self.PD, pos, eD)
        self.PM = self.update_with_evidence(self.PM, pos, eM)
        self.PS = self.update_with_evidence(self.PS, pos, eS)


    def trampa_cualquiera(self):
        """
        Mapa requerido: trampa cualquiera = PF + PP + PD.
        (No necesariamente suma 1, es intencional).
        """
        P = self.make_grid(0.0)
        for i in range(self.n):
            for j in range(self.n):
                P[i][j] = self.PF[i][j] + self.PP[i][j] + self.PD[i][j] #sumamos las probabilidades de cad tipo de trampa

        return P
    
    def print_required_maps(self, pos):
        """Imprimie los 3 mapas obligatorios.
        """
        self.print_map(self.trampa_cualquiera(), "P (trampaa cualquiera) = PF+PP+PD", pos)
        self.print_map(self.PM, "P(enemigo M)", pos)
        self.print_map(self.PS, "P(salida S)", pos)
    
    def get_required_maps(self):
        """Devuelve los 3 mapas sin imprimir. Válido para el resto del problema.
        """
        return (self.trampa_cualquiera(), self.PM, self.PS)


    def descartar_celdas_visitadas_seguras(self, pos):
        """
        Función que emplea inferencia y descarta aquellas celdas donde aunque antes tenían prob de algún peligro, 
        si hemos pasado por ellas y no había ninguno, entonces su prob de peligro se queda a 0
        """
        i,j = pos

        self.PF[i][j] = 0.0
        self.PP[i][j] = 0.0
        self.PD[i][j] = 0.0
        self.PM[i][j] = 0.0

        self.PF = self.normalize(self.PF)
        self.PP = self.normalize(self.PP)
        self.PD = self.normalize(self.PD)
        self.PM = self.normalize(self.PM)



if __name__ == "__main__":
    #main extra para ir probando
    b = PalacioBayes(n=6, start=(0,0))
    pos = (0,0)

    #percepcion ejemplo F y no percibe P, D, M, S
    percep = [True, False, False, False, False, True,False, True, False, False]

    b.update(pos=pos, percepcion=percep)
    b.print_required_maps(pos=pos)

