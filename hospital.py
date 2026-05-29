# hospital.py
import discord
import aiosqlite
import asyncio
import random

DB_PATH = "rpg.db"

# ─── PLANOS DO HOSPITAL ──────────────────────────────────────────
PLANOS = [
    {"id":"basico",   "nome":"Atendimento Basico",  "emoji":"🩹","preco":10, "hp_pct":0.5,"mana_pct":0.5,"desc":"Restaura 50% do HP e Mana",                        "cor":0x1D9E75},
    {"id":"completo", "nome":"Tratamento Completo", "emoji":"🏥","preco":30, "hp_pct":1.0,"mana_pct":1.0,"desc":"Restaura 100% do HP e Mana",                       "cor":0x378ADD},
    {"id":"premium",  "nome":"Suite Premium",       "emoji":"✨","preco":60, "hp_pct":1.0,"mana_pct":1.0,"desc":"HP + Mana full + remove todos os efeitos negativos","cor":0x7F77DD},
]

# ─── POOL DE CADA ROLETA COM RARIDADES ───────────────────────────
ROLETAS = {
    "classe": {
        "nome": "Classe", "emoji": "🎭",
        "pool": [
            {"id":"guerreiro",  "nome":"Guerreiro",  "emoji":"🗡️","raridade":"Comum",   "desc":"Mestre das armas corpo a corpo. Alta vida e defesa solida."},
            {"id":"arqueiro",   "nome":"Arqueiro",   "emoji":"🏹","raridade":"Comum",   "desc":"Velocidade e precisao. Especialista em ataques a distancia e criticos."},
            {"id":"mago",       "nome":"Mago",       "emoji":"🔮","raridade":"Comum",   "desc":"Domina a magia arcana. Alto dano magico mas fisicamente fragil."},
            {"id":"paladino",   "nome":"Paladino",   "emoji":"⚡","raridade":"Incomum", "desc":"Equilibrio entre fe e combate. Pode curar e causar dano sagrado."},
            {"id":"necromante", "nome":"Necromante", "emoji":"🌑","raridade":"Raro",    "desc":"Invoca mortos-vivos e drena a vida dos inimigos. Poder sombrio."},
            {"id":"arcano",     "nome":"Arcano",     "emoji":"✨","raridade":"Epico",   "desc":"Domina a magia pura. Habilidades unicas que ignoram resistencias."},
            {"id":"dracomante", "nome":"Dracomante", "emoji":"🐉","raridade":"Lendario","desc":"Sangue de dragao nas veias. O mais poderoso de todos. Lendario!"},
        ],
    },
    "skill": {
        "nome": "Skill", "emoji": "⚡",
        "pool": [
            {"id":"golpe_basico",  "nome":"Golpe Basico",  "emoji":"⚔️","raridade":"Comum",   "desc":"Ataque fisico direto e confiavel. Sem custo de mana."},
            {"id":"escudo",        "nome":"Escudo",         "emoji":"🛡️","raridade":"Comum",   "desc":"Assume postura defensiva. Reduz 50% do dano recebido por 1 turno."},
            {"id":"tiro_preciso",  "nome":"Tiro Preciso",  "emoji":"🎯","raridade":"Comum",   "desc":"Mira cuidadosa antes de disparar. +40% chance de acerto critico."},
            {"id":"bola_fogo",     "nome":"Bola de Fogo",  "emoji":"🔥","raridade":"Comum",   "desc":"Esfera de fogo que explode no alvo. 25% de chance de queimadura."},
            {"id":"drenar_vida",   "nome":"Drenar Vida",   "emoji":"🌑","raridade":"Comum",   "desc":"Absorve a forca vital do inimigo. Metade do dano vira HP para voce."},
            {"id":"baforada",      "nome":"Baforada",       "emoji":"🔥","raridade":"Comum",   "desc":"Chamas draconicas que causam dano e queimadura por 2 turnos."},
            {"id":"faisca",        "nome":"Faisca Arcana",  "emoji":"✨","raridade":"Comum",   "desc":"Descarga de energia arcana pura que ignora resistencias elementais."},
            {"id":"golpe_brutal",  "nome":"Golpe Brutal",  "emoji":"💥","raridade":"Incomum", "desc":"Concentra toda a forca em um golpe devastador. Dano dobrado."},
            {"id":"esquiva",       "nome":"Esquiva",         "emoji":"💨","raridade":"Incomum", "desc":"Rola para o lado evitando completamente o proximo ataque recebido."},
            {"id":"escudo_arcano", "nome":"Escudo Arcano", "emoji":"💜","raridade":"Incomum", "desc":"Barreira magica que absorve completamente o proximo ataque."},
            {"id":"cura",          "nome":"Cura",            "emoji":"💚","raridade":"Incomum", "desc":"Canaliza energia sagrada. Restaura 35% do HP maximo."},
            {"id":"maldicao",      "nome":"Maldicao",        "emoji":"🩸","raridade":"Incomum", "desc":"Amaldicoa o alvo com energia sombria. Veneno por 4 turnos."},
            {"id":"escamas",       "nome":"Escamas",          "emoji":"🐉","raridade":"Incomum", "desc":"Endurece as escamas draconicas. -35% de dano recebido por 3 turnos."},
            {"id":"campo_forca",   "nome":"Campo de Forca", "emoji":"🔮","raridade":"Incomum", "desc":"Campo que reflete 30% de todo dano recebido por 2 turnos."},
            {"id":"raio",          "nome":"Raio",             "emoji":"⚡","raridade":"Raro",    "desc":"Raio de alta tensao com dano massivo e 35% de chance de paralisar."},
            {"id":"tiro_multiplo", "nome":"Tiro Multiplo",  "emoji":"🏹","raridade":"Raro",    "desc":"Dispara 3 flechas simultaneamente. Cada uma causa dano individual."},
            {"id":"invocar_morto", "nome":"Invocar Morto",  "emoji":"💀","raridade":"Raro",    "desc":"Invoca um guerreiro esqueleto que ataca por voce com seu ATK."},
            {"id":"aura_sagrada",  "nome":"Aura Sagrada",   "emoji":"🌟","raridade":"Raro",    "desc":"Aura divina. +25% ATK e DEF, regenera 5% HP por turno por 3 turnos."},
            {"id":"forma_menor",   "nome":"Forma Menor",    "emoji":"🌋","raridade":"Raro",    "desc":"Forma parcial de dragao. +40% ATK e DEF, regenera HP por 3 turnos."},
            {"id":"distorcao",     "nome":"Distorcao",        "emoji":"🌀","raridade":"Raro",    "desc":"Distorce a percepcao do inimigo. -50% de precisao por 2 turnos."},
            {"id":"furia",         "nome":"Furia",             "emoji":"🔥","raridade":"Epico",   "desc":"EPICO: Entra em furia berserker. +60% ATK, regenera vida a cada golpe."},
            {"id":"sobrecarga",    "nome":"Sobrecarga",      "emoji":"✨","raridade":"Epico",   "desc":"EPICO: Libera toda energia arcana. Dano DEVASTADOR mas fica sem mana."},
            {"id":"chuva_flechas", "nome":"Chuva Flechas",  "emoji":"☄️","raridade":"Epico",   "desc":"EPICO: Dispara 5 flechas em rapida sucessao causando dano total enorme."},
            {"id":"juizo_final",   "nome":"Juizo Final",    "emoji":"☀️","raridade":"Epico",   "desc":"EPICO: Julgamento divino. Dano sagrado que escala com o HP perdido."},
            {"id":"exercito",      "nome":"Exercito Morto", "emoji":"☠️","raridade":"Epico",   "desc":"EPICO: Invoca 3 mortos-vivos que atacam simultaneamente."},
            {"id":"dragao_eterno", "nome":"Dragao Eterno",  "emoji":"💎","raridade":"Lendario","desc":"LENDARIO: Forma completa de dragao. ATK quadruplicado por 1 turno."},
            {"id":"singularidade", "nome":"Singularidade",  "emoji":"⭐","raridade":"Lendario","desc":"LENDARIO: Colapso dimensional. O maior dano do jogo. Fica sem mana."},
        ],
    },
    "arma": {
        "nome": "Arma", "emoji": "⚔️",
        "pool": [
            {"id":"espada_ferro",  "nome":"Espada de Ferro",  "emoji":"⚔️","raridade":"Comum",   "tipo":"arma","desc":"Arma basica do guerreiro"},
            {"id":"arco_madeira",  "nome":"Arco de Madeira",  "emoji":"🏹","raridade":"Comum",   "tipo":"arma","desc":"Arma basica do arqueiro"},
            {"id":"cajado_pinho",  "nome":"Cajado de Pinho",  "emoji":"🪄","raridade":"Comum",   "tipo":"arma","desc":"Arma basica do mago"},
            {"id":"espada_prata",  "nome":"Espada de Prata",  "emoji":"⚔️","raridade":"Incomum", "tipo":"arma","desc":"Dano +5"},
            {"id":"cajado_magico", "nome":"Cajado Magico",    "emoji":"🪄","raridade":"Raro",    "tipo":"arma","desc":"Magia +10"},
            {"id":"arco_elfico",   "nome":"Arco Elfico",      "emoji":"🏹","raridade":"Raro",    "tipo":"arma","desc":"Critico +15%"},
            {"id":"espada_orc",    "nome":"Espada Orc",       "emoji":"🗡️","raridade":"Raro",    "tipo":"arma","desc":"Forjada com metal orc"},
            {"id":"cajado_osso2",  "nome":"Cajado Osseo+",    "emoji":"💀","raridade":"Raro",    "tipo":"arma","desc":"Amplifica magia negra"},
            {"id":"lanca_sagrada", "nome":"Lanca Sagrada",    "emoji":"🔱","raridade":"Epico",   "tipo":"arma","desc":"Sagrado +20"},
            {"id":"garra_dragao",  "nome":"Garra de Dragao",  "emoji":"🐉","raridade":"Lendario","tipo":"arma","desc":"Arma lendaria de dragao"},
        ],
    },
    "armadura": {
        "nome": "Armadura", "emoji": "🛡️",
        "pool": [
            {"id":"armadura_couro",  "nome":"Armadura de Couro", "emoji":"🥋","raridade":"Comum",   "tipo":"armadura","desc":"Defesa +3"},
            {"id":"cota_malha",      "nome":"Cota de Malha",     "emoji":"🛡️","raridade":"Incomum", "tipo":"armadura","desc":"Defesa +8"},
            {"id":"armadura_plena",  "nome":"Armadura Plena",    "emoji":"⚙️","raridade":"Raro",    "tipo":"armadura","desc":"Defesa +15"},
            {"id":"armadura_escama", "nome":"Armadura de Escama","emoji":"🐉","raridade":"Epico",   "tipo":"armadura","desc":"Defesa +22"},
            {"id":"elmo_dragao",     "nome":"Elmo do Dragao",    "emoji":"🪖","raridade":"Lendario","tipo":"armadura","desc":"Defesa maxima"},
        ],
    },
    "poder": {
        "nome": "Poder base", "emoji": "💪",
        "pool": [
            {"id":"fraquinho","nome":"Fraquinho",     "emoji":"💀","valor":10,"raridade":"Comum",   "desc":"Stats muito baixos. Vai precisar batalhar muito para crescer."},
            {"id":"mediano",  "nome":"Mediano",       "emoji":"⚖️","valor":18,"raridade":"Comum",   "desc":"Stats equilibrados. Um comeco honesto para qualquer aventureiro."},
            {"id":"acima",    "nome":"Acima da media","emoji":"📈","valor":26,"raridade":"Incomum", "desc":"Stats acima da media. Born começo! Voce ja intimida."},
            {"id":"forte",    "nome":"Forte",         "emoji":"💪","valor":35,"raridade":"Raro",    "desc":"Stats solidos. Poucos chegam assim na criacao. Impressionante."},
            {"id":"epico",    "nome":"Epico",         "emoji":"⚡","valor":48,"raridade":"Epico",   "desc":"Stats epicos! Um dos mais fortes ja vistos na cidade."},
            {"id":"absurdo",  "nome":"Absurdo",       "emoji":"🔥","valor":65,"raridade":"Lendario","desc":"ABSURDO! Praticamente impossivel de sortear. Voce e uma lenda."},
        ],
    },
}

# Raridades em ordem crescente
RARIDADES = ["Comum", "Incomum", "Raro", "Epico", "Lendario"]
COR_RAR = {
    "Comum":0x888780,"Incomum":0x1D9E75,"Raro":0x378ADD,
    "Epico":0x7F77DD,"Lendario":0xD85A30
}
EMOJI_FICHA = {
    "Comum":"🟫","Incomum":"🟩","Raro":"🟦","Epico":"🟪","Lendario":"🟧"
}

# ─── DB ──────────────────────────────────────────────────────────

async def init_db_hospital():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS giros (
                user_id    INTEGER,
                roleta_id  TEXT,
                raridade   TEXT,
                quantidade INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, roleta_id, raridade)
            )
        """)
        await db.commit()
    print("DB hospital OK")

async def get_personagem(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM personagens WHERE user_id=?", (user_id,)) as c:
            return await c.fetchone()

async def get_giros(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT roleta_id, raridade, quantidade FROM giros WHERE user_id=? AND quantidade > 0",
            (user_id,)
        ) as c:
            rows = await c.fetchall()
    result = {}
    for r in rows:
        key = f"{r['roleta_id']}_{r['raridade']}"
        result[key] = {"roleta_id": r["roleta_id"], "raridade": r["raridade"], "quantidade": r["quantidade"]}
    return result

async def adicionar_giro(user_id, roleta_id, raridade, quantidade=1):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO giros (user_id, roleta_id, raridade, quantidade)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, roleta_id, raridade)
            DO UPDATE SET quantidade = quantidade + ?
        """, (user_id, roleta_id, raridade, quantidade, quantidade))
        await db.commit()

async def remover_giro(user_id, roleta_id, raridade):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE giros SET quantidade = quantidade - 1
            WHERE user_id=? AND roleta_id=? AND raridade=? AND quantidade > 0
        """, (user_id, roleta_id, raridade))
        await db.commit()

# ─── SORTEAR COM RARIDADE MINIMA ─────────────────────────────────

def sortear_ficha(pool, raridade_minima):
    idx_min = RARIDADES.index(raridade_minima) if raridade_minima in RARIDADES else 0
    disponiveis = [item for item in pool if RARIDADES.index(item["raridade"]) >= idx_min]
    if not disponiveis:
        disponiveis = pool

    # Peso inverso: itens mais raros tem peso menor mas sao validos
    pesos_base = {"Comum":40,"Incomum":25,"Raro":15,"Epico":8,"Lendario":3}
    pesos = [pesos_base.get(item["raridade"], 10) for item in disponiveis]
    total = sum(pesos)
    r = random.random() * total
    for i, item in enumerate(disponiveis):
        r -= pesos[i]
        if r <= 0:
            return item
    return disponiveis[-1]

async def animar_roleta(msg, opcoes, resultado, cor):
    for _ in range(8):
        op = random.choice(opcoes)
        embed = discord.Embed(
            description=f"**{op['emoji']} {op['nome']}**",
            color=0x888780
        )
        await msg.edit(embed=embed)
        await asyncio.sleep(0.15)
    desc = resultado.get("desc", "")
    valor_txt = f" — Poder {resultado['valor']}" if "valor" in resultado else ""
    embed = discord.Embed(
        title=f"{resultado['emoji']} {resultado['nome']}{valor_txt}",
        description=(f"Raridade: **{resultado.get('raridade','?')}**\n\n*{desc}*" if desc else f"Raridade: **{resultado.get('raridade','?')}**"),
        color=cor
    )
    await msg.edit(embed=embed)

# ─── /hospital ───────────────────────────────────────────────────

async def cmd_hospital(interaction: discord.Interaction):
    await interaction.response.defer()
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True)
        return

    hp_a   = p["hp_atual"]
    hp_m   = p["hp_max"]
    mana_a = p["mana_atual"] if "mana_atual" in p.keys() else 100
    mana_m = p["mana_max"]   if "mana_max"   in p.keys() else 100

    embed = discord.Embed(
        title="Hospital da Cidade",
        description=(
            f"Bem-vindo, **{p['nome']}**!\n\n"
            f"HP atual: **{hp_a}/{hp_m}**\n"
            f"Mana atual: **{mana_a}/{mana_m}**\n"
            f"Moedas: **{p['moedas']} 🪙**\n\n"
            "Escolha um plano:"
        ),
        color=0x1D9E75
    )
    for pl in PLANOS:
        embed.add_field(
            name=f"{pl['emoji']} {pl['nome']} — {pl['preco']} 🪙",
            value=pl["desc"], inline=False
        )

    opcoes = [
        discord.SelectOption(
            label=f"{pl['emoji']} {pl['nome']} — {pl['preco']} moedas",
            value=pl["id"],
            description=pl["desc"]
        ) for pl in PLANOS
    ]
    sel = discord.ui.Select(placeholder="Escolha o atendimento...", options=opcoes)

    async def escolher(inter: discord.Interaction):
        if inter.user.id != interaction.user.id:
            await inter.response.send_message("Nao e voce!", ephemeral=True)
            return
        plano = next((pl for pl in PLANOS if pl["id"] == sel.values[0]), None)
        if not plano: return
        p2 = await get_personagem(inter.user.id)
        if p2["moedas"] < plano["preco"]:
            await inter.response.send_message(
                f"Moedas insuficientes! Precisa de **{plano['preco']} 🪙**", ephemeral=True
            )
            return
        novo_hp   = int(p2["hp_max"] * plano["hp_pct"])
        mana_max  = p2["mana_max"] if "mana_max" in p2.keys() else 100
        novo_mana = int(mana_max * plano["mana_pct"])
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE personagens SET hp_atual=?, mana_atual=?, moedas=moedas-? WHERE user_id=?",
                (novo_hp, novo_mana, plano["preco"], inter.user.id)
            )
            await db.commit()
        ganho_hp = novo_hp - p2["hp_atual"]
        desc = (
            f"{plano['emoji']} **{plano['nome']}** aplicado!\n\n"
            f"HP: {p2['hp_atual']} → **{novo_hp}/{p2['hp_max']}** (+{max(0,ganho_hp)})\n"
            f"Mana: restaurada para **{novo_mana}**\n"
        )
        if plano["id"] == "premium":
            desc += "Todos os efeitos negativos removidos!\n"
        desc += f"\n-{plano['preco']} 🪙"
        await inter.response.edit_message(
            embed=discord.Embed(title="Atendimento concluido!", description=desc, color=plano["cor"]),
            view=None
        )

    sel.callback = escolher
    v = discord.ui.View(timeout=60)
    v.add_item(sel)
    await interaction.followup.send(embed=embed, view=v)

# ─── /girar ──────────────────────────────────────────────────────

async def cmd_girar(interaction: discord.Interaction):
    await interaction.response.defer()
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True)
        return

    giros = await get_giros(interaction.user.id)
    if not giros:
        await interaction.followup.send(
            embed=discord.Embed(
                title="Sem giros disponiveis",
                description=(
                    "Voce nao tem giros no momento.\n\n"
                    "**Como conseguir:**\n"
                    "• Admin pode conceder com `/set-giros`\n"
                    "• Completar missoes especiais\n"
                    "• Top 3 em torneios"
                ),
                color=0x888780
            ),
            ephemeral=True
        )
        return

    # Monta lista de fichas disponíveis
    desc_giros = ""
    opcoes = []
    for key, info in giros.items():
        roleta = ROLETAS.get(info["roleta_id"])
        if not roleta: continue
        ficha_emoji = EMOJI_FICHA.get(info["raridade"], "⬜")
        label = f"{ficha_emoji} {roleta['nome']} — {info['raridade']} ({info['quantidade']}x)"
        opcoes.append(discord.SelectOption(
            label=label,
            value=key,
            description=f"Sorteia itens {info['raridade']} ou acima"
        ))
        desc_giros += f"{ficha_emoji} **{roleta['nome']} {info['raridade']}**: {info['quantidade']}x\n"

    if not opcoes:
        await interaction.followup.send("Sem giros disponiveis!", ephemeral=True)
        return

    embed = discord.Embed(
        title="Seus Giros Disponiveis",
        description=f"Escolha qual ficha usar:\n\n{desc_giros}",
        color=0x7F77DD
    )

    sel = discord.ui.Select(placeholder="Qual ficha usar?", options=opcoes[:25])

    async def girar(inter: discord.Interaction):
        if inter.user.id != interaction.user.id:
            await inter.response.send_message("Nao e voce!", ephemeral=True)
            return
        await inter.response.defer()

        key = sel.values[0]
        info = giros.get(key)
        if not info: return

        roleta    = ROLETAS.get(info["roleta_id"])
        raridade  = info["raridade"]
        if not roleta: return

        await remover_giro(inter.user.id, info["roleta_id"], raridade)

        resultado = sortear_ficha(roleta["pool"], raridade)
        cor = COR_RAR.get(resultado.get("raridade", "Comum"), 0x888780)

        msg_anim = await inter.followup.send(
            embed=discord.Embed(description="Girando...", color=0x888780),
            wait=True
        )
        await animar_roleta(msg_anim, roleta["pool"], resultado, cor)
        await asyncio.sleep(0.5)

        # Aplica resultado
        aplicado = ""
        async with aiosqlite.connect(DB_PATH) as db:
            rid = info["roleta_id"]
            if rid == "skill":
                await db.execute(
                    "INSERT OR IGNORE INTO skills_desbloqueadas(user_id,skill_id) VALUES(?,?)",
                    (inter.user.id, resultado["id"])
                )
                aplicado = f"Skill **{resultado['nome']}** adicionada ao seu arsenal!"

            elif rid in ("arma", "armadura"):
                tipo = resultado.get("tipo", rid)
                async with db.execute(
                    "SELECT id FROM inventario WHERE user_id=? AND item_id=?",
                    (inter.user.id, resultado["id"])
                ) as c:
                    ex = await c.fetchone()
                if ex:
                    await db.execute("UPDATE inventario SET quantidade=quantidade+1 WHERE id=?", (ex[0],))
                else:
                    await db.execute("""
                        INSERT INTO inventario(user_id,item_id,nome,tipo,raridade,emoji,descricao)
                        VALUES(?,?,?,?,?,?,?)
                    """, (inter.user.id, resultado["id"], resultado["nome"],
                          tipo, resultado["raridade"], resultado["emoji"],
                          resultado.get("desc", "Obtido via roleta")))
                aplicado = f"**{resultado['nome']}** adicionada ao inventario!"

            elif rid == "poder":
                await db.execute(
                    "UPDATE personagens SET poder_id=?, poder_valor=? WHERE user_id=?",
                    (resultado["id"], resultado.get("valor", 10), inter.user.id)
                )
                aplicado = f"Poder base alterado para **{resultado['nome']}** ({resultado.get('valor', '?')})!"

            elif rid == "classe":
                await db.execute(
                    "UPDATE personagens SET classe_id=?, raridade=? WHERE user_id=?",
                    (resultado["id"], resultado["raridade"], inter.user.id)
                )
                aplicado = f"Classe alterada para **{resultado['nome']}** ({resultado['raridade']})!"

            await db.commit()

        giros_restantes = await get_giros(inter.user.id)
        total_restante  = sum(v["quantidade"] for v in giros_restantes.values())

        ficha_emoji = EMOJI_FICHA.get(raridade, "⬜")
        desc_item = resultado.get("desc", "")
        valor_txt = f" (Poder {resultado['valor']})" if "valor" in resultado else ""
        ficha_emoji = EMOJI_FICHA.get(raridade, "⬜")
        desc_item = resultado.get("desc", "")
        valor_txt = f" (Poder {resultado['valor']})" if "valor" in resultado else ""
        desc_txt = f"\n*{desc_item}*" if desc_item else ""
        embed_result = discord.Embed(
            title=f"Resultado — Ficha {ficha_emoji} {raridade}",
            description=f"{resultado['emoji']} **{resultado['nome']}**{valor_txt}\nRaridade: **{resultado.get('raridade','?')}**{desc_txt}\n\n{aplicado}\n\nGiros restantes: **{total_restante}**",
            color=cor
        )
        await msg_anim.edit(embed=embed_result)

    sel.callback = girar
    v = discord.ui.View(timeout=60)

    sel.callback = girar
    v = discord.ui.View(timeout=60)
    v.add_item(sel)
    await interaction.followup.send(embed=embed, view=v)

# ─── /set-giros (admin) ──────────────────────────────────────────

async def cmd_set_giros(interaction: discord.Interaction, jogador: discord.Member):
    await interaction.response.defer(ephemeral=True)

    p = await get_personagem(jogador.id)
    if not p:
        await interaction.followup.send(f"{jogador.display_name} nao tem personagem!", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"Dar giros para {jogador.display_name}",
        description="Escolha a roleta, a raridade da ficha e a quantidade:",
        color=0x7F77DD
    )

    sel_roleta = discord.ui.Select(
        placeholder="Escolha a roleta...",
        options=[
            discord.SelectOption(
                label=f"{r['emoji']} {r['nome']}",
                value=rid,
                description=f"Roleta de {r['nome']}"
            ) for rid, r in ROLETAS.items()
        ],
        row=0
    )

    sel_raridade = discord.ui.Select(
        placeholder="Raridade da ficha...",
        options=[
            discord.SelectOption(
                label=f"{EMOJI_FICHA[rar]} Ficha {rar}",
                value=rar,
                description=f"Sorteia {rar} ou acima"
            ) for rar in RARIDADES
        ],
        row=1
    )

    sel_qtd = discord.ui.Select(
        placeholder="Quantidade...",
        options=[
            discord.SelectOption(label=f"{i}x giro(s)", value=str(i))
            for i in [1, 2, 3, 5, 10, 20]
        ],
        row=2
    )

    escolhas = {"roleta": None, "raridade": None, "qtd": 1}
    btn = discord.ui.Button(label="Confirmar", style=discord.ButtonStyle.success, disabled=True, row=3)

    async def on_roleta(inter):
        escolhas["roleta"] = sel_roleta.values[0]
        if escolhas["roleta"] and escolhas["raridade"]: btn.disabled = False
        await inter.response.edit_message(view=v)

    async def on_raridade(inter):
        escolhas["raridade"] = sel_raridade.values[0]
        if escolhas["roleta"] and escolhas["raridade"]: btn.disabled = False
        await inter.response.edit_message(view=v)

    async def on_qtd(inter):
        escolhas["qtd"] = int(sel_qtd.values[0])
        await inter.response.edit_message(view=v)

    async def on_confirmar(inter):
        if inter.user.id != interaction.user.id: return
        rid = escolhas["roleta"]
        rar = escolhas["raridade"]
        qtd = escolhas["qtd"]
        roleta = ROLETAS.get(rid)
        if not roleta or not rar: return

        await adicionar_giro(jogador.id, rid, rar, qtd)

        ficha_emoji = EMOJI_FICHA.get(rar, "⬜")
        await inter.response.edit_message(
            embed=discord.Embed(
                title="Giros adicionados!",
                description=(
                    f"{ficha_emoji} **{qtd}x Ficha {rar}** de **{roleta['nome']}**\n"
                    f"adicionado para {jogador.mention}!"
                ),
                color=COR_RAR.get(rar, 0x888780)
            ),
            view=None
        )

    sel_roleta.callback  = on_roleta
    sel_raridade.callback = on_raridade
    sel_qtd.callback     = on_qtd
    btn.callback         = on_confirmar

    v = discord.ui.View(timeout=120)
    v.add_item(sel_roleta)
    v.add_item(sel_raridade)
    v.add_item(sel_qtd)
    v.add_item(btn)

    await interaction.followup.send(embed=embed, view=v, ephemeral=True)