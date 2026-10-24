"""
Script para la Parte 2.2. Cruzar el río modelando MDP.

"""
import random

class RiverEnvironment:
    def __init__(self, rows=7, cols=9, nislas=2):
        self.rows=rows
        self.cols = cols
        self.nislas = nislas

        #elementos fijos
        self.start_pos = (rows//2, 0) #orilla inicial
        self.goal_pos = (rows// 2, cols-1) #salida en orilla final

        #estado del agente
        self.agente_pos = self.start_pos #orilla inicial
        self.done = False

        #obstáculos/peligros
        self.islands =set()
        self.peligros = set() 
        #corriente por columna
        self.strength = []
        for _ in range(cols):
            self.strength.append(0.0)

        self._generate_random_map()

    
    def _generate_random_map(self):
        #construimos un grid base
        self.grid = []
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                if c==0 or c==self.cols -1:
                    row.append('|')
                else:
                    row.append('R')
            
            self.grid.append(row)
        
        #colocamos la salida en orilla final
        gr, gc = self.goal_pos
        self.grid[gr][gc] = 'E'

        #corriente por columna
        self.strength[0] = 0.0 #la orilla inicial y la fianl no tienen
        self.strength[self.cols -1] = 0.0 

        #las demás, según estipula el enunciado, toman un valor aleatorio unfiroem
        for j in range(1, self.cols -1):
            self.strength[j] = round(random.uniform(0.06, 0.94), 1)


        #colocamos islas, sin que esten en la primera o la última fila, ni en la orilla, ni se solapen
        candidatas = []
        for r in range(1, self.rows -1):
            for c in range(1, self.cols-1):
                if (r,c) != self.goal_pos:
                    candidatas.append((r,c))
        
        random.shuffle(candidatas) #ponemos apra que estén de forma aleatoria
        self.islands = set()

        for pos in candidatas:
            if len(self.islands) >=self.nislas:
                break #no puede haber más
            self.islands.add(pos)

        #pintamos islas
        for (r,c) in self.islands:
            self.grid[r][c] = 'I'

        #reset estado
        self.agente_pos = (self.rows//2, 0)
        self.done = False

    def reset(self):
        self.agente_pos = self.start_pos
        self.done = False
        return self.agente_pos 

    def dentro_tablero(self, pos):
        r,c = pos
        return 0 <=r < self.rows and 0 <= c<self.cols
    
    def is_island(self, pos):
        return pos in self.islands
    
    def es_meta(self, pos):
        return pos == self.goal_pos
    
    def es_peligro(self, pos):
        return pos in self.peligros
    
    def river_strength(self, j):
        return self.strength[j]

    def plantilla(self):
        for r in range(self.rows):
            linea = []
            for c in range(self.cols):
                if (r,c) == self.agente_pos:
                    linea.append('CWCK') #definimos la posicion del agetnte
                else:
                    linea.append(self.grid[r][c])
            
            print("  ".join(linea))
        print()


    def aplicar_movimiento_determinista(self, pos, action):
        """Función que aplica el movimiento determinista con rebote: borde o isla, te quedas.
        """
        r, c = pos
        nr, nc = r,c

        if action == 'up':
            nr -= 1
        elif action == 'down':
            nr += 1
        elif action == 'left':
            nc -=1
        elif action == 'right':
            nc += 1
        else:
            return pos #accion que no sifrve, no nos movemos
        
        npos = (nr, nc)
        if (not self.dentro_tablero(npos)) or self.is_island(npos):
            return pos
        return npos
    
    def print_strength(self):
        print(f"river_strength por columna: {self.strength}")
        print()

#SIMULACION MDP

class RiverMDP:
    def __init__(self, env: RiverEnvironment):
        self.env = env
        #definimos las acciones
        self.actions = ['up', 'down', 'left', 'right', 'stay']

        #recompensas 
        self.r_movimiento = -1
        self.r_salida =  100
        self.r_peligro = -100

    def estados(self):
        #definimos los estados: todas las celdas excepto islas
        ss = []
        for r in range(self.env.rows):
            for c in range(self.env.cols):
                s = (r,c)
                if not self.env.is_island(s):
                    ss.append(s) #mientras no sea una isla, cuenta como posible estado
        return ss 
    

    def recompensas(self, s, a, sp):
        if self.env.es_meta(sp):
            return self.r_salida
        if self.env.es_peligro(sp):
            return self.r_peligro
        return self.r_movimiento #en cada movimiento, cobramos el -1

    def estado_objetivo(self, s):
        return self.env.es_meta(s)
    
    def transiciones(self, s, a):
        """Método que establece la distribución de probabilidad asociada a cada acción en un estado s:
        P(s'|s,a) """

        if self.estado_objetivo(s): #si estamos en la meta, la prob es 1
            return [(s, 1.0)]
        
        i, j = s #definimos coordenads
        rs = self.env.river_strength(j) #acortamos el nombre

        dist = {}

        def add(sp, p):
            dist[sp] = dist.get(sp, 0.0) + p

        if a == 'down':
            sp = self.env.aplicar_movimiento_determinista(s, 'down')
            add(sp, 1.0) #la prob es 1

        elif a == 'stay':
            p_stay = 1.0 -rs
            p_down = rs

            sp_stay = s
            sp_down = self.env.aplicar_movimiento_determinista(s, 'down')
            
            add(sp_stay, p_stay)
            add(sp_down, p_down)
        else: #si a no es down
            #definimos probabilidades
            p_dir = 1.0 - rs
            p_down = rs
            
            #aplicamos movimientos
            sp_dir = self.env.aplicar_movimiento_determinista(s,a)
            sp_down = self.env.aplicar_movimiento_determinista(s, 'down')

            #calculamos P(s'|s,a)
            add(sp_dir, p_dir)
            add(sp_down, p_down)

        #normalizacion defencisva
        total = sum(dist.values())
        buenas = []
        for sp, p in dist.items():
            buenas.append((sp, p / total))
        return buenas
    
        

#value iteration
def value_iteration(mdp: RiverMDP):
    #valores por defecto
    gamma = 0.95 #aunque en clase usamos 1, también se puede
    max_iteraciones = 10000

    V = {s: 0.0 for s in mdp.estados()}

    for _ in range(max_iteraciones):
        delta = 0.0
    
        for s in mdp.estados():
            if mdp.estado_objetivo(s): 
                continue

            best = None
            for a in mdp.actions:
                q = 0.0
                for sp, p in mdp.transiciones(s,a ): #aplicamos la ecuación de Bellman
                    q += p*(mdp.recompensas(s,a,sp) + gamma*V[sp])
                if best is None or q > best:
                    best = q

            delta = max(delta, abs(best-V[s])) #actualizamos con el maximo
            V[s] = best

        if delta < 1e-6:
            break #condicon de aprada para que no itere hasta el 10000

    #política greedy, sacamos la política:
    policy = {}
    for s in mdp.estados():
        if mdp.estado_objetivo(s):
            continue

        best_a = None
        best_q = None
        for a in mdp.actions:
            q = 0.0
            for sp, p in mdp.transiciones(s,a):
                q += p * (mdp.recompensas(s,a, sp) + gamma * V[sp])
            
            if best_q is None or q > best_q:
                best_q = q
                best_a = a
        
        policy[s] = best_a #la política que buscamos es la meor accion
    
    return V, policy 


#simulacion 
def muestra_siguiente_estado(transiciones):
    r = random.random()
    acc = 0.0
    for sp, p in transiciones:
        acc += p
        if r <= acc:
            return sp

    return transiciones[-1][0]        

def simular(env: RiverEnvironment, mdp: RiverMDP, policy, max_pasos = 80):
    env.reset()
    total_return = 0

    print("Mapa inicial")
    env.plantilla()
    env.print_strength()

    for t in range(max_pasos):
        s = env.agente_pos
        if mdp.estado_objetivo(s):
            print("LLegamos POR FIN  a al salidaaa")
            break

        a = policy.get(s, 'stay')
        transi = mdp.transiciones(s, a)
        sp = muestra_siguiente_estado(transi)
        r = mdp.recompensas(s,a,sp)

        total_return += r
        env.agente_pos = sp

        print(f"Paso {t}: estado s: {s}, acción a: {a} --> s'{sp}, r= {r}")
        env.plantilla()
    
    print(f"Retorno total: {total_return}")



if __name__ == "__main__":
    env = RiverEnvironment(rows=7, cols=9, nislas=2)
    mdp = RiverMDP(env)

    V, policy = value_iteration(mdp)

    print("Política (flechas): ")
    flechas = {'up': '↑', 'down': '↓', 'left': '←', 'right': '→', 'stay': '·'}
    for r in range(env.rows):
        row = []
        for c in range(env.cols):
            s = (r, c)
            if env.is_island(s):
                row.append('I')
            elif env.es_meta(s):
                row.append('E')
            else:
                row.append(flechas.get(policy.get(s, 'stay'), '·'))
        print(" ".join(row))
    print()

    simular(env, mdp, policy, max_pasos=60)