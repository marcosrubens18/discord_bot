# expedicao_ia.py — Fallback sem IA para testes
import json
import random

GEMINI_API_KEY = ""  # Não precisa

LORE_VILLA_ELDORIA = """
Villa Eldoria é uma cidade medieval de fantasia com magia e monstros.
"""

def prompt_sistema(expedicao: dict, participantes: list) -> str:
    return "Sistema de expedição ativo."

async def chamar_gemini(mensagens: list, system: str) -> dict:
    """Versão offline que gera respostas automáticas"""
    
    # Primeira mensagem - início da expedição
    if len(mensagens) <= 2:
        return {
            "tipo": "narrativa",
            "texto": "🏰 **A Expedição Começa!**\n\nOs aventureiros se reúnem na entrada da masmorra. O vento frio sopra entre as ruínas antigas. Uma névoa densa envolve o caminho à frente.\n\nVocês se preparam para a jornada, verificando seus equipamentos e armas.\n\nO que vocês fazem?"
        }
    
    # Conta quantas interações já teve
    interacoes = len([m for m in mensagens if m.get("role") == "user"])
    
    # Escolha (a cada 2 interações)
    if interacoes % 2 == 0 and interacoes < 8:
        opcoes_lista = [
            ["Entrar pela porta da esquerda", "Entrar pela porta da direita", "Inspecionar as paredes em busca de segredos"],
            ["Seguir o corredor principal", "Explorar uma passagem lateral", "Voltar e acender uma tocha"],
            ["Atacar os inimigos de frente", "Tentar flanquear pelas sombras", "Usar magia para iluminar a área"],
            ["Subir as escadas", "Descer para o porão", "Procurar por pistas"]
        ]
        return {
            "tipo": "escolha",
            "texto": "Uma decisão se apresenta aos aventureiros:",
            "opcoes": random.choice(opcoes_lista)
        }
    
    # Combate (após algumas escolhas)
    if interacoes > 6 and interacoes < 12:
        monstros = ["Goblin", "Esqueleto", "Lobo Selvagem", "Morcego Gigante"]
        return {
            "tipo": "combate",
            "monstro": random.choice(monstros),
            "quantidade": random.randint(1, 3),
            "narrativa": "⚠️ **COMBATE!** ⚠️\n\nDe repente, criaturas saltam das sombras! Preparem suas armas!"
        }
    
    # Finalização
    if interacoes >= 12:
        return {
            "tipo": "fim",
            "sucesso": True,
            "narrativa": "🏆 **VITÓRIA!** 🏆\n\nApós uma longa jornada, os aventureiros derrotam o guardião final e encontram o tesouro! A expedição foi um sucesso!\n\nVocês retornam à vila como heróis, carregando riquezas e glória.",
            "cronica": "Os bravos aventureiros completaram a expedição com sucesso!"
        }
    
    # Narrativa padrão
    narrativas = [
        "Os aventureiros avançam cautelosamente pelo corredor escuro. O eco de seus passos ressoa nas paredes de pedra...",
        "Uma brisa fria passa por vocês. Algo observa das sombras, mas não conseguem identificar o que é...",
        "Vocês encontram uma sala com um baque antigo no centro. Parece trancado...",
        "O chão começa a tremer levemente. Talvez seja melhor se apressarem...",
        "Vocês avistam uma luz ao longe. Seria a saída? Ou mais perigos?"
    ]
    
    return {
        "tipo": "narrativa",
        "texto": random.choice(narrativas)
    }

async def resumir_historico(historico: list, expedicao_nome: str) -> str:
    return f"Resumo da expedição {expedicao_nome}..."

async def gerar_cronica(expedicao: dict, participantes: list, historico: list, sucesso: bool) -> str:
    nomes = ", ".join([p["nome"] for p in participantes])
    resultado = "sucesso" if sucesso else "derrota"
    return f"📜 **Crônica de {expedicao['nome']}**\n\nOs aventureiros {nomes} completaram a expedição com {resultado}!"
