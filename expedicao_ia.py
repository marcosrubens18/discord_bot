# expedicao_ia.py — Integração com Gemini AI para Expedições Narrativas
import os
import json
import aiohttp
import asyncio

# Tenta ler a chave de várias fontes
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Se não achou, tenta do arquivo config.txt
if not GEMINI_API_KEY:
    try:
        with open("config.txt", "r") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    GEMINI_API_KEY = line.split("=", 1)[1].strip()
                    break
    except:
        pass

# Debug
print(f"[Gemini] API Key configurada: {'SIM' if GEMINI_API_KEY else 'NAO'}")
if GEMINI_API_KEY:
    print(f"[Gemini] Primeiros caracteres: {GEMINI_API_KEY[:15]}...")

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
        f"- {p['nome']} (Classe: {p['classe_id'].title()}, Nível: {p['nivel']}, Rank: {p.get('rank', 'F')})"
        for p in participantes
    ])
    monstros = ", ".join(expedicao.get("monstros_permitidos", []))
    return f"""Você é o Mestre da Expedição em Villa Eldoria. Conduza uma aventura épica e imersiva.

MUNDO:
{LORE_VILLA_ELDORIA}

EXPEDIÇÃO: {expedicao['nome']}
CONTEXTO: {expedicao['contexto']}
DIFICULDADE: {expedicao.get('dificuldade', 'Media')}

PARTICIPANTES ATIVOS:
{nomes_classes}

MONSTROS PERMITIDOS (APENAS ESTES):
{monstros}

REGRAS ABSOLUTAS:
1. Use apenas os monstros listados acima
2. NUNCA distribua ouro, XP ou itens — o sistema cuida disso
3. SEMPRE responda em JSON com o campo "tipo"
4. Mantenha tom épico em português

RESPOSTAS POSSÍVEIS (responda SOMENTE com JSON):

1. Narrativa: {{"tipo":"narrativa","texto":"..."}}
2. Escolha: {{"tipo":"escolha","texto":"...","opcoes":["opcao1","opcao2"]}}
3. Combate: {{"tipo":"combate","monstro":"Goblin","quantidade":2,"narrativa":"..."}}
4. Fim: {{"tipo":"fim","sucesso":true,"narrativa":"..."}}

Comece narrando a chegada dos aventureiros ao local da expedição.
"""

async def chamar_gemini(mensagens: list, system: str) -> dict:
    """Chama a API Gemini com histórico de mensagens."""
    
    if not GEMINI_API_KEY:
        print("[Gemini] ERRO: API Key não configurada!")
        return {"tipo": "narrativa", "texto": "Mestre está ausente. API Key não configurada."}

    # Formata as mensagens corretamente
    contents = []
    for msg in mensagens:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}]
        })
    
    # Se não tem mensagens, adiciona uma inicial
    if not contents:
        contents.append({
            "role": "user",
            "parts": [{"text": "Inicie a expedição."}]
        })

    payload = {
        "system_instruction": {
            "parts": [{"text": system}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.85,
            "maxOutputTokens": 800,
            "responseMimeType": "application/json"
        }
    }

    url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
    
    print(f"[Gemini] Enviando requisição para {url[:50]}...")
    print(f"[Gemini] Número de mensagens: {len(contents)}")
    
    try:
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as resp:
                print(f"[Gemini] Status code: {resp.status}")
                
                if resp.status != 200:
                    texto_erro = await resp.text()
                    print(f"[Gemini] Erro {resp.status}: {texto_erro[:200]}")
                    return {"tipo": "narrativa", "texto": f"Erro na API: {resp.status}"}
                
                data = await resp.json()
                
                if "candidates" not in data or not data["candidates"]:
                    print(f"[Gemini] Resposta sem candidates: {data}")
                    return {"tipo": "narrativa", "texto": "A IA não retornou uma resposta válida."}
                
                texto = data["candidates"][0]["content"]["parts"][0]["text"]
                print(f"[Gemini] Resposta recebida: {texto[:100]}...")
                
                # Limpa o texto
                texto = texto.strip()
                if texto.startswith("```json"):
                    texto = texto[7:]
                if texto.startswith("```"):
                    texto = texto[3:]
                if texto.endswith("```"):
                    texto = texto[:-3]
                texto = texto.strip()
                
                # Tenta parsear JSON
                try:
                    return json.loads(texto)
                except json.JSONDecodeError as e:
                    print(f"[Gemini] JSON inválido: {e}")
                    # Tenta extrair JSON do texto
                    import re
                    json_match = re.search(r'\{.*\}', texto, re.DOTALL)
                    if json_match:
                        try:
                            return json.loads(json_match.group())
                        except:
                            pass
                    return {"tipo": "narrativa", "texto": texto[:500]}
                    
    except asyncio.TimeoutError:
        print("[Gemini] Timeout na requisição")
        return {"tipo": "narrativa", "texto": "A IA demorou muito para responder. Tente novamente."}
    except Exception as e:
        print(f"[Gemini] Erro inesperado: {e}")
        return {"tipo": "narrativa", "texto": f"Erro: {str(e)[:100]}"}

async def resumir_historico(historico: list, expedicao_nome: str) -> str:
    """Gera um resumo do histórico."""
    if not historico:
        return ""
    eventos = "\n".join([f"- {h['conteudo'][:100]}" for h in historico[-10:]])
    return f"Resumo de {expedicao_nome}:\n{eventos}"

async def gerar_cronica(expedicao: dict, participantes: list, historico: list, sucesso: bool) -> str:
    """Gera a crônica final."""
    nomes = ", ".join([p["nome"] for p in participantes])
    resultado = "SUCESSO" if sucesso else "DERROTA"
    return f"📜 **Crônica de {expedicao['nome']}**\n\nOs aventureiros {nomes} completaram a expedição com {resultado}!\n\n*Registrado nos anais de Villa Eldoria.*"
