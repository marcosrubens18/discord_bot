# expedicao.py — Sistema de Expedições Narrativas com IA
import discord
import asyncio
import json
from datetime import datetime, timedelta
from db import get_pool
from expedicao_ia import chamar_gemini, prompt_sistema, resumir_historico, gerar_cronica
from expedicao_combate import rodar_combate_expedicao

# ─── DB ───────────────────────────────────────────────────────────

async def init_db_expedicao():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS expedicoes (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                descricao TEXT DEFAULT '',
                contexto TEXT DEFAULT '',
                nivel_minimo INTEGER DEFAULT 1,
                max_participantes INTEGER DEFAULT 5,
                fim_inscricoes TIMESTAMP,
                recompensa_ouro INTEGER DEFAULT 0,
                recompensa_xp INTEGER DEFAULT 0,
                recompensa_fichas INTEGER DEFAULT 0,
                monstros_permitidos JSONB DEFAULT '[]',
                dificuldade TEXT DEFAULT 'Media',
                status TEXT DEFAULT 'inscricoes',
                canal_id BIGINT DEFAULT 0,
                cargo_id BIGINT DEFAULT 0,
                criado_por BIGINT,
                criado_em TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS expedicao_participantes (
                id SERIAL PRIMARY KEY,
                expedicao_id INTEGER REFERENCES expedicoes(id),
                user_id BIGINT,
                nome TEXT,
                classe_id TEXT,
                nivel INTEGER DEFAULT 1,
                rank TEXT DEFAULT 'F',
                sobreviveu BOOLEAN DEFAULT TRUE,
                inscrito_em TIMESTAMP DEFAULT NOW(),
                UNIQUE(expedicao_id, user_id)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS expedicao_historico (
                id SERIAL PRIMARY KEY,
                expedicao_id INTEGER REFERENCES expedicoes(id),
                tipo TEXT DEFAULT 'narrativa',
                conteudo TEXT,
                criado_em TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS expedicao_resumos (
                id SERIAL PRIMARY KEY,
                expedicao_id INTEGER REFERENCES expedicoes(id),
                resumo TEXT,
                criado_em TIMESTAMP DEFAULT NOW()
            )
        """)
    print("DB expedicao OK!")

# ─── ESTADO ATIVO DAS EXPEDIÇÕES ─────────────────────────────────
EXPEDICOES_ATIVAS: dict = {}
EXPEDICOES_LOCKS = {}

async def get_exp_lock(exp_id):
    if exp_id not in EXPEDICOES_LOCKS:
        EXPEDICOES_LOCKS[exp_id] = asyncio.Lock()
    return EXPEDICOES_LOCKS[exp_id]

# ─── MODAL CRIAR EXPEDIÇÃO ────────────────────────────────────────

class ExpedicaoModal(discord.ui.Modal, title="Criar Expedição Narrativa"):
    nome_input = discord.ui.TextInput(
        label="Nome da Expedição",
        placeholder="Ex: O Farol Negro",
        max_length=60
    )
    descricao_input = discord.ui.TextInput(
        label="Descrição curta",
        placeholder="Ex: Uma luz voltou a aparecer em farol abandonado...",
        max_length=200
    )
    contexto_input = discord.ui.TextInput(
        label="Contexto completo para a IA",
        style=discord.TextStyle.paragraph,
        placeholder="Descreva o cenário, objetivos e atmosfera da expedição...",
        max_length=800
    )
    config_input = discord.ui.TextInput(
        label="NívelMin|MaxJogadores|HorasInscrição|Dific.",
        placeholder="Ex: 5|5|24|Difícil",
        max_length=40
    )
    recomp_input = discord.ui.TextInput(
        label="Recomp: ouro/xp/fichas | Monstros",
        placeholder="Ex: 5000|10000|1 | Goblin,Vampiro,Dragão",
        max_length=200
    )

    def __init__(self, guild, canal_anuncio, bot):
        super().__init__()
        self.discord_guild = guild
        self.canal_anuncio = canal_anuncio
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await init_db_expedicao()

        nivel_min = 1
        max_p = 5
        horas = 24
        dific = "Media"
        try:
            partes = self.config_input.value.split("|")
            nivel_min = int(partes[0].strip()) if partes[0].strip().isdigit() else 1
            max_p = int(partes[1].strip()) if len(partes) > 1 and partes[1].strip().isdigit() else 5
            horas = int(partes[2].strip()) if len(partes) > 2 and partes[2].strip().isdigit() else 24
            dific = partes[3].strip() if len(partes) > 3 else "Media"
        except:
            pass

        ouro = xp = fichas = 0
        monstros = []
        try:
            partes_r = self.recomp_input.value.split("|")
            recomp = partes_r[0].strip().split("/")
            if len(recomp) >= 1:
                ouro = int("".join(filter(str.isdigit, recomp[0])) or "0")
            if len(recomp) >= 2:
                xp = int("".join(filter(str.isdigit, recomp[1])) or "0")
            if len(recomp) >= 3:
                fichas = int("".join(filter(str.isdigit, recomp[2])) or "0")
            if len(partes_r) >= 2:
                monstros = [m.strip() for m in partes_r[1].split(",") if m.strip()]
        except:
            pass

        fim = datetime.utcnow() + timedelta(hours=horas)
        pool = await get_pool()
        async with pool.acquire() as conn:
            exp = await conn.fetchrow("""
                INSERT INTO expedicoes
                (nome,descricao,contexto,nivel_minimo,max_participantes,
                 fim_inscricoes,recompensa_ouro,recompensa_xp,recompensa_fichas,
                 monstros_permitidos,dificuldade,status,criado_por)
                VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,'inscricoes',$12) RETURNING *
            """, self.nome_input.value, self.descricao_input.value, self.contexto_input.value,
                nivel_min, max_p, fim, ouro, xp, fichas,
                json.dumps(monstros), dific, interaction.user.id)

        monstros_txt = ", ".join(monstros) if monstros else "A definir"
        recomp_txt = f"{ouro} ouro | {xp} XP | {fichas} fichas de roleta"
        embed = discord.Embed(
            title=f"🧭 {self.nome_input.value}",
            description=self.descricao_input.value,
            color=0x7F77DD
        )
        embed.add_field(name="Dificuldade", value=dific, inline=True)
        embed.add_field(name="Nível mínimo", value=str(nivel_min), inline=True)
        embed.add_field(name="Vagas", value=f"0/{max_p}", inline=True)
        embed.add_field(name="Inscrições até", value=f"<t:{int(fim.timestamp())}:R>", inline=True)
        embed.add_field(name="Recompensas", value=recomp_txt, inline=False)
        embed.add_field(name="Monstros", value=monstros_txt, inline=False)
        embed.set_footer(text=f"Expedição #{exp['id']} | Clique para participar!")

        class InscreverView(discord.ui.View):
            def __init__(self): 
                super().__init__(timeout=None)
            @discord.ui.button(label="🧭 Participar da Expedição!", style=discord.ButtonStyle.primary,
                               custom_id=f"exp_inscricao_{exp['id']}")
            async def btn(self, inter, b):
                await _inscrever_expedicao(inter, exp["id"])

        msg = await self.canal_anuncio.send(embed=embed, view=InscreverView())
        async with pool.acquire() as conn:
            await conn.execute("UPDATE expedicoes SET canal_id=$1 WHERE id=$2",
                               msg.channel.id, exp["id"])

        await interaction.followup.send(
            f"✅ Expedição **{self.nome_input.value}** criada! ID: `{exp['id']}`\n"
            f"Inscrições abertas por {horas}h em {self.canal_anuncio.mention}\n\n"
            f"Quando quiser iniciar: `/expedicao-iniciar {exp['id']}`",
            ephemeral=True
        )
        asyncio.create_task(_agendar_inscricoes(exp["id"], horas * 3600, self.discord_guild))

async def _agendar_inscricoes(exp_id, segundos, guild):
    await asyncio.sleep(segundos)
    await _fechar_inscricoes(exp_id, guild)

async def _inscrever_expedicao(interaction: discord.Interaction, exp_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        exp = await conn.fetchrow(
            "SELECT * FROM expedicoes WHERE id=$1 AND status='inscricoes'", exp_id)
        if not exp:
            await interaction.response.send_message("Inscrições encerradas!", ephemeral=True)
            return
        p = await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", interaction.user.id)
        if not p:
            await interaction.response.send_message("Crie seu personagem primeiro!", ephemeral=True)
            return
        if p["nivel"] < exp["nivel_minimo"]:
            await interaction.response.send_message(
                f"Nível insuficiente! Precisa de nível {exp['nivel_minimo']}.", ephemeral=True)
            return
        ex = await conn.fetchrow(
            "SELECT id FROM expedicao_participantes WHERE expedicao_id=$1 AND user_id=$2",
            exp_id, interaction.user.id)
        if ex:
            await interaction.response.send_message("Você já está inscrito!", ephemeral=True)
            return
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM expedicao_participantes WHERE expedicao_id=$1", exp_id)
        if total >= exp["max_participantes"]:
            await interaction.response.send_message("Vagas esgotadas!", ephemeral=True)
            return
        from catalogo import get_rank
        rank = get_rank(p["nivel"])["rank"]
        await conn.execute("""
            INSERT INTO expedicao_participantes(expedicao_id,user_id,nome,classe_id,nivel,rank)
            VALUES($1,$2,$3,$4,$5,$6)
        """, exp_id, interaction.user.id, p["nome"], p["classe_id"], p["nivel"], rank)
        novo_total = total + 1
    await interaction.response.send_message(
        f"✅ Inscrito na expedição **{exp['nome']}**! ({novo_total}/{exp['max_participantes']})\n"
        f"Aguarde o encerramento das inscrições para o canal privado ser criado.",
        ephemeral=True)
    if novo_total >= exp["max_participantes"]:
        asyncio.create_task(_fechar_inscricoes(exp_id, interaction.guild))

async def _fechar_inscricoes(exp_id: int, guild: discord.Guild):
    pool = await get_pool()
    async with pool.acquire() as conn:
        exp = await conn.fetchrow(
            "SELECT * FROM expedicoes WHERE id=$1 AND status='inscricoes'", exp_id)
        if not exp:
            return
        participantes = await conn.fetch(
            "SELECT * FROM expedicao_participantes WHERE expedicao_id=$1", exp_id)
        if not participantes:
            await conn.execute("UPDATE expedicoes SET status='cancelada' WHERE id=$1", exp_id)
            return
        await conn.execute("UPDATE expedicoes SET status='preparacao' WHERE id=$1", exp_id)

    cargo = None
    try:
        cargo = await guild.create_role(
            name=f"🧭 Exp — {exp['nome'][:30]}",
            color=discord.Color.purple(), mentionable=True)
        for p in participantes:
            member = guild.get_member(p["user_id"])
            if member:
                await member.add_roles(cargo)
    except Exception as e:
        print(f"Erro cargo exp: {e}")

    try:
        cat = discord.utils.get(guild.categories, name="EXPEDIÇÕES") or \
              await guild.create_category("EXPEDIÇÕES")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        if cargo:
            overwrites[cargo] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        nome_canal = f"🧭┃expedicao-{exp['nome'].lower()[:25].replace(' ', '-')}"
        canal = await guild.create_text_channel(nome_canal, category=cat, overwrites=overwrites)

        async with pool.acquire() as conn:
            await conn.execute("UPDATE expedicoes SET canal_id=$1, cargo_id=$2 WHERE id=$3",
                               canal.id, cargo.id if cargo else 0, exp_id)

        nomes = ", ".join([p["nome"] for p in participantes])
        embed_prep = discord.Embed(
            title=f"🧭 {exp['nome']} — Sala de Preparação",
            description=(
                f"**Bem-vindos, aventureiros!**\n\n"
                f"{exp['descricao']}\n\n"
                f"**Participantes:** {nomes}\n\n"
                f"Usem este canal para combinar o horário da aventura.\n"
                f"Quando todos estiverem prontos, um administrador irá usar:\n"
                f"`/expedicao-iniciar {exp_id}`\n\n"
                f"**Recompensas:**\n"
                f"🪙 {exp['recompensa_ouro']} ouro | ⭐ {exp['recompensa_xp']} XP | 🎰 {exp['recompensa_fichas']} fichas"
            ),
            color=0x7F77DD
        )
        await canal.send(embed=embed_prep)
    except Exception as e:
        print(f"Erro canal exp: {e}")

# ─── INICIAR EXPEDIÇÃO ────────────────────────────────────────────

async def cmd_expedicao_iniciar(interaction: discord.Interaction, exp_id: int):
    await interaction.response.defer(ephemeral=True)
    pool = await get_pool()
    async with pool.acquire() as conn:
        exp = await conn.fetchrow(
            "SELECT * FROM expedicoes WHERE id=$1 AND status IN ('preparacao','inscricoes')", exp_id)
        if not exp:
            await interaction.followup.send("Expedição não encontrada ou já iniciada!", ephemeral=True)
            return
        participantes = await conn.fetch(
            "SELECT ep.*, p.hp_atual, p.hp_max, p.mana_atual, p.mana_max, p.ataque, p.defesa, p.raca_id "
            "FROM expedicao_participantes ep "
            "JOIN personagens p ON ep.user_id=p.user_id "
            "WHERE ep.expedicao_id=$1", exp_id)
        await conn.execute("UPDATE expedicoes SET status='ativa' WHERE id=$1", exp_id)

    canal = interaction.guild.get_channel(exp["canal_id"])
    if not canal:
        await interaction.followup.send("Canal da expedição não encontrado!", ephemeral=True)
        return

    monstros = json.loads(exp["monstros_permitidos"]) if exp["monstros_permitidos"] else []
    p_list = [dict(p) for p in participantes]
    exp_dict = dict(exp)
    exp_dict["monstros_permitidos"] = monstros

    EXPEDICOES_ATIVAS[exp_id] = {
        "expedicao": exp_dict,
        "participantes": p_list,
        "participantes_ids": [p["user_id"] for p in p_list],
        "participantes_vivos": [p["user_id"] for p in p_list],
        "historico_ia": [],
        "historico_db": [],
        "canal": canal,
        "guild": interaction.guild,
        "bot": interaction.client,
        "turno_escolha": False,
    }

    await interaction.followup.send(
        f"✅ Expedição **{exp['nome']}** iniciada! A IA está narrando em {canal.mention}",
        ephemeral=True)

    asyncio.create_task(_loop_expedicao(exp_id))

async def _loop_expedicao(exp_id: int):
    """Loop principal da expedição — narrativa com IA."""
    estado = EXPEDICOES_ATIVAS.get(exp_id)
    if not estado:
        return

    async def salvar_historico(tipo: str, conteudo: str):
        estado["historico_db"].append({"tipo": tipo, "conteudo": conteudo})
        # Também salva no historico_ia
        role = "user" if tipo in ("escolha_resultado", "combate_resultado") else "model"
        estado["historico_ia"].append({
            "role": role,
            "content": conteudo[:500]
        })
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO expedicao_historico(expedicao_id,tipo,conteudo) VALUES($1,$2,$3)",
                exp_id, tipo, conteudo[:1000])

    async def obter_resposta_ia(mensagem_usuario: str = None) -> dict:
        hist = estado["historico_ia"]
        
        if mensagem_usuario:
            hist.append({"role": "user", "content": mensagem_usuario})
        
        if len(hist) > 30:
            # Mantém contexto inicial
            inicio = hist[0] if hist else None
            hist = hist[-20:]
            if inicio and inicio not in hist:
                hist.insert(0, inicio)
            estado["historico_ia"] = hist

        sistema = prompt_sistema(estado["expedicao"], estado["participantes"])
        return await chamar_gemini(hist, sistema)

    # Primeira narração
    resposta = await obter_resposta_ia("Inicie a expedição narrando a chegada dos aventureiros.")
    
    # Loop principal
    while True:
        # Verifica se ainda tem participantes vivos
        if not estado.get("participantes_vivos"):
            await _encerrar_expedicao(exp_id, sucesso=False)
            return
        
        tipo = resposta.get("tipo", "narrativa")
        
        if tipo == "fim":
            await _processar_resposta_fim(exp_id, resposta, salvar_historico)
            break
        elif tipo == "combate":
            resposta = await _processar_resposta_combate(exp_id, resposta, salvar_historico, estado)
        elif tipo == "escolha":
            resposta = await _processar_resposta_escolha(exp_id, resposta, salvar_historico, estado)
        else:
            await _processar_resposta_narrativa(exp_id, resposta, salvar_historico, estado["canal"])
            # Pega próxima resposta da IA
            resposta = await obter_resposta_ia()
        
        await asyncio.sleep(1)

async def _processar_resposta_narrativa(exp_id: int, resposta: dict, salvar_historico, canal):
    """Processa resposta narrativa simples."""
    texto = resposta.get("texto", "...")
    embed = discord.Embed(description=texto, color=0x7F77DD)
    embed.set_author(name="📖 Mestre da Expedição")
    await canal.send(embed=embed)
    await salvar_historico("narrativa", texto)

async def _processar_resposta_escolha(exp_id: int, resposta: dict, salvar_historico, estado):
    """Processa escolha dos jogadores."""
    canal = estado["canal"]
    bot = estado["bot"]
    texto = resposta.get("texto", "O que vocês fazem?")
    opcoes = resposta.get("opcoes", [])
    
    embed = discord.Embed(
        title="🤔 Uma escolha se apresenta...",
        description=texto,
        color=0xE4AF3C
    )
    if opcoes:
        embed.add_field(
            name="Opções",
            value="\n".join([f"**{i+1}.** {op}" for i, op in enumerate(opcoes)]),
            inline=False
        )
    embed.set_footer(text="Envie sua escolha neste canal — todos participam!")
    await canal.send(embed=embed)
    await salvar_historico("escolha", f"{texto} | Opções: {opcoes}")

    # Coleta respostas
    estado["turno_escolha"] = True
    respostas_jogadores = []
    ids_vivos = estado.get("participantes_vivos", [])
    ids_responderam = set()

    def check(msg):
        return (msg.channel.id == canal.id and
                msg.author.id in ids_vivos and
                msg.author.id not in ids_responderam)

    try:
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < 120:
            try:
                msg = await bot.wait_for("message", check=check, timeout=10)
                ids_responderam.add(msg.author.id)
                respostas_jogadores.append(f"{msg.author.display_name}: {msg.content}")
                if len(ids_responderam) >= len(ids_vivos):
                    break
            except asyncio.TimeoutError:
                if len(ids_responderam) > 0:
                    break
    except Exception as e:
        print(f"Erro na coleta de respostas: {e}")

    estado["turno_escolha"] = False
    respostas_txt = "\n".join(respostas_jogadores) if respostas_jogadores else "Ninguém respondeu."
    await salvar_historico("escolha_resultado", respostas_txt)

    # Envia para IA continuar
    from expedicao_ia import chamar_gemini
    sistema = prompt_sistema(estado["expedicao"], estado["participantes"])
    estado["historico_ia"].append({
        "role": "user",
        "content": f"Os aventureiros responderam:\n{respostas_txt}\nContinue a narrativa."
    })
    nova_resp = await chamar_gemini(estado["historico_ia"], sistema)
    estado["historico_ia"].append({
        "role": "model",
        "content": json.dumps(nova_resp, ensure_ascii=False)
    })
    return nova_resp

async def _processar_resposta_combate(exp_id: int, resposta: dict, salvar_historico, estado):
    """Processa combate."""
    canal = estado["canal"]
    nome_m = resposta.get("monstro", "Goblin")
    quantidade = resposta.get("quantidade", 1)
    narrativa = resposta.get("narrativa", "")

    if narrativa:
        embed_n = discord.Embed(description=narrativa, color=0xE24B4A)
        embed_n.set_author(name="⚔️ Combate se inicia!")
        await canal.send(embed=embed_n)

    await salvar_historico("combate", f"vs {nome_m} x{quantidade}")

    # Executa combate
    ids_vivos = estado["participantes_vivos"]
    resultado = await rodar_combate_expedicao(canal, ids_vivos, nome_m, quantidade)

    # Atualiza participantes vivos
    estado["participantes_vivos"] = resultado["sobreviventes"]
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        for uid in resultado["derrotados"]:
            await conn.execute(
                "UPDATE expedicao_participantes SET sobreviveu=FALSE WHERE expedicao_id=$1 AND user_id=$2",
                exp_id, uid)

    resultado_txt = (
        f"Resultado do combate contra {nome_m}:\n"
        f"Vitória: {resultado['sucesso']}\n"
        f"Sobreviventes: {', '.join(resultado['sobreviventes_nomes']) or 'Nenhum'}\n"
        f"Derrotados: {', '.join(resultado['derrotados_nomes']) or 'Nenhum'}"
    )
    await salvar_historico("combate_resultado", resultado_txt)

    # Se todos morreram, encerra
    if not resultado["sobreviventes"]:
        await _encerrar_expedicao(exp_id, sucesso=False)
        return None

    # Continua narrativa
    sistema = prompt_sistema(estado["expedicao"], estado["participantes"])
    estado["historico_ia"].append({
        "role": "user",
        "content": resultado_txt + "\nContinue a narrativa considerando o resultado."
    })
    from expedicao_ia import chamar_gemini as cg
    nova_resp = await cg(estado["historico_ia"], sistema)
    estado["historico_ia"].append({
        "role": "model",
        "content": json.dumps(nova_resp, ensure_ascii=False)
    })
    return nova_resp

async def _processar_resposta_fim(exp_id: int, resposta: dict, salvar_historico):
    """Processa fim da expedição."""
    sucesso = resposta.get("sucesso", True)
    narrativa = resposta.get("narrativa", "")
    estado = EXPEDICOES_ATIVAS.get(exp_id)
    
    if estado and narrativa:
        embed_fim = discord.Embed(
            title="🏁 A expedição chegou ao fim!",
            description=narrativa,
            color=0x1D9E75 if sucesso else 0xE24B4A
        )
        await estado["canal"].send(embed=embed_fim)
    
    await salvar_historico("fim", narrativa)
    await _encerrar_expedicao(exp_id, sucesso=sucesso)

# ─── ENCERRAR EXPEDIÇÃO ───────────────────────────────────────────

async def _encerrar_expedicao(exp_id: int, sucesso: bool):
    estado = EXPEDICOES_ATIVAS.get(exp_id)
    pool = await get_pool()

    async with pool.acquire() as conn:
        participantes = await conn.fetch(
            "SELECT * FROM expedicao_participantes WHERE expedicao_id=$1 AND sobreviveu=TRUE", exp_id)
        await conn.execute("UPDATE expedicoes SET status='finalizada' WHERE id=$1", exp_id)

    # Distribui recompensas
    if sucesso and participantes and estado:
        exp = estado["expedicao"]
        total = len(participantes)
        ouro_cada = exp["recompensa_ouro"] // total if total else 0
        xp_cada = exp["recompensa_xp"] // total if total else 0
        fichas_cada = exp["recompensa_fichas"]

        async with pool.acquire() as conn:
            for p in participantes:
                await conn.execute(
                    "UPDATE personagens SET moedas=moedas+$1, xp=xp+$2 WHERE user_id=$3",
                    ouro_cada, xp_cada, p["user_id"])
                if fichas_cada > 0:
                    await conn.execute("""
                        INSERT INTO giros(user_id,roleta_id,raridade,quantidade)
                        VALUES($1,'skill','Lendario',$2)
                        ON CONFLICT(user_id,roleta_id,raridade)
                        DO UPDATE SET quantidade=giros.quantidade+$2
                    """, p["user_id"], fichas_cada)

        if estado and estado.get("canal"):
            embed_recomp = discord.Embed(
                title="🏆 Recompensas distribuídas!",
                description=(
                    f"Cada aventureiro recebeu:\n"
                    f"🪙 **{ouro_cada} moedas**\n"
                    f"⭐ **{xp_cada} XP**\n"
                    f"🎰 **{fichas_cada} ficha(s) de roleta**"
                ),
                color=0xE4AF3C
            )
            await estado["canal"].send(embed=embed_recomp)

    # Gera crônica se tiver estado
    if estado:
        p_list = [dict(p) for p in participantes] or estado["participantes"]
        cronica = await gerar_cronica(estado["expedicao"], p_list, estado["historico_db"], sucesso)

        canal_cronicas = discord.utils.get(estado["guild"].text_channels, name="📚┃cronicas-de-eldoria")
        if not canal_cronicas:
            canal_cronicas = discord.utils.get(estado["guild"].text_channels, name="cronicas-de-eldoria")
        if canal_cronicas:
            async with pool.acquire() as conn:
                num = await conn.fetchval("SELECT COUNT(*) FROM expedicoes WHERE status='finalizada'")
            embed_cronica = discord.Embed(
                title=f"📖 Crônica #{num} — {estado['expedicao']['nome']}",
                description=cronica[:2000],
                color=0x7F77DD if sucesso else 0x888780
            )
            embed_cronica.add_field(
                name="Resultado", value="✅ Sucesso" if sucesso else "❌ Derrota", inline=True)
            nomes = ", ".join([p["nome"] for p in p_list])
            embed_cronica.add_field(name="Participantes", value=nomes, inline=False)
            embed_cronica.set_footer(text="Crônicas de Eldoria — Villa Eldoria RPG")
            await canal_cronicas.send(embed=embed_cronica)

    # Aguarda e limpa canal/cargo
    await asyncio.sleep(10)  # 10 segundos para visualização
    
    if estado:
        try:
            if estado.get("canal"):
                await estado["canal"].delete(reason="Expedição encerrada")
        except Exception as e:
            print(f"Erro ao deletar canal: {e}")
        
        try:
            cargo_id = estado["expedicao"].get("cargo_id", 0)
            if cargo_id:
                cargo = estado["guild"].get_role(cargo_id)
                if cargo:
                    await cargo.delete(reason="Expedição encerrada")
        except Exception as e:
            print(f"Erro ao deletar cargo: {e}")

    EXPEDICOES_ATIVAS.pop(exp_id, None)
    if exp_id in EXPEDICOES_LOCKS:
        del EXPEDICOES_LOCKS[exp_id]

# ─── COMANDOS EXPORTADOS ──────────────────────────────────────────

async def cmd_expedicao_criar(interaction: discord.Interaction, canal, bot):
    await interaction.response.send_modal(ExpedicaoModal(interaction.guild, canal, bot))

async def cmd_expedicao_status(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    pool = await get_pool()
    async with pool.acquire() as conn:
        exps = await conn.fetch("""
            SELECT e.*, COUNT(ep.id) as inscritos
            FROM expedicoes e
            LEFT JOIN expedicao_participantes ep ON e.id=ep.expedicao_id
            WHERE e.status NOT IN ('finalizada','cancelada')
            GROUP BY e.id ORDER BY e.id DESC LIMIT 10
        """)
    if not exps:
        await interaction.followup.send("Nenhuma expedição ativa!", ephemeral=True)
        return

    embed = discord.Embed(title="🧭 Expedições Ativas", color=0x7F77DD)
    status_map = {"inscricoes": "📋 Inscrições", "preparacao": "🏕️ Preparação", "ativa": "⚔️ Em Aventura"}
    for e in exps:
        embed.add_field(
            name=f"{e['nome']} #{e['id']}",
            value=f"{status_map.get(e['status'], e['status'])} | {e['inscritos']}/{e['max_participantes']} jogadores",
            inline=False
        )
    await interaction.followup.send(embed=embed, ephemeral=True)

async def cmd_expedicao_encerrar(interaction: discord.Interaction, exp_id: int, sucesso: bool = True):
    await interaction.response.defer(ephemeral=True)
    pool = await get_pool()
    async with pool.acquire() as conn:
        exp = await conn.fetchrow("SELECT * FROM expedicoes WHERE id=$1", exp_id)
    if not exp:
        await interaction.followup.send("Expedição não encontrada!", ephemeral=True)
        return

    if exp_id in EXPEDICOES_ATIVAS:
        await _encerrar_expedicao(exp_id, sucesso=sucesso)
    else:
        async with pool.acquire() as conn:
            await conn.execute("UPDATE expedicoes SET status='finalizada' WHERE id=$1", exp_id)
    await interaction.followup.send(
        f"✅ Expedição **{exp['nome']}** encerrada! Resultado: {'Sucesso' if sucesso else 'Derrota'}",
        ephemeral=True)
