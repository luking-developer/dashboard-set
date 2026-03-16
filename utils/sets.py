def buscar_primer_hueco(lista_sets, inicio_rango):
    """
    Encuentra el primer numero faltante en una secuencia.
    Si no hay huecos, devuelve el maximo + 1.
    Si la lista esta vacia, devuelve el inicio del rango.
    """
    if not lista_sets:
        return inicio_rango
    
    conjunto_sets = set(lista_sets)
    min_val = min(lista_sets)
    max_val = max(lista_sets)
    
    # Checkear si falta el numero inicial del rango
    if min_val > inicio_rango:
        return inicio_rango

    # Buscar el primer hueco entre el minimo y el maximo existente
    for i in range(min_val, max_val + 1):
        if i not in conjunto_sets:
            return i
            
    # Si no hay huecos, el siguiente es el maximo + 1
    return max_val + 1