import copy

class WorldCupCSP:
    def __init__(self, teams, groups, debug=False):
        """
        Inicializa el problema CSP para el sorteo del Mundial.
        :param teams: Diccionario con los equipos, sus confederaciones y bombos.
        :param groups: Lista con los nombres de los grupos (A-L).
        :param debug: Booleano para activar trazas de depuración.
        """
        self.teams = teams
        self.groups = groups
        self.debug = debug

        # Las variables son los equipos.
        self.variables = list(teams.keys())

        # El dominio de cada variable inicialmente son todos los grupos.
        self.domains = {team: list(groups) for team in self.variables}

    def get_team_confederation(self, team):
        return self.teams[team]["conf"]

    def get_team_pot(self, team):
        return self.teams[team]["pot"]

    def is_valid_assignment(self, group, team, assignment):
        """
        Verifica si asignar un equipo a un grupo viola
        las restricciones de confederación o tamaño del grupo.
        """
        team_conf = self.teams[team]["conf"]
        team_pot = self.teams[team]["pot"]

        # Euipos ya asignados a este grupo
        teams_in_group = [t for t, g in assignment.items() if g == group]

        # Restriccion de tamaño del grupo (máximo 4)
        if len(teams_in_group) >= 4:
            return False
        
        # Restriccion de que no puede haber 2 equipos del mismo bombo
        for t in teams_in_group:
            if self.teams[t]["pot"] == team_pot:
                return False
            
        # Restricción de confederaciones (máximo 1, excepto UEFA máximo 2)
        conf_count = sum(1 for t in teams_in_group if self.teams[t]["conf"] == team_conf)
        if team_conf == "UEFA":
            if conf_count >= 2:
                return False
        else:
            if conf_count >= 1:
                return False
            
        return True

    def forward_check(self, assignment, domains):
        """
        Propagación de restricciones.
        Debe eliminar valores inconsistentes en dominios futuros.
        Retorna True si la propagación es exitosa, False si algún dominio queda vacío.
        """
        # Hacemos una copia de los dominios actuales para modificarla de forma segura
        new_domains = copy.deepcopy(domains)

        # Para cada variable no asignada, eliminar grupos invalidos de su dominio
        for team in self.variables:
            if team in assignment:
                continue
            new_domains[team] = [
                g for g in new_domains[team]
                if self.is_valid_assignment(g, team, assignment)
            ]
            if len(new_domains[team]) == 0:
                if self.debug:
                    print(f" [FC] Dominio vacio para {team}")
    
        return True, new_domains

    def select_unassigned_variable(self, assignment, domains):
        """
        Heurística MRV (Minimum Remaining Values).
        Selecciona la variable no asignada con el dominio más pequeño.
        """
        # Heurística MRV - seleccionar variable no asignada con dominio mas pequeño
        unassigned = [v for v in self.variables if v not in assignment]
        if not unassigned:
            return None
        return min(unassigned, key=lambda v: len(domains[v]))
    

    def backtrack(self, assignment, domains=None):
        """
        Backtracking search para resolver el CSP.
        """
        if domains is None:
            domains = copy.deepcopy(self.domains)

        # Condición de parada: Si todas las variables están asignadas, retornamos la asignación.
        if len(assignment) == len(self.variables):
            return assignment

        # Seleccionar variable con MRV
        team = self.select_unassigned_variable(assignment, domains)
        if team is None:
            return None
        
        if self.debug:
            print(f"[BT] Intentando asignar: {team} | Dominio: {domains[team]}")

        # Iterar sobre sus valores (grupos) posibles en el dominio
        for group in domains[team]:
            # Verificar si es válido, hacer la asignación y aplicar forward checking
            if self.is_valid_assignment(group, team, assignment):
                assignment[team] = group

                if self.debug:
                    print(f" [BT] {team} -> Grupo {group}")

                succes, new_domains = self.forward_check(assignment, domains)

                if succes:
                    # Llamada recursiva
                    result = self.backtrack(assignment, new_domains)
                    if result is not None:
                        return result

                # Deshacer la asignación si falla (backtrack)
                if self.debug:
                    print(f" [BT] Backtrack: deshaciendo {team} -> Grupo {group}")
                del assignment[team]
                                
        return None
