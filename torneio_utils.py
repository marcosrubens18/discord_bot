# torneio_utils.py — Utilitários para o sistema de torneio
import math
from typing import List, Tuple

def nome_fase(total_lutas: int) -> str:
    """
    Retorna o nome da fase baseado no número de lutas.
    
    Args:
        total_lutas: Número total de lutas na fase
    
    Returns:
        Nome da fase em maiúsculas
    """
    if total_lutas == 1:
        return "FINAL"
    if total_lutas == 2:
        return "SEMIFINAL"
    if total_lutas == 4:
        return "QUARTAS"
    if total_lutas == 8:
        return "OITAVAS"
    if total_lutas == 16:
        return "OITAVAS"
    if total_lutas == 32:
        return "TRIGÉSIMAS SEGUNDAS"
    return f"RODADA {total_lutas}"

def proxima_potencia_2(n: int) -> int:
    """
    Retorna a próxima potência de 2 maior ou igual a n.
    
    Args:
        n: Número de participantes
    
    Returns:
        Próxima potência de 2
    """
    p = 1
    while p < n:
        p *= 2
    return p

def calcular_byes(n_participantes: int) -> int:
    """
    Calcula o número de byes necessários.
    
    Args:
        n_participantes: Número de participantes
    
    Returns:
        Número de byes
    """
    pot2 = proxima_potencia_2(n_participantes)
    return pot2 - n_participantes

def gerar_chaves(participantes_ids: List[int], participantes_nomes: List[str]) -> List[Tuple]:
    """
    Gera as chaves do torneio com byes para os melhores.
    
    Args:
        participantes_ids: Lista de IDs dos participantes
        participantes_nomes: Lista de nomes dos participantes
    
    Returns:
        Lista de tuplas (user1_id, user1_nome, user2_id, user2_nome, bye)
    """
    n = len(participantes_ids)
    pot2 = proxima_potencia_2(n)
    byes = pot2 - n
    
    chaves = []
    luta_num = 1
    
    # Byes para os melhores (primeiros da lista - maior nível)
    for i in range(byes):
        chaves.append((participantes_ids[i], participantes_nomes[i], None, None, True))
        luta_num += 1
    
    # Pares com os restantes
    restantes_ids = participantes_ids[byes:]
    restantes_nomes = participantes_nomes[byes:]
    
    for i in range(0, len(restantes_ids) - 1, 2):
        chaves.append((
            restantes_ids[i], restantes_nomes[i],
            restantes_ids[i + 1], restantes_nomes[i + 1],
            False
        ))
        luta_num += 1
    
    return chaves