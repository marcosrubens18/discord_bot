# expedicao_ia.py — Integração com Gemini AI para Expedições Narrativas
import os
import json
import asyncio
import aiohttp
from datetime import datetime

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

LORE_VILLA_ELDORIA = """
Villa Eldoria é uma cidade medieval de fantasia com magia, monstros e aventureiros.
O mundo possui masmorras perigosas, criaturas sombrias e tesouros antigos.
Os aventureiros pertencem a classes como Guerreiro, Mago, Arqueiro, Paladino, Necromante, Dracomante e Arcano.
Cada classe possui habilidades únicas e passivas raciais.
O sistema de progressão vai do Rank F ao Rank SS.
A moeda local são as Moedas de Ouro.
"""

def prompt_sistema(expedicao: dict, participantes: list) -> str:
    nomes_classes = "\n".join([
        f"- {p['nome']} (Classe: {p['classe_id'].title()}, Nível: {p['nivel']}, Rank: {p.get('rank','F')})"
        for p in participantes
    ])
    monstros = ", ".join(expedicao.get("monstros_permitidos", []))
    return f"""Você é o Mestre da Expedição em Villa Eldoria. Conduza uma aventura épica e imersiva.

MUNDO:
{LORE_VILLA_ELDORIA}

EXPEDIÇÃO: {expedicao['nome']}
CONTEXTO: {expedicao['contexto']}
DIFICULDADE: {expedicao.get('dificuldade','Media')}

PARTICIPANTES ATIVOS:
{nomes_classes}

MONSTROS PERMITIDOS (APENAS ESTES):
{monstros}

REGRAS ABSOLUTAS:
1. NUNCA invente monstros além dos listados acima
2. NUNCA distribua ouro, XP ou itens diretamente — o sistema cuida disso
3. SEMPRE responda em JSON válido com o campo "tipo"
4. Mantenha tom épico e narrativo em português
5. Considere as classes dos participantes nas situações criadas

TIPOS DE RESPOSTA POSSÍVEIS:

Narrativa simples:
{{"tipo":"narrativa","texto":"..."}}

Apresentar escolhas aos jogadores:
{{"tipo":"escolha","texto":"...","opcoes":["opcao1","opcao2","opcao3"]}}

Iniciar combate:
{{"tipo":"combate","monstro":"Nome do Monstro","quantidade":1,"narrativa":"..."}}

Encerrar expedição com sucesso:
{{"tipo":"fim","sucesso":true,"narrativa":"...","cronica":"resumo épico da aventura"}}

Encerrar expedição com derrota:
{{"tipo":"fim","sucesso":false,"narrativa":"...","cronica":"resumo épico da aventura"}}

Comece narrando a chegada dos aventureiros ao local da expedição.
"""

async def chamar_gemini(mensagens: list, system: str) -> dict:
    """Chama a API Gemini com histórico de mensagens."""
    if not GEMINI_API_KEY:
        return {"tipo": "narrativa", "texto": "Erro: GEMINI_API_KEY não configurada."}

    # Monta o conteúdo
    contents = []
    for msg in mensagens:
        contents.append({
            "role": msg["role"],
            "parts": [{"text": msg["content"]}]
        })

    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.85,
            "maxOutputTokens": 1500,
            "responseMimeType": "application/json"
        }
    }

    url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                data = await resp.json()
                if resp.status != 200:
                    print(f"Gemini error {resp.status}: {data}")
                    return {"tipo": "narrativa", "texto": "O Mestre está pensando... tente novamente."}
                texto = data["candidates"][0]["content"]["parts"][0]["text"]
                # Parse JSON
                texto = texto.strip()
                if texto.startswith("```"):
                    texto = texto.split("```")[1]
                    if texto.startswith("json"):
                        texto = texto[4:]
                return json.loads(texto)
    except json.JSONDecodeError:
        return {"tipo": "narrativa", "texto": texto if 'texto' in dir() else "Erro ao processar resposta."}
    except Exception as e:
        print(f"Erro Gemini: {e}")
        return {"tipo": "narrativa", "texto": "O Mestre encontrou um obstáculo mágico. Aguarde..."}

async def resumir_historico(historico: list, expedicao_nome: str) -> str:
    """Gera um resumo do histórico para economizar tokens."""
    if not historico: return ""
    eventos_txt = "\n".join([
        f"[{h['tipo'].upper()}] {h['conteudo'][:200]}"
        for h in historico[-20:]
    ])
    payload = {
        "contents": [{
            "role": "user",
            "parts": [{"text": f"Resuma em 3-4 parágrafos os eventos da expedição '{expedicao_nome}':\n{eventos_txt}"}]
        }],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 500}
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "Resumo indisponível."

async def gerar_cronica(expedicao: dict, participantes: list, historico: list, sucesso: bool) -> str:
    """Gera a crônica final da expedição."""
    nomes = ", ".join([p["nome"] for p in participantes])
    eventos = "\n".join([f"- {h['conteudo'][:150]}" for h in historico[-30:]])
    resultado = "SUCESSO" if sucesso else "DERROTA"
    prompt = (
        f"Escreva uma crônica épica e literária em português para o arquivo de Villa Eldoria.\n\n"
        f"Expedição: {expedicao['nome']}\n"
        f"Participantes: {nomes}\n"
        f"Resultado: {resultado}\n"
        f"Eventos:\n{eventos}\n\n"
        f"A crônica deve ter entre 150 e 300 palavras, tom épico medieval, "
        f"mencionar os participantes pelos nomes e destacar o momento mais dramático."
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.9, "maxOutputTokens": 600}
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Expedição '{expedicao['nome']}' — Resultado: {resultado}. Participantes: {nomes}."
