# -*- coding: utf-8 -*-
import sys, io, os, random, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import discord
from discord import app_commands
from discord.ext import commands

from db import get_pool, init_db
from catalogo import (
    get_rank, CARGOS_RANK, calcular_mana_max,
    get_armas_classe, get_armaduras_classe,
    get_catalogo_completo, get_item_por_chave, get_itens_por_categoria
)
from utils import atualizar_cargo_nivel, atualizar_cargo_rank, atualizar_todos_cargos
from setup_cmd import cmd_setup
from dungeon import cmd_dungeon
from hospital import cmd_hospital, cmd_girar, cmd_set_giros, init_db_hospital, COR_RAR, EMOJI_FICHA
from batalha import (
    rodar_pvp, rodar_treino, MONSTROS, SKILLS_POR_CLASSE, BATALHAS_ATIVAS,
    get_skills_eq, get_skills_desbloq, GerenciarSkillsView,
    AceitarDueloView, EscolherArenaView, init_db_batalha,
    ARENAS, LOJA_ITENS, RECEITAS, POCOES
)
from missoes import cmd_missoes, cmd_ranking, init_db_missoes, atualizar_progresso
from conquistas import cmd_conquistas, init_conquistas, verificar_conquistas
from eventos import cmd_criar_evento, cmd_eventos, cmd_evento_info, cmd_encerrar_evento, cmd_add_pontos, init_db_eventos
from anuncios import cmd_anunciar, cmd_anunciar_evento, cmd_agendar_anuncio, CORES
from loja_sazonal import (cmd_loja_sazonal, cmd_loja_sazonal_remover, LojaItemModal, LojaRotativaModal, init_db_loja_sazonal)
from guildas import (cmd_guilda_criar, cmd_guilda_info, cmd_guilda_convidar, cmd_guilda_sair,
    cmd_guilda_expulsar, cmd_guilda_promover, cmd_guilda_depositar, cmd_guilda_retirar,
    cmd_guilda_ranking, cmd_guilda_missoes, init_db_guildas, dar_xp_guilda, atualizar_missao_guilda)
from dupla import rodar_treino_dupla
from expedicao import (
    cmd_expedicao_criar, 
    cmd_expedicao_status, 
    cmd_expedicao_encerrar, 
    cmd_expedicao_iniciar, 
    init_db_expedicao
)
from torneio import (cmd_torneio_criar, cmd_torneio_status, cmd_torneio_lutar,
    cmd_torneio_fechar_inscricoes, cmd_torneio_cancelar, init_db_torneio)
from dungeon_evento import (DungeonEventoCriarModal, AdicionarAndarModal,
    cmd_dungeon_evento_ativar, cmd_dungeon_evento_info,
    cmd_dungeon_evento_fechar, init_db_dungeon_evento)
from mercado import cmd_mercador, cmd_mercado_vender
from racas import RACAS, RACAS_BASICAS, get_raca, PassivaRacial, COR_RAR_RACA
# from imagens import (
#     IMG_, IMG_SETUP, IMG_INVENTARIO, IMG_SKILLS, IMG_AJUDA,
#     IMG_LOJA, IMG_FERREIRO, IMG_HOSPITAL, IMG_MERCADO, IMG_MERCADOR,
#     IMG_MISSOES, IMG_RANKING, IMG_CONQUISTAS, IMG_ROLETA,
#     IMG_BANNER_GERAL, IMG_VITORIA, IMG_DERROTA, IMG_LEVEL_UP, IMG_CLASSE
# )

# ─── DADOS ───────────────────────────────────────────────────────
def calcular_stats(poder_valor, destino_id, nivel=1):
    hp = 80 + poder_valor*2 + nivel*5
    atk = 8 + poder_valor//5 + nivel*2
    dfs = 5 + poder_valor//6 + nivel*1
    if destino_id == "prodigio":    atk = int(atk*1.12); dfs = int(dfs*0.95)
    elif destino_id == "guardiao":  dfs = int(dfs*1.12); atk = int(atk*0.95)
    elif destino_id == "abencado":  hp=int(hp*1.08); atk=int(atk*1.05); dfs=int(dfs*1.05)
    elif destino_id == "maldito":   atk=int(atk*0.85); dfs=int(dfs*0.85)
    elif destino_id == "amaldicoado": atk=random.randint(5,atk+5); dfs=random.randint(3,dfs+3)
    return hp, atk, dfs

CLASSES = [
    {"id":"guerreiro","nome":"Guerreiro","emoji":"🗡️","raridade":"Comum","peso":30,"desc":"Combate corpo a corpo. Alta defesa."},
    {"id":"arqueiro","nome":"Arqueiro","emoji":"🏹","raridade":"Comum","peso":25,"desc":"Precisao e criticos frequentes."},
    {"id":"mago","nome":"Mago","emoji":"🔮","raridade":"Comum","peso":20,"desc":"Dano magico crescente por turno."},
    {"id":"paladino","nome":"Paladino","emoji":"⚡","raridade":"Incomum","peso":12,"desc":"Hibrido: cura e combate."},
    {"id":"necromante","nome":"Necromante","emoji":"🌑","raridade":"Raro","peso":8,"desc":"Drena vida dos inimigos."},
    {"id":"dracomante","nome":"Dracomante","emoji":"🐉","raridade":"Lendario","peso":2,"desc":"Sangue de dragao. Resistencia maxima."},
    {"id":"arcano","nome":"Arcano","emoji":"✨","raridade":"Epico","peso":3,"desc":"Dano arcano que ignora defesa."},
]
PODERES = [
    {"id":"fraquinho","nome":"Fraquinho","emoji":"💀","valor":10},
    {"id":"mediano","nome":"Mediano","emoji":"⚖️","valor":18},
    {"id":"acima","nome":"Acima da media","emoji":"📈","valor":26},
    {"id":"forte","nome":"Forte","emoji":"💪","valor":35},
    {"id":"epico","nome":"Epico","emoji":"⚡","valor":48},
    {"id":"absurdo","nome":"Absurdo","emoji":"🔥","valor":65},
]
PESOS_PODER = [20,30,25,15,7,3]
DESTINOS = [
    {"id":"equilibrado","nome":"Equilibrado","emoji":"⚖️"},
    {"id":"prodigio","nome":"Prodigio","emoji":"🔥"},
    {"id":"maldito","nome":"Maldito","emoji":"💀"},
    {"id":"guardiao","nome":"Guardiao","emoji":"🛡️"},
    {"id":"abencado","nome":"Abencado","emoji":"🌟"},
    {"id":"amaldicoado","nome":"Amaldicado","emoji":"☠️"},
    {"id":"filho_caos","nome":"Filho do Caos","emoji":"🌀"},
]
EMOJI_CLASSE = {"guerreiro":"🗡️","mago":"🔮","arqueiro":"🏹","paladino":"⚡","necromante":"🌑","dracomante":"🐉","arcano":"✨"}
COR_RAR_BOT = {"Comum":0x888780,"Incomum":0x1D9E75,"Raro":0x378ADD,"Epico":0x7F77DD,"Lendario":0xD85A30}

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ─── HELPERS ─────────────────────────────────────────────────────

async def get_treino_uso(user_id):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow('SELECT * FROM treino_uso WHERE user_id=$1', user_id)
            if not row: return 0, None
            from datetime import datetime
            if row['reset_em'] and datetime.utcnow() >= row['reset_em']:
                await conn.execute('UPDATE treino_uso SET count=0, reset_em=NULL WHERE user_id=$1', user_id)
                return 0, None
            return row['count'], row['reset_em']
    except Exception as e:
        print(f'Erro get_treino_uso: {e}')
        return 0, None

async def incrementar_treino(user_id):
    try:
        from datetime import datetime, timedelta
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow('SELECT count FROM treino_uso WHERE user_id=$1', user_id)
            novo = (row['count'] if row else 0) + 1
            reset_em = datetime.utcnow() + timedelta(hours=2) if novo >= 20 else None
            await conn.execute(
                'INSERT INTO treino_uso(user_id,count,reset_em) VALUES($1,$2,$3) ON CONFLICT(user_id) DO UPDATE SET count=$2, reset_em=COALESCE($3, treino_uso.reset_em)',
                user_id, novo, reset_em)
    except Exception as e:
        print(f'Erro incrementar_treino: {e}')

def sortear_peso(lista, pesos):
    return random.choices(lista, weights=pesos, k=1)[0]

async def get_personagem(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", user_id)

def em_batalha(uid): return uid in BATALHAS_ATIVAS

async def checar_batalha(inter):
    if em_batalha(inter.user.id):
        try: await inter.response.send_message("Voce esta em batalha! Termine primeiro.", ephemeral=True)
        except: pass
        return False
    return True

async def atualizar_cargo_rank(guild, member, rank):
    for nome_c, rank_c in CARGOS_RANK.items():
        cargo = discord.utils.get(guild.roles, name=nome_c)
        if cargo:
            try:
                if nome_c == rank_c:
                    await member.add_roles(cargo)
                else:
                    if cargo in member.roles:
                        await member.remove_roles(cargo)
            except: pass

async def criar_canal_privado(guild, member, nome, classe):
    try:
        cat = (discord.utils.get(guild.categories, name="MEU ") or
               discord.utils.get(guild.categories, name="Meu ") or
               discord.utils.get(guild.categories, name="") or
               discord.utils.get(guild.categories, name=""))
        if not cat:
            cat = await guild.create_category("MEU ")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        nome_canal = f"{classe['emoji']}│{nome.lower()[:20]}"
        canal = await guild.create_text_channel(nome_canal, category=cat, overwrites=overwrites)
        cor = COR_RAR_BOT.get(classe.get("raridade","Comum"), 0x7F77DD)
        await canal.send(content=member.mention)

        secoes = [
            ("Bem-vindo a Villa Eldoria!", cor,
             "Este e o seu canal privado - so voce e o bot tem acesso aqui.\n\n"
             "Aqui estao todas as informacoes para sua jornada.\n"
             "**Leia tudo antes de comecar!**\n\n"
             "Use `/tutorial` a qualquer momento para rever qualquer secao.", "1/11"),

            ("Seu Personagem", 0x7F77DD,
             "**Comandos essenciais:**\n"
             "`/` - Ver sua ficha completa\n"
             "`/inventario` - Ver seus itens\n"
             "`/skills` - Ver suas habilidades\n"
             "`/setup` - Equipar armas e armaduras\n\n"
             "Ganhe XP para subir de nivel e evoluir seu personagem.\n"
             "Cada nivel aumenta HP, Mana, ATK e DEF automaticamente.", "2/11"),

            ("Roletas do Destino", 0x9B59B6,
             "`/girar` - Girar a roleta usando fichas\n\n"
             "As roletas podem conceder:\n"
             "- Novas classes raras (Dracomante, Arcano...)\n"
             "- Racas especiais\n"
             "- Itens e recompensas exclusivas\n\n"
             "Fichas sao obtidas em eventos, missoes e conquistas.", "3/11"),

            ("Sistema de Combate", 0xE24B4A,
             "`/treinar [dificuldade]` - Batalhar contra monstros\n"
             "`/desafiar @jogador` - Duelo PvP\n"
             "`/treinar-dupla @parceiro` - Batalha em dupla (+20% recompensa)\n\n"
             "Durante a batalha voce pode usar skills, se defender,\n"
             "usar pocoes da mochila ou fugir.\n\n"
             "**Dificuldades:** Facil > Medio > Dificil > Lendario", "4/11"),

            ("Dungeons", 0x7F77DD,
             "`/dungeon` - Entrar em uma dungeon\n\n"
             "Cada dungeon tem andares com monstros diferentes.\n"
             "Derrote todos para avancar e ganhar loot.\n"
             "Se morrer perde todas as recompensas do run.\n\n"
             "Masmorras vao do Rank F ao Rank SS.\n"
             "Cada rank e mais desafiador e recompensador.", "5/11"),

            ("Inventario e Loja", 0x1D9E75,
             "`/inventario` - Ver seus itens\n"
             "`/loja` - Comprar armas, armaduras e pocoes\n"
             "`/loja-sazonal` - Itens especiais e ofertas do dia\n"
             "`/ferreiro` - Forjar equipamentos raros\n"
             "`/mercado` - Vender seus itens\n\n"
             "Dica: Equipe sempre a melhor arma e armadura para sua classe!\n"
             "Use `/setup` para equipar ou clique em Equipar no `/inventario`.", "6/11"),

            ("Hospital e Recuperacao", 0x3498DB,
             "`/hospital` - Acessar o hospital\n\n"
             "Opcoes de cura:\n"
             "- Comprar cura com moedas\n"
             "- Descanso gratis de 30 minutos (recupera tudo)\n"
             "- Pocoes de cura do inventario durante batalhas\n\n"
             "Dica: Use o descanso gratis sempre que possivel!", "7/11"),

            ("Guildas", 0xE4AF3C,
             "`/guilda-info` - Ver informacoes da sua guilda\n"
             "`/guilda-missoes` - Ver missoes semanais\n"
             "`/guilda-depositar` - Depositar no banco da guilda\n\n"
             "Beneficios de ter guilda:\n"
             "- Bonus de XP e moedas conforme o nivel da guilda\n"
             "- Missoes semanais com recompensas para todos\n"
             "- Batalhas em dupla com membros\n\n"
             "Para criar uma guilda: `/guilda-criar` (custa 5000 moedas)", "8/11"),

            ("Rankings e Conquistas", 0xE4AF3C,
             "`/ranking` - Ver ranking do servidor\n"
             "`/conquistas` - Ver suas conquistas\n"
             "`/missoes` - Ver missoes diarias\n"
             "`/historico` - Ver historico de batalhas\n\n"
             "Rankings: Maior nivel, mais vitorias, mais rico,\n"
             "dungeons concluidas e torneios vencidos.\n\n"
             "Complete conquistas para ganhar recompensas!", "9/11"),

            ("Eventos e Torneios", 0xD85A30,
             "`/eventos` - Ver eventos ativos\n"
             "`/evento-info` - Detalhes e ranking do evento\n\n"
             "Tipos de eventos:\n"
             "- Torneios PvP com chaves e premios\n"
             "- Dungeons de evento com monstros customizados\n"
             "- Eventos especiais com premios exclusivos\n\n"
             "Fique de olho nos canais de anuncio!", "10/11"),

            ("Dicas para Iniciantes", 0x1D9E75,
             "**Por onde comecar:**\n"
             "1. Use `/loja` e compre uma arma para sua classe\n"
             "2. Use `/treinar facil` para ganhar XP e moedas\n"
             "3. Complete as `/missoes` diarias\n"
             "4. Entre numa guilda para bonus de XP\n"
             "5. Explore `/dungeon` quando estiver mais forte\n\n"
             "**Como evoluir rapido:**\n"
             "- Faca missoes diarias todos os dias\n"
             "- Participe de todos os eventos\n"
             "- Use o descanso gratis do hospital\n"
             "- Jogue em dupla para +20% de recompensa\n\n"
             "Use `/tutorial` para rever qualquer secao!", "11/11"),
        ]

        for titulo, cor_s, desc, secao in secoes:
            e = discord.Embed(title=titulo, description=desc, color=cor_s)
            e.set_footer(text=f"Villa Eldoria RPG — Secao {secao}")
            await canal.send(embed=e)
            await asyncio.sleep(0.4)

    except Exception as e:
        print(f"Erro ao criar canal privado: {e}")

# ─── AUTOCOMPLETE FUNCTIONS ──────────────────────────────────────

async def autocomplete_item_categoria(interaction: discord.Interaction, current: str):
    try:
        categoria = str(interaction.namespace.categoria or "")
    except:
        categoria = ""
    itens = get_itens_por_categoria(categoria) if categoria else get_catalogo_completo()
    filtrado = [i for i in itens if current.lower() in i["nome"].lower() or current.lower() in i["raridade"].lower()]
    return [
        app_commands.Choice(
            name=f"{i['emoji']} {i['nome']} [{i['raridade']}]"[:100],
            value=i["chave"]
        )
        for i in filtrado[:25]
    ]

async def autocomplete_item_todos(interaction: discord.Interaction, current: str):
    itens = get_catalogo_completo()
    filtrado = [i for i in itens if current.lower() in i["nome"].lower() or current.lower() in i["raridade"].lower() or current.lower() in i["tipo"].lower()]
    return [
        app_commands.Choice(
            name=f"{i['emoji']} {i['nome']} [{i['raridade']}] — {i['tipo']}{' ('+i['classe']+')' if i['classe'] else ''}"[:100],
            value=i["chave"]
        )
        for i in filtrado[:25]
    ]

async def autocomplete_materiais(interaction: discord.Interaction, current: str):
    itens = get_catalogo_completo()
    filtrado = [i for i in itens if i["tipo"] in ("material","pocao") and (current.lower() in i["nome"].lower() or not current)]
    return [
        app_commands.Choice(
            name=f"{i['emoji']} {i['nome']} [{i['raridade']}]"[:100],
            value=i["chave"]
        )
        for i in filtrado[:25]
    ]

async def autocomplete_item_premio(interaction: discord.Interaction, current: str):
    try:
        premio_tipo = str(interaction.namespace.premio_tipo or "")
    except:
        premio_tipo = ""
    if premio_tipo == "item":
        itens = get_catalogo_completo()
        filtrado = [i for i in itens if current.lower() in i["nome"].lower() or not current]
        return [
            app_commands.Choice(
                name=f"{i['emoji']} {i['nome']} [{i['raridade']}]"[:100],
                value=f"{i['id']}|{i['nome']}|{i['tipo']}|{i['raridade']}|{i['emoji']}|{i.get('desc','')}"[:100]
            )
            for i in filtrado[:25]
        ]
    elif premio_tipo == "moedas":
        exemplos = ["1000","2000","5000","10000","20000","50000"]
        return [app_commands.Choice(name=f"{v} moedas", value=v) for v in exemplos if current in v]
    elif premio_tipo == "xp":
        exemplos = ["500","1000","2000","5000","10000"]
        return [app_commands.Choice(name=f"{v} XP", value=v) for v in exemplos if current in v]
    elif premio_tipo == "ficha":
        exemplos = ["1","2","3","5","10"]
        return [app_commands.Choice(name=f"{v} ficha(s)", value=v) for v in exemplos if current in v]
    elif premio_tipo == "cargo":
        return [app_commands.Choice(name="Nome do cargo (ex: Campiao)", value=current or "Campiao")]
    elif premio_tipo == "classe":
        classes = ["guerreiro","arqueiro","mago","paladino","necromante","dracomante","arcano"]
        EMOJI_CLS = {"guerreiro":"🗡️","arqueiro":"🏹","mago":"🔮","paladino":"⚡","necromante":"🌑","dracomante":"🐉","arcano":"✨"}
        return [app_commands.Choice(name=f"{EMOJI_CLS[cl]} {cl.title()}", value=cl) for cl in classes if current.lower() in cl]
    return [app_commands.Choice(name=current or "Digite o valor do premio", value=current or "")]

async def autocomplete_canal(interaction: discord.Interaction, current: str):
    if not interaction.guild: return []
    canais = [
        ch for ch in interaction.guild.channels
        if isinstance(ch, (discord.TextChannel, discord.ForumChannel))
        and (not current or current.lower() in ch.name.lower())
    ]
    canais.sort(key=lambda ch: ch.name)
    return [
        app_commands.Choice(name=f"#{ch.name}", value=str(ch.id))
        for ch in canais[:25]
    ]

def resolver_canal(guild, canal):
    if canal is None: return None
    if hasattr(canal, 'id'):
        return guild.get_channel(canal.id) or canal
    canal_str = str(canal)
    if canal_str.isdigit():
        return guild.get_channel(int(canal_str))
    return discord.utils.get(guild.channels, name=canal_str.lstrip('#'))

# ─── /criar_personagem ───────────────────────────────────────────

@bot.tree.command(name="criar_personagem", description="Escolha sua raca e classe para comecar!")
async def criar_personagem(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    uid = interaction.user.id
    if await get_personagem(uid):
        await interaction.followup.send("Voce ja tem personagem! Use /.", ephemeral=True)
        return

    embed_raca = discord.Embed(title="Passo 1 — Escolha sua Raca", color=0x7F77DD)
    for rid in RACAS_BASICAS:
        r = RACAS[rid]
        embed_raca.add_field(name=f"{r['emoji']} {r['nome']}", value=r['passiva_desc'], inline=False)

    class RacaView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=120)
            self.escolha = None
        @discord.ui.button(label="Humano", style=discord.ButtonStyle.primary)
        async def btn_h(self, inter, b):
            if inter.user.id != uid: return
            self.escolha = "humano"; await inter.response.defer(); self.stop()
        @discord.ui.button(label="Anao", style=discord.ButtonStyle.primary)
        async def btn_a(self, inter, b):
            if inter.user.id != uid: return
            self.escolha = "anao"; await inter.response.defer(); self.stop()
        @discord.ui.button(label="Elfo", style=discord.ButtonStyle.primary)
        async def btn_e(self, inter, b):
            if inter.user.id != uid: return
            self.escolha = "elfo"; await inter.response.defer(); self.stop()

    vr = RacaView()
    msg = await interaction.followup.send(embed=embed_raca, view=vr, ephemeral=True, wait=True)
    await vr.wait()
    if not vr.escolha:
        await msg.edit(content="Tempo esgotado!", embed=None, view=None); return
    raca = RACAS[vr.escolha]

    BASICAS = [c for c in CLASSES if c["raridade"] == "Comum"]
    embed_cls = discord.Embed(title="Passo 2 — Escolha sua Classe", color=0xE4AF3C)
    for c in BASICAS:
        embed_cls.add_field(name=f"{c['emoji']} {c['nome']}", value=c["desc"], inline=True)
    embed_cls.set_footer(text=f"Raca: {raca['emoji']} {raca['nome']}")

    class ClasseView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=120)
            self.escolha = None
        @discord.ui.button(label="Guerreiro", style=discord.ButtonStyle.success)
        async def btn_g(self, inter, b):
            if inter.user.id != uid: return
            self.escolha = next(c for c in CLASSES if c["id"]=="guerreiro")
            await inter.response.defer(); self.stop()
        @discord.ui.button(label="Arqueiro", style=discord.ButtonStyle.success)
        async def btn_a(self, inter, b):
            if inter.user.id != uid: return
            self.escolha = next(c for c in CLASSES if c["id"]=="arqueiro")
            await inter.response.defer(); self.stop()
        @discord.ui.button(label="Mago", style=discord.ButtonStyle.success)
        async def btn_m(self, inter, b):
            if inter.user.id != uid: return
            self.escolha = next(c for c in CLASSES if c["id"]=="mago")
            await inter.response.defer(); self.stop()

    vc = ClasseView()
    await msg.edit(embed=embed_cls, view=vc)
    await vc.wait()
    if not vc.escolha:
        await msg.edit(content="Tempo esgotado!", embed=None, view=None); return
    classe = vc.escolha

    await msg.edit(embed=discord.Embed(
        title="As roletas giram...",
        description=f"{raca['emoji']} {raca['nome']} + {classe['emoji']} {classe['nome']}\n\nSortindo poder, destino e skills...",
        color=0x7F77DD), view=None)
    await asyncio.sleep(1.5)

    poder = sortear_peso(PODERES, PESOS_PODER)
    destino = random.choice(DESTINOS)
    mana_max = calcular_mana_max(classe["id"], 1, poder["valor"], destino["id"])
    if raca["id"] == "elfo": mana_max += 20

    from catalogo import SKILLS_COMPLETAS
    skills_cls = SKILLS_COMPLETAS.get(classe["id"], [])
    disp = [s for s in skills_cls if s["nivel"] <= 5]
    if len(disp) < 2: disp = skills_cls[:2]
    random.shuffle(disp)
    skills_s = disp[:2]

    hp, atk, dfs = calcular_stats(poder["valor"], destino["id"], 1)
    if raca["id"] == "anao": dfs += 8
    nome = interaction.user.display_name

    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        await conn.execute("""
            INSERT INTO personagens
            (user_id,nome,classe_id,raridade,poder_id,poder_valor,destino_id,skill_id,
             nivel,xp,hp_max,hp_atual,ataque,defesa,mana_max,mana_atual,moedas,raca_id)
            VALUES($1,$2,$3,$4,$5,$6,$7,$8,1,0,$9,$10,$11,$12,$13,$13,50,$14)
        """, uid, nome, classe["id"], classe["raridade"], poder["id"], poder["valor"],
            destino["id"], skills_s[0]["id"] if skills_s else "",
            hp, hp, atk, dfs, mana_max, raca["id"])
        for i, sk in enumerate(skills_s):
            await conn.execute("INSERT INTO skills_desbloqueadas(user_id,skill_id) VALUES($1,$2) ON CONFLICT DO NOTHING", uid, sk["id"])
            await conn.execute("INSERT INTO skills_equipadas(user_id,skill_id,slot) VALUES($1,$2,$3) ON CONFLICT(user_id,slot) DO UPDATE SET skill_id=EXCLUDED.skill_id", uid, sk["id"], i)

    efinal = discord.Embed(title=f"Bem-vindo, {nome}!", color=COR_RAR_BOT.get(classe["raridade"],0x888780))
    efinal.add_field(name="Raca",   value=f"{raca['emoji']} {raca['nome']}", inline=True)
    efinal.add_field(name="Classe", value=f"{classe['emoji']} {classe['nome']}", inline=True)
    efinal.add_field(name="Poder",  value=f"{poder['emoji']} {poder['nome']}", inline=True)
    efinal.add_field(name="Destino",value=f"{destino['emoji']} {destino['nome']}", inline=True)
    efinal.add_field(name="HP",     value=str(hp), inline=True)
    efinal.add_field(name="ATK",    value=str(atk), inline=True)
    efinal.add_field(name="Mana",   value=str(mana_max), inline=True)
    efinal.set_footer(text="Use /loja para comprar sua primeira arma! | /perfil para ver sua ficha")
    await msg.edit(embed=efinal, view=None)

    guild = interaction.guild
    if guild:
        member = guild.get_member(uid)
        if member:
            cargo_raca = discord.utils.get(guild.roles, name=raca.get("cargos",""))
            if cargo_raca:
                try: await member.add_roles(cargo_raca)
                except: pass
            cargo_base = discord.utils.get(guild.roles, name="🏠 Morador da Vila")
            if not cargo_base:
                cargo_base = discord.utils.get(guild.roles, name="Morador da Vila")
            if cargo_base:
                try: await member.add_roles(cargo_base)
                except: pass
            recem = discord.utils.get(guild.roles, name="🌱 Recem-chegado")
            if recem and recem in member.roles:
                try: await member.remove_roles(recem)
                except: pass
            await atualizar_todos_cargos(guild, member, 1)
        await criar_canal_privado(guild, member, nome, classe)

# ─── /perfil ─────────────────────────────────────────────────────

@bot.tree.command(name="perfil", description="Mostra a ficha do seu personagem")
@app_commands.describe(jogador="Jogador (opcional)")
async def perfil(interaction: discord.Interaction, jogador: discord.Member = None):
    await interaction.response.defer()
    alvo = jogador or interaction.user
    p = await get_personagem(alvo.id)
    if not p:
        await interaction.followup.send("Personagem nao encontrado!", ephemeral=True)
        return
    cls = next((c for c in CLASSES if c["id"] == p["classe_id"]), None)
    raca_p = get_raca(p["raca_id"] if p["raca_id"] else "humano")
    rank_i = get_rank(p["nivel"])
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        arma = await conn.fetchrow("SELECT * FROM inventario WHERE user_id=$1 AND tipo='arma' AND equipado=1", alvo.id)
        arm = await conn.fetchrow("SELECT * FROM inventario WHERE user_id=$1 AND tipo='armadura' AND equipado=1", alvo.id)
        ids_eq = await conn.fetch("SELECT skill_id FROM skills_equipadas WHERE user_id=$1 ORDER BY slot", alvo.id)
    from catalogo import SKILLS_COMPLETAS
    sk_nomes = []
    for r in ids_eq:
        for sk in SKILLS_COMPLETAS.get(p["classe_id"], []):
            if sk["id"] == r["skill_id"]:
                sk_nomes.append(f"{sk['emoji']} {sk['nome']}")
                break
    xp_need = 100 + (p["nivel"] - 1) * 50
    embed = discord.Embed(
        title=f"{cls['emoji'] if cls else '?'} {p['nome']}",
        description=(
            f"**Raca:** {raca_p['emoji']} {raca_p['nome']}\n"
            f"**Classe:** {cls['nome'] if cls else p['classe_id']} — *{p['raridade']}*\n"
            f"**Rank:** {rank_i['emoji']} {rank_i['rank']} — {rank_i['nome']}\n"
            f"**Nivel:** {p['nivel']} | XP: {p['xp']}/{xp_need}"
        ),
        color=COR_RAR_BOT.get(p["raridade"], 0x888780)
    )
    embed.add_field(name="Stats", value=f"❤️ {p['hp_atual']}/{p['hp_max']} | ⚔️ {p['ataque']} | 🛡️ {p['defesa']} | 💙 {p['mana_atual']}/{p['mana_max']}", inline=False)
    embed.add_field(name="Equipamento", value=f"⚔️ {arma['nome'] if arma else 'Sem arma'} | 🛡️ {arm['nome'] if arm else 'Sem armadura'}", inline=False)
    if sk_nomes:
        embed.add_field(name="Skills", value=" | ".join(sk_nomes), inline=False)
    embed.add_field(name=f"{raca_p['emoji']} Passiva Racial", value=raca_p['passiva_desc'], inline=False)
    embed.add_field(name="Moedas", value=f"{p['moedas']} 🪙", inline=True)
    embed.add_field(name="Vitorias", value=str(p.get('vitorias', 0)), inline=True)
    embed.set_thumbnail(url=alvo.display_avatar.url)
    await interaction.followup.send(embed=embed)

# ─── /inventario ─────────────────────────────────────────────────

@bot.tree.command(name="inventario", description="Mostra seu inventario completo")
@app_commands.describe(jogador="Jogador (opcional)")
async def inventario(interaction: discord.Interaction, jogador: discord.Member = None):
    await interaction.response.defer(ephemeral=True)
    alvo = jogador or interaction.user
    p = await get_personagem(alvo.id)
    if not p:
        await interaction.followup.send("Personagem nao encontrado!", ephemeral=True); return
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        itens = await conn.fetch("SELECT * FROM inventario WHERE user_id=$1 ORDER BY tipo,raridade", alvo.id)
    armas = [i for i in itens if i["tipo"]=="arma"]
    armdrs = [i for i in itens if i["tipo"]=="armadura"]
    pocoes = [i for i in itens if i["tipo"]=="pocao" or i["item_id"]=="elixir"]
    mats = [i for i in itens if i["tipo"]=="material"]
    embed = discord.Embed(title=f"Inventario de {alvo.display_name}", color=0x7F77DD)
    def fmt(lista):
        if not lista: return "—"
        return "\n".join([f"{i['emoji']} **{i['nome']}** [{i['raridade']}] (x{i.get('quantidade',1)}){' ✅' if i.get('equipado') else ''}" for i in lista])
    embed.add_field(name="Mochila", value=fmt(pocoes) if pocoes else "—", inline=False)
    embed.add_field(name="Armas",   value=fmt(armas)  if armas  else "—", inline=True)
    embed.add_field(name="Armaduras",value=fmt(armdrs) if armdrs else "—",inline=True)
    if mats: embed.add_field(name="Materiais", value=fmt(mats), inline=False)
    embed.set_footer(text=f"Moedas: {p['moedas']} 🪙")
    if IMG_INVENTARIO: embed.set_image(url=IMG_INVENTARIO)

    equipaveis = armas + armdrs
    if equipaveis and alvo.id == interaction.user.id:
        opcoes = [discord.SelectOption(
            label=f"{i['emoji']} {i['nome'][:40]}",
            value=str(i["id"]),
            description=f"{i['tipo'].title()} | {i['raridade']}",
            default=bool(i.get("equipado"))
        ) for i in equipaveis[:25]]

        class EquiparView(discord.ui.View):
            def __init__(self): super().__init__(timeout=60)
            @discord.ui.select(placeholder="Equipar item...", options=opcoes)
            async def sel(self, inter: discord.Interaction, s):
                if inter.user.id != interaction.user.id: return
                item_id = int(s.values[0])
                item_row = next((i for i in equipaveis if i["id"]==item_id), None)
                if not item_row: await inter.response.send_message("Item nao encontrado!", ephemeral=True); return
                pool2 = await get_pool()
                async with pool2.acquire() as conn2:
                    await conn2.execute("UPDATE inventario SET equipado=0 WHERE user_id=$1 AND tipo=$2", inter.user.id, item_row["tipo"])
                    await conn2.execute("UPDATE inventario SET equipado=1 WHERE id=$1", item_id)
                await inter.response.send_message(f"Equipado: {item_row['emoji']} **{item_row['nome']}**!", ephemeral=True)

        await interaction.followup.send(embed=embed, view=EquiparView(), ephemeral=True)
    else:
        await interaction.followup.send(embed=embed, ephemeral=True)

# ─── /setup ──────────────────────────────────────────────────────

@bot.tree.command(name="setup", description="Monte seu setup completo")
async def setup(interaction: discord.Interaction):
    await cmd_setup(interaction)

# ─── /skills ─────────────────────────────────────────────────────

@bot.tree.command(name="skills", description="Veja e gerencie suas skills equipadas")
async def skills(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True); return
    from catalogo import SKILLS_COMPLETAS
    todas = SKILLS_COMPLETAS.get(p["classe_id"], [])
    ids_desbloq = await get_skills_desbloq(interaction.user.id)
    ids_eq = await get_skills_eq(interaction.user.id)
    disp = [s for s in todas if s["id"] in ids_desbloq]
    if not disp:
        await interaction.followup.send("Nenhuma skill desbloqueada ainda!", ephemeral=True); return
    view = GerenciarSkillsView(interaction.user.id, disp, ids_eq)
    embed = discord.Embed(title="Gerenciar Skills", description="Selecione ate 4 skills para equipar:", color=0x7F77DD)
    for s in disp:
        mana_txt = f" | {s['mana']} mana" if s.get('mana') else ''
        embed.add_field(name=f"{s['emoji']} {s['nome']} (Nv{s['nivel']})", value=f"{s['desc']}{mana_txt}", inline=True)
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)

# ─── /equipar ────────────────────────────────────────────────────

@bot.tree.command(name="equipar", description="Equipa um item do inventario pelo nome")
@app_commands.describe(item="Nome do item a equipar")
async def equipar(interaction: discord.Interaction, item: str):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True); return
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM inventario WHERE user_id=$1 AND LOWER(nome) LIKE $2 AND tipo IN ('arma','armadura') LIMIT 1",
            interaction.user.id, f"%{item.lower()}%")
        if not row:
            await interaction.followup.send(f"Item '{item}' nao encontrado!", ephemeral=True); return
        await conn.execute("UPDATE inventario SET equipado=0 WHERE user_id=$1 AND tipo=$2", interaction.user.id, row["tipo"])
        await conn.execute("UPDATE inventario SET equipado=1 WHERE id=$1", row["id"])
    await interaction.followup.send(f"Equipado: {row['emoji']} **{row['nome']}**!", ephemeral=True)

# ─── /jogar-fora ─────────────────────────────────────────────────

@bot.tree.command(name="jogar-fora", description="Descarta um item do inventario")
@app_commands.describe(item="Nome do item a descartar")
async def jogar_fora(interaction: discord.Interaction, item: str):
    await interaction.response.defer(ephemeral=True)
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM inventario WHERE user_id=$1 AND LOWER(nome) LIKE $2 LIMIT 1",
            interaction.user.id, f"%{item.lower()}%")
        if not row:
            await interaction.followup.send(f"Item '{item}' nao encontrado!", ephemeral=True); return
        await conn.execute("DELETE FROM inventario WHERE id=$1", row["id"])
    await interaction.followup.send(f"Descartado: {row['emoji']} {row['nome']}", ephemeral=True)

# ─── /dar ────────────────────────────────────────────────────────

@bot.tree.command(name="dar", description="Da um item para outro jogador")
@app_commands.describe(jogador="Jogador que recebe", item="Nome do item")
async def dar(interaction: discord.Interaction, jogador: discord.Member, item: str):
    await interaction.response.defer(ephemeral=True)
    if jogador.id == interaction.user.id:
        await interaction.followup.send("Voce nao pode dar item para si mesmo!", ephemeral=True); return
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM inventario WHERE user_id=$1 AND LOWER(nome) LIKE $2 LIMIT 1",
            interaction.user.id, f"%{item.lower()}%")
        if not row:
            await interaction.followup.send(f"Item '{item}' nao encontrado!", ephemeral=True); return
        ex = await conn.fetchrow("SELECT id,quantidade FROM inventario WHERE user_id=$1 AND item_id=$2", jogador.id, row["item_id"])
        if ex: await conn.execute("UPDATE inventario SET quantidade=quantidade+1 WHERE id=$1", ex["id"])
        else: await conn.execute("INSERT INTO inventario(user_id,item_id,nome,tipo,raridade,emoji,descricao) VALUES($1,$2,$3,$4,$5,$6,$7)",
            jogador.id, row["item_id"], row["nome"], row["tipo"], row["raridade"], row["emoji"], row["descricao"])
        if row["quantidade"] > 1: await conn.execute("UPDATE inventario SET quantidade=quantidade-1 WHERE id=$1", row["id"])
        else: await conn.execute("DELETE FROM inventario WHERE id=$1", row["id"])
    await interaction.followup.send(f"Dado {row['emoji']} **{row['nome']}** para {jogador.mention}!", ephemeral=True)

# ─── /treinar ────────────────────────────────────────────────────

@bot.tree.command(name="treinar", description="Batalha contra monstros para ganhar XP")
@app_commands.describe(dificuldade="Escolha a dificuldade")
@app_commands.choices(dificuldade=[
    app_commands.Choice(name="Facil",    value="facil"),
    app_commands.Choice(name="Medio",    value="medio"),
    app_commands.Choice(name="Dificil",  value="dificil"),
    app_commands.Choice(name="Lendario", value="lendario"),
])
async def treinar(interaction: discord.Interaction, dificuldade: str = "facil"):
    await interaction.response.defer()
    if em_batalha(interaction.user.id):
        await interaction.followup.send("Voce ja esta em batalha!", ephemeral=True); return
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Use /criar_personagem primeiro!", ephemeral=True); return
    count, reset_em = await get_treino_uso(interaction.user.id)
    if count >= 20 and reset_em:
        from datetime import datetime
        secs = int((reset_em - datetime.utcnow()).total_seconds())
        mins = secs // 60; segs = secs % 60
        await interaction.followup.send(
            f"Voce ja treinou 20 vezes! Descanse. Treina novamente em {mins}min {segs}s.", ephemeral=True); return
    monstros_d = [m for m in MONSTROS if m["dificuldade"] == dificuldade]
    if not monstros_d:
        await interaction.followup.send("Dificuldade invalida!", ephemeral=True); return
    monstro = random.choice(monstros_d)

    view_arena = EscolherArenaView(interaction.user.id)
    embed_arena = discord.Embed(
        title="Escolha a Arena!",
        description=f"Voce vai enfrentar **{monstro['emoji']} {monstro['nome']}**!\n\nEscolha onde a batalha vai acontecer:",
        color=0x7F77DD
    )
    embed_arena.set_footer(text="30s para selecionar automaticamente")
    msg_arena = await interaction.followup.send(embed=embed_arena, view=view_arena, wait=True)
    await view_arena.wait()
    arena = view_arena.arena or random.choice(ARENAS)
    embed_escolhida = discord.Embed(
        title=f"{arena['emoji']} {arena['nome']}",
        description=f"Bonus: {arena['bonus']}\n\nPreparando batalha...",
        color=arena["cor"]
    )
    if arena.get("img"): embed_escolhida.set_image(url=arena["img"])
    try: await msg_arena.edit(embed=embed_escolhida, view=None)
    except: pass
    await asyncio.sleep(1)
    try:
        await rodar_treino(interaction, p, monstro, arena)
    except Exception as e:
        import traceback
        print(f"ERRO rodar_treino: {e}")
        traceback.print_exc()
        BATALHAS_ATIVAS.discard(interaction.user.id)
        try:
            await interaction.followup.send("Ocorreu um erro na batalha. Tente novamente!", ephemeral=True)
        except: pass
    finally:
        await incrementar_treino(interaction.user.id)

# ─── /desafiar ───────────────────────────────────────────────────

@bot.tree.command(name="desafiar", description="Desafia outro jogador para um duelo PvP")
@app_commands.describe(jogador="Jogador a desafiar")
async def desafiar(interaction: discord.Interaction, jogador: discord.Member):
    await interaction.response.defer()
    if em_batalha(interaction.user.id):
        await interaction.followup.send("Voce ja esta em batalha!", ephemeral=True); return
    if jogador.bot or jogador.id == interaction.user.id:
        await interaction.followup.send("Jogador invalido!", ephemeral=True); return
    p1 = await get_personagem(interaction.user.id)
    p2 = await get_personagem(jogador.id)
    if not p1: await interaction.followup.send("Voce nao tem personagem!", ephemeral=True); return
    if not p2: await interaction.followup.send(f"{jogador.display_name} nao tem personagem!", ephemeral=True); return
    view = AceitarDueloView(interaction.user.id, jogador.id)
    embed = discord.Embed(title="Desafio de Duelo!", description=f"{interaction.user.mention} desafia {jogador.mention}!\nVoce aceita?", color=0xE4AF3C)
    msg_d = await interaction.followup.send(embed=embed, view=view, wait=True)
    await view.wait()
    if not view.resposta:
        await msg_d.edit(embed=discord.Embed(title="Desafio recusado!", color=0x888780), view=None); return
    arena = random.choice(ARENAS)
    await msg_d.edit(embed=discord.Embed(title=f"Duelo! {arena['emoji']} {arena['nome']}", color=0x1D9E75), view=None)
    await rodar_pvp(interaction.channel, p1, p2, interaction.user, jogador, arena)

# ─── /dungeon ────────────────────────────────────────────────────

@bot.tree.command(name="dungeon", description="Entre em uma dungeon! Se morrer perde tudo")
@app_commands.describe(rank="Rank da dungeon")
@app_commands.choices(rank=[
    app_commands.Choice(name="Rank F (Nv 1+)",   value="F"),
    app_commands.Choice(name="Rank E (Nv 10+)",  value="E"),
    app_commands.Choice(name="Rank D (Nv 20+)",  value="D"),
    app_commands.Choice(name="Rank C (Nv 30+)",  value="C"),
    app_commands.Choice(name="Rank B (Nv 40+)",  value="B"),
    app_commands.Choice(name="Rank A (Nv 50+)",  value="A"),
    app_commands.Choice(name="Rank S (Nv 60+)",  value="S"),
    app_commands.Choice(name="Rank SS (Nv 75+)", value="SS"),
])
async def dungeon(interaction: discord.Interaction, rank: str = "F"):
    if interaction.user.id in BATALHAS_ATIVAS:
        await interaction.response.send_message("Voce ja esta em batalha!", ephemeral=True); return
    await cmd_dungeon(interaction, rank)

# ─── /hospital ───────────────────────────────────────────────────

@bot.tree.command(name="hospital", description="Restaure seu HP e Mana no hospital")
async def hospital(interaction: discord.Interaction):
    await cmd_hospital(interaction)

# ─── /girar ──────────────────────────────────────────────────────

@bot.tree.command(name="girar", description="Use fichas de roleta para ganhar itens raros")
async def girar(interaction: discord.Interaction):
    await cmd_girar(interaction)

# ─── /loja ───────────────────────────────────────────────────────

@bot.tree.command(name="loja", description="Compre armas, armaduras e pocoes")
@app_commands.describe(categoria="Categoria de item")
@app_commands.choices(categoria=[
    app_commands.Choice(name="Armas",     value="armas"),
    app_commands.Choice(name="Armaduras", value="armaduras"),
    app_commands.Choice(name="Pocoes",    value="pocoes"),
])
async def loja(interaction: discord.Interaction, categoria: str = "pocoes"):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True); return
    if categoria == "armas":
        itens = [i for i in get_armas_classe(p["classe_id"]) if i["raridade"] in ("Comum","Incomum")]
    elif categoria == "armaduras":
        itens = [i for i in get_armaduras_classe(p["classe_id"]) if i["raridade"] in ("Comum","Incomum")]
    else:
        itens = [{"id":k,"nome":v["nome"],"emoji":v["emoji"],"raridade":"Comum","preco":v["preco"],"desc":f"Recupera {v['valor']} HP/Mana"} for k,v in POCOES.items()]
    if not itens:
        await interaction.followup.send("Nenhum item disponivel!", ephemeral=True); return
    opcoes = [discord.SelectOption(label=f"{i['emoji']} {i['nome']} — {i.get('preco',0)} moedas", value=i["id"], description=i.get("desc","")[:50]) for i in itens[:25]]
    class LojaView(discord.ui.View):
        def __init__(self): super().__init__(timeout=60); self.item = None
        @discord.ui.select(placeholder="Escolha o item...", options=opcoes)
        async def sel(self, inter, s):
            if inter.user.id != interaction.user.id: return
            self.item = next((i for i in itens if i["id"]==s.values[0]), None)
            await inter.response.defer(); self.stop()
    v = LojaView()
    embed_loja = discord.Embed(title=f"Loja — {categoria.title()}", description=f"Moedas: **{p['moedas']}**", color=0xE4AF3C)
    await interaction.followup.send(embed=embed_loja, view=v, ephemeral=True)
    await v.wait()
    if not v.item: return
    it = v.item; preco = it.get("preco",0)
    if p["moedas"] < preco:
        await interaction.followup.send(f"Moedas insuficientes! Precisa de {preco}.", ephemeral=True); return
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        await conn.execute("UPDATE personagens SET moedas=moedas-$1 WHERE user_id=$2", preco, interaction.user.id)
        ex = await conn.fetchrow("SELECT id FROM inventario WHERE user_id=$1 AND item_id=$2", interaction.user.id, it["id"])
        if ex: await conn.execute("UPDATE inventario SET quantidade=quantidade+1 WHERE id=$1", ex["id"])
        else: await conn.execute("INSERT INTO inventario(user_id,item_id,nome,tipo,raridade,emoji,descricao) VALUES($1,$2,$3,$4,$5,$6,$7)",
            interaction.user.id, it["id"], it["nome"], categoria.rstrip("s"), it["raridade"], it["emoji"], it.get("desc",""))
    await interaction.followup.send(f"Comprou {it['emoji']} **{it['nome']}** por {preco} moedas!", ephemeral=True)

# ─── /ferreiro ───────────────────────────────────────────────────

@bot.tree.command(name="ferreiro", description="Forje itens com materiais de dungeon")
async def ferreiro(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True); return
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        inv = await conn.fetch("SELECT item_id,quantidade FROM inventario WHERE user_id=$1", interaction.user.id)
        pf = await conn.fetchrow("SELECT moedas FROM personagens WHERE user_id=$1", interaction.user.id)
    inv_map = {r["item_id"]:r["quantidade"] for r in inv}
    disp = [r for r in RECEITAS if all(inv_map.get(m,0)>=q for m,q in r["materiais"].items())]
    linhas = []
    for r in RECEITAS:
        pode = r in disp
        status = "✅" if pode else "❌"
        falta_txt = ""
        if not pode:
            faltando = [f"{q-inv_map.get(m,0)}x {m}" for m,q in r["materiais"].items() if inv_map.get(m,0) < q]
            if faltando: falta_txt = f" (falta: {', '.join(faltando)})"
        linhas.append(f"{status} {r['emoji']} **{r['nome']}** [{r['raridade']}] — {r['preco_forja']} moedas{falta_txt}")
    desc = "\n".join(linhas)
    if not disp:
        await interaction.followup.send(embed=discord.Embed(title="Ferreiro", description=f"Sem materiais suficientes!\n\n{desc}", color=0x888780), ephemeral=True); return
    opcoes = [discord.SelectOption(label=f"{r['emoji']} {r['nome']}", value=r["id"]) for r in disp[:25]]
    class FerreiroView(discord.ui.View):
        def __init__(self): super().__init__(timeout=60); self.escolha = None
        @discord.ui.select(placeholder="Escolha a receita...", options=opcoes)
        async def sel(self, inter, s):
            if inter.user.id != interaction.user.id: return
            self.escolha = s.values[0]; await inter.response.defer(); self.stop()
    v = FerreiroView()
    await interaction.followup.send(embed=discord.Embed(title="Ferreiro", description=desc, color=0x888780), view=v, ephemeral=True)
    await v.wait()
    if not v.escolha: return
    receita = next((r for r in RECEITAS if r["id"]==v.escolha), None)
    if not receita: return
    if pf["moedas"] < receita["preco_forja"]:
        await interaction.followup.send("Moedas insuficientes!", ephemeral=True); return
    async with pool_db.acquire() as conn:
        await conn.execute("UPDATE personagens SET moedas=moedas-$1 WHERE user_id=$2", receita["preco_forja"], interaction.user.id)
        for mat, qtd in receita["materiais"].items():
            row = await conn.fetchrow("SELECT id,quantidade FROM inventario WHERE user_id=$1 AND item_id=$2", interaction.user.id, mat)
            if row:
                if row["quantidade"] > qtd: await conn.execute("UPDATE inventario SET quantidade=quantidade-$1 WHERE id=$2", qtd, row["id"])
                else: await conn.execute("DELETE FROM inventario WHERE id=$1", row["id"])
        ex = await conn.fetchrow("SELECT id FROM inventario WHERE user_id=$1 AND item_id=$2", interaction.user.id, receita["id"])
        if ex: await conn.execute("UPDATE inventario SET quantidade=quantidade+1 WHERE id=$1", ex["id"])
        else: await conn.execute("INSERT INTO inventario(user_id,item_id,nome,tipo,raridade,emoji,descricao) VALUES($1,$2,$3,$4,$5,$6,$7)",
            interaction.user.id, receita["id"], receita["nome"], receita["tipo"], receita["raridade"], receita["emoji"], receita["desc"])
    await interaction.followup.send(f"Forjado: {receita['emoji']} **{receita['nome']}**!", ephemeral=True)

# ─── /mercado ────────────────────────────────────────────────────

@bot.tree.command(name="mercado", description="Venda itens do inventario por moedas")
async def mercado(interaction: discord.Interaction):
    await cmd_mercado_vender(interaction)

# ─── /mercador ───────────────────────────────────────────────────

@bot.tree.command(name="mercador", description="Troque materiais por itens exclusivos")
async def mercador(interaction: discord.Interaction):
    await cmd_mercador(interaction)

# ─── /missoes ────────────────────────────────────────────────────

@bot.tree.command(name="missoes", description="Veja e complete suas missoes diarias")
async def missoes(interaction: discord.Interaction):
    await cmd_missoes(interaction)

# ─── /ranking ────────────────────────────────────────────────────

@bot.tree.command(name="ranking", description="Top 10 jogadores do servidor")
async def ranking(interaction: discord.Interaction):
    await cmd_ranking(interaction)

# ─── /conquistas ─────────────────────────────────────────────────

@bot.tree.command(name="conquistas", description="Veja suas conquistas e progresso")
async def conquistas(interaction: discord.Interaction):
    await cmd_conquistas(interaction)

# ─── /set-item ───────────────────────────────────────────────────

@bot.tree.command(name="set-item", description="[ADMIN] Da item a um jogador")
@app_commands.describe(
    jogador="Jogador que vai receber o item",
    categoria="Categoria do item",
    item="Digite para buscar o item",
    quantidade="Quantidade (padrao: 1)"
)
@app_commands.choices(categoria=[
    app_commands.Choice(name="Pocoes",             value="pocoes"),
    app_commands.Choice(name="Armas Guerreiro",    value="arma_guerreiro"),
    app_commands.Choice(name="Armas Arqueiro",     value="arma_arqueiro"),
    app_commands.Choice(name="Armas Mago",         value="arma_mago"),
    app_commands.Choice(name="Armas Paladino",     value="arma_paladino"),
    app_commands.Choice(name="Armas Necromante",   value="arma_necromante"),
    app_commands.Choice(name="Armas Dracomante",   value="arma_dracomante"),
    app_commands.Choice(name="Armas Arcano",       value="arma_arcano"),
    app_commands.Choice(name="Armaduras Guerreiro",value="arm_guerreiro"),
    app_commands.Choice(name="Armaduras Arqueiro", value="arm_arqueiro"),
    app_commands.Choice(name="Armaduras Mago",     value="arm_mago"),
    app_commands.Choice(name="Armaduras Paladino", value="arm_paladino"),
    app_commands.Choice(name="Armaduras Necromante",value="arm_necromante"),
    app_commands.Choice(name="Armaduras Dracomante",value="arm_dracomante"),
    app_commands.Choice(name="Armaduras Arcano",   value="arm_arcano"),
    app_commands.Choice(name="Materiais",          value="materiais"),
])
@app_commands.autocomplete(item=autocomplete_item_categoria)
@app_commands.checks.has_permissions(administrator=True)
async def set_item(interaction: discord.Interaction, jogador: discord.Member,
                   categoria: str, item: str, quantidade: int = 1):
    await interaction.response.defer(ephemeral=True)
    if not await get_personagem(jogador.id):
        await interaction.followup.send(f"{jogador.display_name} nao tem personagem!", ephemeral=True); return

    it = get_item_por_chave(item)
    if not it:
        itens_cat = get_itens_por_categoria(categoria)
        it = next((i for i in itens_cat if i["id"] == item), None)
    if not it:
        await interaction.followup.send(f"Item nao encontrado! Selecione da lista de sugestoes.", ephemeral=True); return

    qtd = max(1, min(quantidade, 99))
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        ex = await conn.fetchrow(
            "SELECT id,quantidade FROM inventario WHERE user_id=$1 AND item_id=$2",
            jogador.id, it["id"])
        if ex:
            await conn.execute("UPDATE inventario SET quantidade=quantidade+$1 WHERE id=$2", qtd, ex["id"])
        else:
            await conn.execute(
                "INSERT INTO inventario(user_id,item_id,nome,tipo,raridade,emoji,descricao) VALUES($1,$2,$3,$4,$5,$6,$7)",
                jogador.id, it["id"], it["nome"], it["tipo"], it["raridade"], it["emoji"], it.get("desc",""))

    cor = COR_RAR_BOT.get(it["raridade"], 0x888780)
    await interaction.followup.send(
        embed=discord.Embed(
            title="Item adicionado!",
            description=f"{it['emoji']} **{it['nome']}** x{qtd} para {jogador.mention}!",
            color=cor
        ), ephemeral=True
    )

# ─── /set-moedas ─────────────────────────────────────────────────

@bot.tree.command(name="set-moedas", description="[ADMIN] Define ou adiciona moedas")
@app_commands.describe(jogador="Jogador alvo", quantidade="Quantidade", modo="definir ou adicionar")
@app_commands.choices(modo=[
    app_commands.Choice(name="Adicionar", value="adicionar"),
    app_commands.Choice(name="Definir",   value="definir"),
])
@app_commands.checks.has_permissions(administrator=True)
async def set_moedas(interaction: discord.Interaction, jogador: discord.Member, quantidade: int, modo: str = "adicionar"):
    await interaction.response.defer(ephemeral=True)
    if not await get_personagem(jogador.id):
        await interaction.followup.send(f"{jogador.display_name} nao tem personagem!", ephemeral=True); return
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        if modo == "definir": await conn.execute("UPDATE personagens SET moedas=$1 WHERE user_id=$2", quantidade, jogador.id)
        else: await conn.execute("UPDATE personagens SET moedas=moedas+$1 WHERE user_id=$2", quantidade, jogador.id)
    await interaction.followup.send(f"Moedas de {jogador.display_name} atualizadas!", ephemeral=True)

# ─── /set-nivel ──────────────────────────────────────────────────

@bot.tree.command(name="set-nivel", description="[ADMIN] Define o nivel de um jogador")
@app_commands.describe(jogador="Jogador alvo", nivel="Nivel (1-100)")
@app_commands.checks.has_permissions(administrator=True)
async def set_nivel(interaction: discord.Interaction, jogador: discord.Member, nivel: int):
    await interaction.response.defer(ephemeral=True)
    if nivel < 1 or nivel > 100:
        await interaction.followup.send("Nivel deve ser entre 1 e 100!", ephemeral=True); return
    p = await get_personagem(jogador.id)
    if not p:
        await interaction.followup.send(f"{jogador.display_name} nao tem personagem!", ephemeral=True); return
    nd = nivel - p["nivel"]
    hp_n = max(50, p["hp_max"]+nd*5); atk_n = max(5, p["ataque"]+nd*2); dfs_n = max(3, p["defesa"]+nd*1)
    mana_n = calcular_mana_max(p["classe_id"], nivel, p["poder_valor"], p["destino_id"])
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        await conn.execute("UPDATE personagens SET nivel=$1,xp=0,hp_max=$2,hp_atual=$3,ataque=$4,defesa=$5,mana_max=$6,mana_atual=$7 WHERE user_id=$8",
            nivel, hp_n, hp_n, atk_n, dfs_n, mana_n, mana_n, jogador.id)
        from catalogo import SKILLS_COMPLETAS
        for sk in SKILLS_COMPLETAS.get(p["classe_id"], []):
            if sk["nivel"] <= nivel:
                await conn.execute("INSERT INTO skills_desbloqueadas(user_id,skill_id) VALUES($1,$2) ON CONFLICT DO NOTHING", jogador.id, sk["id"])
    guild = interaction.guild
    if guild:
        member = guild.get_member(jogador.id)
        if member: await atualizar_todos_cargos(guild, member, nivel)
    rank_o = get_rank(nivel)
    await interaction.followup.send(f"{jogador.mention} agora e Nivel {nivel} — {rank_o['emoji']} Rank {rank_o['rank']}!", ephemeral=True)

# ─── /set-giros ──────────────────────────────────────────────────

@bot.tree.command(name="set-giros", description="[ADMIN] Da fichas de roleta a um jogador")
@app_commands.describe(jogador="Jogador alvo")
@app_commands.checks.has_permissions(administrator=True)
async def set_giros(interaction: discord.Interaction, jogador: discord.Member):
    await cmd_set_giros(interaction, jogador)

# ─── /deletar_personagem ─────────────────────────────────────────

@bot.tree.command(name="deletar_personagem", description="Deleta seu personagem permanentemente")
async def deletar_personagem(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Voce nao tem personagem!", ephemeral=True); return
    class ConfView(discord.ui.View):
        def __init__(self): super().__init__(timeout=30); self.ok = None
        @discord.ui.button(label="Confirmar delecao", style=discord.ButtonStyle.danger)
        async def sim(self, inter, b):
            if inter.user.id != interaction.user.id: return
            self.ok = True; await inter.response.defer(); self.stop()
        @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
        async def nao(self, inter, b):
            self.ok = False; await inter.response.defer(); self.stop()
    v = ConfView()
    await interaction.followup.send("ATENCAO: Isso apaga seu personagem! Confirma?", view=v, ephemeral=True)
    await v.wait()
    if not v.ok: return
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        for t in ["skills_equipadas","skills_desbloqueadas","inventario","missoes_diarias","conquistas","giros"]:
            try: await conn.execute(f"DELETE FROM {t} WHERE user_id=$1", interaction.user.id)
            except: pass
        await conn.execute("DELETE FROM personagens WHERE user_id=$1", interaction.user.id)
    await interaction.followup.send("Personagem deletado. Use /criar_personagem para recomecar.", ephemeral=True)

# ─── /criar-evento ───────────────────────────────────────────────

@bot.tree.command(name="criar-evento", description="[ADMIN] Cria um novo evento no servidor")
@app_commands.describe(
    tipo="Tipo do evento",
    premio_tipo="Tipo de premio",
    premio_valor="Valor do premio",
    canal="Canal onde o evento sera anunciado"
)
@app_commands.choices(tipo=[
    app_commands.Choice(name="Torneio de Batalha",  value="batalha"),
    app_commands.Choice(name="Corrida de Dungeon",  value="dungeon"),
    app_commands.Choice(name="Coleta de Materiais", value="coleta"),
    app_commands.Choice(name="Corrida de Nivel",    value="nivel"),
    app_commands.Choice(name="Evento Livre",        value="livre"),
])
@app_commands.choices(premio_tipo=[
    app_commands.Choice(name="Moedas",           value="moedas"),
    app_commands.Choice(name="XP",               value="xp"),
    app_commands.Choice(name="Fichas de Roleta", value="ficha"),
    app_commands.Choice(name="Item especifico",  value="item"),
    app_commands.Choice(name="Cargo exclusivo",  value="cargo"),
    app_commands.Choice(name="Classe especial",  value="classe"),
])
@app_commands.autocomplete(premio_valor=autocomplete_item_premio, canal=autocomplete_canal)
@app_commands.checks.has_permissions(administrator=True)
async def criar_evento(interaction: discord.Interaction, tipo: str, premio_tipo: str, premio_valor: str, canal: str):
    canal_obj = resolver_canal(interaction.guild, canal)
    if not canal_obj: await interaction.response.send_message('Canal nao encontrado!', ephemeral=True); return
    await cmd_criar_evento(interaction, tipo, premio_tipo, premio_valor, canal_obj)

# ─── /eventos ────────────────────────────────────────────────────

@bot.tree.command(name="eventos", description="Lista os eventos ativos no servidor")
async def eventos(interaction: discord.Interaction):
    await cmd_eventos(interaction)

# ─── /evento-info ────────────────────────────────────────────────

@bot.tree.command(name="evento-info", description="Detalhes de um evento e ranking de participantes")
@app_commands.describe(evento_id="ID do evento (0 = evento ativo atual)")
async def evento_info(interaction: discord.Interaction, evento_id: int = 0):
    await cmd_evento_info(interaction, evento_id)

# ─── /encerrar-evento ────────────────────────────────────────────

@bot.tree.command(name="encerrar-evento", description="[ADMIN] Encerra evento e entrega premio ao 1o lugar")
@app_commands.describe(evento_id="ID do evento a encerrar")
@app_commands.checks.has_permissions(administrator=True)
async def encerrar_evento(interaction: discord.Interaction, evento_id: int):
    await cmd_encerrar_evento(interaction, evento_id)

# ─── /add-pontos ─────────────────────────────────────────────────

@bot.tree.command(name="add-pontos", description="[ADMIN] Adiciona pontos a um participante do evento")
@app_commands.describe(jogador="Jogador alvo", pontos="Pontos a adicionar", evento_id="ID do evento (0 = atual)")
@app_commands.checks.has_permissions(administrator=True)
async def add_pontos(interaction: discord.Interaction, jogador: discord.Member, pontos: int, evento_id: int = 0):
    await cmd_add_pontos(interaction, jogador, pontos, evento_id)

# ─── /anunciar ───────────────────────────────────────────────────

@bot.tree.command(name="anunciar", description="[ADMIN] Cria e envia um anuncio formatado")
@app_commands.describe(
    canal="Canal (digite para buscar)",
    cor="Cor do embed",
    ping="Cargo a pingar (opcional)"
)
@app_commands.autocomplete(canal=autocomplete_canal)
@app_commands.choices(cor=[
    app_commands.Choice(name="Dourado", value="dourado"),
    app_commands.Choice(name="Roxo", value="roxo"),
    app_commands.Choice(name="Verde", value="verde"),
    app_commands.Choice(name="Azul", value="azul"),
    app_commands.Choice(name="Vermelho", value="vermelho"),
    app_commands.Choice(name="Laranja", value="laranja"),
    app_commands.Choice(name="Cinza", value="cinza"),
    app_commands.Choice(name="Preto", value="preto"),
])
@app_commands.checks.has_permissions(administrator=True)
async def anunciar(interaction: discord.Interaction, canal: str,
                   cor: str = "roxo", ping: discord.Role = None):
    canal_obj = resolver_canal(interaction.guild, canal)
    if not canal_obj: await interaction.response.send_message('Canal nao encontrado!', ephemeral=True); return
    await cmd_anunciar(interaction, canal_obj, cor, ping)

# ─── /anunciar-evento ────────────────────────────────────────────

@bot.tree.command(name="anunciar-evento", description="[ADMIN] Anuncia um evento com data e premio")
@app_commands.describe(
    canal="Canal (digite para buscar)",
    ping="Cargo a pingar (opcional)"
)
@app_commands.autocomplete(canal=autocomplete_canal)
@app_commands.checks.has_permissions(administrator=True)
async def anunciar_evento(interaction: discord.Interaction, canal: str,
                          ping: discord.Role = None):
    canal_obj = resolver_canal(interaction.guild, canal)
    if not canal_obj: await interaction.response.send_message('Canal nao encontrado!', ephemeral=True); return
    await cmd_anunciar_evento(interaction, canal_obj, ping)

# ─── /agendar-anuncio ────────────────────────────────────────────

@bot.tree.command(name="agendar-anuncio", description="[ADMIN] Agenda um anuncio para enviar depois")
@app_commands.describe(
    canal="Canal do anuncio",
    cor="Cor do embed"
)
@app_commands.choices(cor=[
    app_commands.Choice(name="Dourado", value="dourado"),
    app_commands.Choice(name="Roxo", value="roxo"),
    app_commands.Choice(name="Verde", value="verde"),
    app_commands.Choice(name="Azul", value="azul"),
    app_commands.Choice(name="Vermelho", value="vermelho"),
    app_commands.Choice(name="Laranja", value="laranja"),
    app_commands.Choice(name="Cinza", value="cinza"),
    app_commands.Choice(name="Preto", value="preto"),
])
@app_commands.checks.has_permissions(administrator=True)
async def agendar_anuncio(interaction: discord.Interaction, canal: str,
                          cor: str = "dourado"):
    canal_obj = resolver_canal(interaction.guild, canal)
    if not canal_obj: await interaction.response.send_message('Canal nao encontrado!', ephemeral=True); return
    await cmd_agendar_anuncio(interaction, canal_obj, cor)

# ─── /torneio-criar ──────────────────────────────────────────────

@bot.tree.command(name="torneio-criar", description="[ADMIN] Cria um torneio PvP")
@app_commands.describe(
    canal="Canal onde o torneio sera anunciado",
    premio_1="Premio do 1 lugar (obrigatorio)",
    premio_2="Premio do 2 lugar (opcional)",
    premio_3="Premio do 3 lugar (opcional)"
)
@app_commands.autocomplete(premio_1=autocomplete_item_premio, premio_2=autocomplete_item_premio, premio_3=autocomplete_item_premio, canal=autocomplete_canal)
@app_commands.checks.has_permissions(administrator=True)
async def torneio_criar(interaction: discord.Interaction, canal: str,
                         premio_1: str, premio_2: str = "", premio_3: str = ""):
    canal_obj = resolver_canal(interaction.guild, canal)
    if not canal_obj: await interaction.response.send_message('Canal nao encontrado!', ephemeral=True); return
    await cmd_torneio_criar(interaction, premio_1, premio_2, premio_3, canal_obj)

# ─── /torneio-status ─────────────────────────────────────────────

@bot.tree.command(name="torneio-status", description="Veja as chaves e status de um torneio")
@app_commands.describe(torneio_id="ID do torneio")
async def torneio_status(interaction: discord.Interaction, torneio_id: int):
    await cmd_torneio_status(interaction, torneio_id)

# ─── /torneio-lutar ──────────────────────────────────────────────

@bot.tree.command(name="torneio-lutar", description="[ADMIN] Inicia uma luta do torneio")
@app_commands.describe(torneio_id="ID do torneio", jogador1="Jogador 1", jogador2="Jogador 2")
@app_commands.checks.has_permissions(administrator=True)
async def torneio_lutar(interaction: discord.Interaction, torneio_id: int,
                         jogador1: discord.Member, jogador2: discord.Member):
    await cmd_torneio_lutar(interaction, torneio_id, jogador1, jogador2)

# ─── /torneio-fechar-inscricoes ──────────────────────────────────

@bot.tree.command(name="torneio-fechar-inscricoes", description="[ADMIN] Fecha inscricoes e monta as chaves")
@app_commands.describe(torneio_id="ID do torneio")
@app_commands.checks.has_permissions(administrator=True)
async def torneio_fechar_inscricoes(interaction: discord.Interaction, torneio_id: int):
    await cmd_torneio_fechar_inscricoes(interaction, torneio_id)

# ─── /torneio-cancelar ───────────────────────────────────────────

@bot.tree.command(name="torneio-cancelar", description="[ADMIN] Cancela torneio e devolve inscricoes")
@app_commands.describe(torneio_id="ID do torneio")
@app_commands.checks.has_permissions(administrator=True)
async def torneio_cancelar(interaction: discord.Interaction, torneio_id: int):
    await cmd_torneio_cancelar(interaction, torneio_id)

# ─── /dungeon-evento-criar ───────────────────────────────────────

@bot.tree.command(name="dungeon-evento-criar", description="[ADMIN] Cria uma dungeon de evento customizada")
@app_commands.describe(
    canal="Canal onde a dungeon sera anunciada",
    premio="Premio para quem completar"
)
@app_commands.autocomplete(premio=autocomplete_item_premio, canal=autocomplete_canal)
@app_commands.checks.has_permissions(administrator=True)
async def dungeon_evento_criar(interaction: discord.Interaction, canal: str, premio: str):
    canal_obj = resolver_canal(interaction.guild, canal)
    canal_id = canal_obj.id if canal_obj else 0
    await interaction.response.send_modal(DungeonEventoCriarModal(interaction.guild, premio, canal_id))

# ─── /dungeon-evento-configurar ──────────────────────────────────

@bot.tree.command(name="dungeon-evento-configurar", description="[ADMIN] Configura os andares da dungeon de evento")
@app_commands.describe(dungeon_id="ID da dungeon")
@app_commands.checks.has_permissions(administrator=True)
async def dungeon_evento_configurar(interaction: discord.Interaction, dungeon_id: int):
    await interaction.response.send_modal(AdicionarAndarModal(dungeon_id))

# ─── /dungeon-evento-ativar ──────────────────────────────────────

@bot.tree.command(name="dungeon-evento-ativar", description="[ADMIN] Ativa e anuncia a dungeon de evento")
@app_commands.describe(dungeon_id="ID da dungeon")
@app_commands.checks.has_permissions(administrator=True)
async def dungeon_evento_ativar(interaction: discord.Interaction, dungeon_id: int):
    await cmd_dungeon_evento_ativar(interaction, dungeon_id)

# ─── /dungeon-evento-info ────────────────────────────────────────

@bot.tree.command(name="dungeon-evento-info", description="Veja detalhes e andares de uma dungeon de evento")
@app_commands.describe(dungeon_id="ID da dungeon")
async def dungeon_evento_info(interaction: discord.Interaction, dungeon_id: int):
    await cmd_dungeon_evento_info(interaction, dungeon_id)

# ─── /dungeon-evento-fechar ──────────────────────────────────────

@bot.tree.command(name="dungeon-evento-fechar", description="[ADMIN] Fecha uma dungeon de evento")
@app_commands.describe(dungeon_id="ID da dungeon")
@app_commands.checks.has_permissions(administrator=True)
async def dungeon_evento_fechar(interaction: discord.Interaction, dungeon_id: int):
    await cmd_dungeon_evento_fechar(interaction, dungeon_id)

# ─── /loja-sazonal ───────────────────────────────────────────────

@bot.tree.command(name="loja-sazonal", description="Compre itens sazonais e ofertas do dia")
async def loja_sazonal(interaction: discord.Interaction):
    if not await checar_batalha(interaction): return
    await cmd_loja_sazonal(interaction)

# ─── /loja-sazonal-adicionar ─────────────────────────────────────

@bot.tree.command(name="loja-sazonal-adicionar", description="[ADMIN] Adiciona item permanente a loja sazonal")
@app_commands.describe(item="Digite para buscar o item", preco="Preco em moedas", estoque="Estoque (-1 = ilimitado)")
@app_commands.autocomplete(item=autocomplete_item_todos)
@app_commands.checks.has_permissions(administrator=True)
async def loja_sazonal_adicionar(interaction: discord.Interaction, item: str, preco: int = 500, estoque: int = -1):
    await interaction.response.defer(ephemeral=True)
    it = get_item_por_chave(item)
    if not it:
        await interaction.followup.send("Item nao encontrado! Selecione da lista de sugestoes.", ephemeral=True); return
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        await conn.execute("""
            INSERT INTO loja_sazonal(item_id,nome,emoji,tipo,raridade,descricao,preco,estoque)
            VALUES($1,$2,$3,$4,$5,$6,$7,$8)
        """, it["id"], it["nome"], it["emoji"], it["tipo"], it["raridade"],
            it.get("desc",""), preco, estoque)
    est_txt = str(estoque) if estoque >= 0 else "Ilimitado"
    await interaction.followup.send(
        f"Adicionado a loja sazonal! {it['emoji']} **{it['nome']}** [{it['raridade']}] — {preco} moedas | Estoque: {est_txt}",
        ephemeral=True)

# ─── /loja-rotativa-adicionar ────────────────────────────────────

@bot.tree.command(name="loja-rotativa-adicionar", description="[ADMIN] Adiciona oferta do dia na loja rotativa")
@app_commands.describe(item="Digite para buscar o item", preco="Preco em moedas", estoque="Estoque do dia")
@app_commands.autocomplete(item=autocomplete_item_todos)
@app_commands.checks.has_permissions(administrator=True)
async def loja_rotativa_adicionar(interaction: discord.Interaction, item: str, preco: int = 300, estoque: int = 3):
    await interaction.response.defer(ephemeral=True)
    it = get_item_por_chave(item)
    if not it:
        await interaction.followup.send("Item nao encontrado! Selecione da lista de sugestoes.", ephemeral=True); return
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        await conn.execute("""
            INSERT INTO loja_rotativa(item_id,nome,emoji,tipo,raridade,descricao,preco,estoque)
            VALUES($1,$2,$3,$4,$5,$6,$7,$8)
        """, it["id"], it["nome"], it["emoji"], it["tipo"], it["raridade"],
            it.get("desc",""), preco, estoque)
    await interaction.followup.send(
        f"Adicionado a oferta do dia! {it['emoji']} **{it['nome']}** [{it['raridade']}] — {preco} moedas | Estoque: {estoque}",
        ephemeral=True)

# ─── /loja-sazonal-remover ───────────────────────────────────────

@bot.tree.command(name="loja-sazonal-remover", description="[ADMIN] Remove item da loja sazonal pelo ID")
@app_commands.describe(item_id="ID numerico do item")
@app_commands.checks.has_permissions(administrator=True)
async def loja_sazonal_remover(interaction: discord.Interaction, item_id: int):
    await cmd_loja_sazonal_remover(interaction, item_id)

# ─── /historico ──────────────────────────────────────────────────

@bot.tree.command(name="historico", description="Veja seu historico das ultimas batalhas")
async def historico(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True); return
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        try:
            logs = await conn.fetch("""
                SELECT * FROM log_batalhas WHERE user_id=$1
                ORDER BY criado_em DESC LIMIT 10
            """, interaction.user.id)
        except:
            logs = []
    if not logs:
        await interaction.followup.send("Nenhuma batalha registrada ainda!", ephemeral=True); return
    embed = discord.Embed(title=f"📜 Historico de {p['nome']}", color=0x7F77DD)
    linhas = []
    for l in logs:
        emoji = "✅" if l["resultado"] == "vitoria" else "❌"
        tempo = l["criado_em"].strftime("%d/%m %H:%M") if l["criado_em"] else "?"
        linhas.append(f"{emoji} **{l['tipo'].title()}** — {l['oponente']} | +{l['xp_ganho']}XP +{l['moedas_ganhas']}🪙 | Nv{l['nivel_apos']} | {tempo}")
    embed.description = "\n".join(linhas)
    await interaction.followup.send(embed=embed, ephemeral=True)

# ─── /guilda-missoes ─────────────────────────────────────────────

@bot.tree.command(name="guilda-missoes", description="Veja as missoes semanais da sua guilda")
async def guilda_missoes(interaction: discord.Interaction):
    await cmd_guilda_missoes(interaction)

# ─── /guilda-retirar ─────────────────────────────────────────────

@bot.tree.command(name="guilda-retirar", description="[Mestre] Retira moedas do banco da guilda")
@app_commands.describe(valor="Quantidade de moedas a retirar")
async def guilda_retirar(interaction: discord.Interaction, valor: int):
    await cmd_guilda_retirar(interaction, valor)

# ─── /treinar-dupla ──────────────────────────────────────────────

@bot.tree.command(name="treinar-dupla", description="Batalha em dupla com outro jogador da guilda")
@app_commands.describe(parceiro="Jogador parceiro", dificuldade="Dificuldade")
@app_commands.choices(dificuldade=[
    app_commands.Choice(name="Facil",    value="facil"),
    app_commands.Choice(name="Medio",    value="medio"),
    app_commands.Choice(name="Dificil",  value="dificil"),
    app_commands.Choice(name="Lendario", value="lendario"),
])
async def treinar_dupla(interaction: discord.Interaction, parceiro: discord.Member,
                         dificuldade: str = "facil"):
    await interaction.response.defer()
    if parceiro.bot or parceiro.id == interaction.user.id:
        await interaction.followup.send("Parceiro invalido!", ephemeral=True); return
    if em_batalha(interaction.user.id) or em_batalha(parceiro.id):
        await interaction.followup.send("Um dos jogadores ja esta em batalha!", ephemeral=True); return
    p1 = await get_personagem(interaction.user.id)
    p2 = await get_personagem(parceiro.id)
    if not p1 or not p2:
        await interaction.followup.send("Ambos precisam ter personagem!", ephemeral=True); return

    class AceitarView(discord.ui.View):
        def __init__(self): super().__init__(timeout=60); self.ok = None
        @discord.ui.button(label="Aceitar!", style=discord.ButtonStyle.success)
        async def sim(self, inter, b):
            if inter.user.id != parceiro.id: return
            self.ok = True; await inter.response.defer(); self.stop()
        @discord.ui.button(label="Recusar", style=discord.ButtonStyle.danger)
        async def nao(self, inter, b):
            if inter.user.id != parceiro.id: return
            self.ok = False; await inter.response.defer(); self.stop()

    v = AceitarView()
    embed_inv = discord.Embed(
        title="Convite de Batalha em Dupla!",
        description=f"{interaction.user.mention} te convida para batalhar juntos! Dificuldade: **{dificuldade.title()}**",
        color=0x7F77DD
    )
    await interaction.followup.send(content=parceiro.mention, embed=embed_inv, view=v)
    await v.wait()
    if not v.ok:
        await interaction.followup.send(f"{parceiro.display_name} recusou o convite.", ephemeral=True); return

    monstros_d = [m for m in MONSTROS if m["dificuldade"] == dificuldade]
    if not monstros_d:
        await interaction.followup.send("Dificuldade invalida!", ephemeral=True); return
    monstro = random.choice(monstros_d)
    arena = random.choice(ARENAS)
    await rodar_treino_dupla(interaction, p1, p2, monstro, arena,
                              interaction.user, parceiro)

# ─── /guilda-criar ───────────────────────────────────────────────

@bot.tree.command(name="guilda-criar", description="Funda uma nova guilda (custa 5000 moedas)")
async def guilda_criar(interaction: discord.Interaction):
    await cmd_guilda_criar(interaction)

# ─── /guilda-info ────────────────────────────────────────────────

@bot.tree.command(name="guilda-info", description="Informacoes sobre uma guilda")
@app_commands.describe(nome="Nome da guilda (vazio = sua guilda)")
async def guilda_info(interaction: discord.Interaction, nome: str = ""):
    await cmd_guilda_info(interaction, nome)

# ─── /guilda-convidar ────────────────────────────────────────────

@bot.tree.command(name="guilda-convidar", description="Convida um jogador para sua guilda")
@app_commands.describe(jogador="Jogador a convidar")
async def guilda_convidar(interaction: discord.Interaction, jogador: discord.Member):
    await cmd_guilda_convidar(interaction, jogador)

# ─── /guilda-sair ────────────────────────────────────────────────

@bot.tree.command(name="guilda-sair", description="Sai da sua guilda atual")
async def guilda_sair(interaction: discord.Interaction):
    await cmd_guilda_sair(interaction)

# ─── /guilda-expulsar ────────────────────────────────────────────

@bot.tree.command(name="guilda-expulsar", description="[Mestre] Expulsa um membro da guilda")
@app_commands.describe(jogador="Membro a expulsar")
async def guilda_expulsar(interaction: discord.Interaction, jogador: discord.Member):
    await cmd_guilda_expulsar(interaction, jogador)

# ─── /guilda-promover ────────────────────────────────────────────

@bot.tree.command(name="guilda-promover", description="[Mestre] Promove um membro ou transfere lideranca")
@app_commands.describe(jogador="Membro a promover")
async def guilda_promover(interaction: discord.Interaction, jogador: discord.Member):
    await cmd_guilda_promover(interaction, jogador)

# ─── /guilda-depositar ───────────────────────────────────────────

@bot.tree.command(name="guilda-depositar", description="Deposita moedas no banco da guilda")
@app_commands.describe(valor="Quantidade de moedas")
async def guilda_depositar(interaction: discord.Interaction, valor: int):
    await cmd_guilda_depositar(interaction, valor)

# ─── /guilda-ranking ─────────────────────────────────────────────

@bot.tree.command(name="guilda-ranking", description="Ranking de todas as guildas do servidor")
async def guilda_ranking(interaction: discord.Interaction):
    await cmd_guilda_ranking(interaction)

# ─── /tutorial ───────────────────────────────────────────────────

TUTORIAL_SECOES = {
    "personagem": ("Seu Personagem", 0x7F77DD,
        "`/perfil` - Ver sua ficha completa\n"
        "`/inventario` - Ver seus itens\n"
        "`/skills` - Ver suas habilidades\n"
        "`/setup` - Equipar armas e armaduras\n\n"
        "Ganhe XP para subir de nivel e evoluir.\n"
        "Cada nivel aumenta HP, Mana, ATK e DEF automaticamente."),
    "combate": ("Sistema de Combate", 0xE24B4A,
        "`/treinar [dificuldade]` - Batalhar contra monstros\n"
        "`/desafiar @jogador` - Duelo PvP\n"
        "`/treinar-dupla @parceiro` - Batalha em dupla (+20%)\n\n"
        "Durante a batalha: use skills, se defenda,\n"
        "use pocoes da mochila ou fuja.\n\n"
        "**Dificuldades:** Facil > Medio > Dificil > Lendario"),
    "dungeons": ("Dungeons", 0x7F77DD,
        "`/dungeon` - Entrar em uma dungeon\n\n"
        "Cada dungeon tem andares com monstros diferentes.\n"
        "Derrote todos para avancar e ganhar loot.\n"
        "Se morrer perde as recompensas do run.\n\n"
        "Masmorras vao do Rank F ao Rank SS."),
    "loja": ("Inventario e Loja", 0x1D9E75,
        "`/inventario` - Ver seus itens\n"
        "`/loja` - Comprar armas, armaduras e pocoes\n"
        "`/loja-sazonal` - Itens especiais e ofertas do dia\n"
        "`/ferreiro` - Forjar equipamentos raros\n"
        "`/mercado` - Vender seus itens\n\n"
        "Equipe sempre a melhor arma e armadura para sua classe!"),
    "hospital": ("Hospital e Recuperacao", 0x3498DB,
        "`/hospital` - Acessar o hospital\n\n"
        "Opcoes de cura:\n"
        "- Comprar cura com moedas\n"
        "- Descanso gratis de 30 minutos\n"
        "- Pocoes durante batalhas\n\n"
        "Use o descanso gratis sempre que possivel!"),
    "guildas": ("Guildas", 0xE4AF3C,
        "`/guilda-info` - Ver informacoes da sua guilda\n"
        "`/guilda-missoes` - Ver missoes semanais\n"
        "`/guilda-depositar` - Depositar no banco\n\n"
        "Beneficios: bonus de XP/moedas, missoes semanais,\n"
        "batalhas em dupla e canal exclusivo.\n\n"
        "Para criar: `/guilda-criar` (custa 5000 moedas)"),
    "ranking": ("Rankings e Conquistas", 0xE4AF3C,
        "`/ranking` - Ver ranking do servidor\n"
        "`/conquistas` - Ver suas conquistas\n"
        "`/missoes` - Ver missoes diarias\n"
        "`/historico` - Ver historico de batalhas\n\n"
        "Rankings: nivel, vitorias, rico, dungeons, torneios.\n"
        "Complete conquistas para ganhar recompensas!"),
    "eventos": ("Eventos e Torneios", 0xD85A30,
        "`/eventos` - Ver eventos ativos\n"
        "`/evento-info` - Detalhes e ranking\n\n"
        "Tipos: torneios PvP, dungeons de evento,\n"
        "eventos especiais com premios exclusivos.\n\n"
        "Fique de olho nos canais de anuncio!"),
    "dicas": ("Dicas para Iniciantes", 0x1D9E75,
        "**Por onde comecar:**\n"
        "1. Use `/loja` e compre uma arma\n"
        "2. Use `/treinar facil` para ganhar XP\n"
        "3. Complete as `/missoes` diarias\n"
        "4. Entre numa guilda para bonus de XP\n"
        "5. Explore `/dungeon` quando estiver forte\n\n"
        "**Como evoluir rapido:**\n"
        "Faca missoes diarias, participe de eventos,\n"
        "use o descanso gratis do hospital e jogue em dupla!"),
}

@bot.tree.command(name="tutorial", description="Guia completo do servidor — escolha uma secao")
@app_commands.describe(secao="Qual secao voce quer ver?")
@app_commands.choices(secao=[
    app_commands.Choice(name="Personagem — perfil, skills e progressao", value="personagem"),
    app_commands.Choice(name="Combate — treino, PvP e batalha em dupla",  value="combate"),
    app_commands.Choice(name="Dungeons — masmorras e recompensas",         value="dungeons"),
    app_commands.Choice(name="Loja e Inventario — itens e equipamentos",   value="loja"),
    app_commands.Choice(name="Hospital — cura e recuperacao",              value="hospital"),
    app_commands.Choice(name="Guildas — unir forcas",                      value="guildas"),
    app_commands.Choice(name="Rankings e Conquistas",                      value="ranking"),
    app_commands.Choice(name="Eventos e Torneios",                         value="eventos"),
    app_commands.Choice(name="Dicas para Iniciantes",                      value="dicas"),
])
async def tutorial(interaction: discord.Interaction, secao: str = "dicas"):
    titulo, cor, desc = TUTORIAL_SECOES.get(secao, TUTORIAL_SECOES["dicas"])
    embed = discord.Embed(title=titulo, description=desc, color=cor)
    embed.set_footer(text="Villa Eldoria RPG | Use /tutorial novamente para ver outra secao")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ─── /expedicao-criar ────────────────────────────────────────────

@bot.tree.command(name="expedicao-criar", description="[ADMIN] Cria uma expedição narrativa com IA")
@app_commands.describe(canal="Canal onde a expedição sera anunciada")
@app_commands.autocomplete(canal=autocomplete_canal)
@app_commands.checks.has_permissions(administrator=True)
async def expedicao_criar(interaction: discord.Interaction, canal: str):
    canal_obj = resolver_canal(interaction.guild, canal)
    if not canal_obj:
        await interaction.response.send_message("Canal não encontrado!", ephemeral=True)
        return
    await cmd_expedicao_criar(interaction, canal_obj, bot)

# ─── /expedicao-iniciar ──────────────────────────────────────────

@bot.tree.command(name="expedicao-iniciar", description="[ADMIN] Inicia a aventura de uma expedição")
@app_commands.describe(expedicao_id="ID da expedição")
@app_commands.checks.has_permissions(administrator=True)
async def expedicao_iniciar(interaction: discord.Interaction, expedicao_id: int):
    await cmd_expedicao_iniciar(interaction, expedicao_id)

# ─── /expedicao-encerrar ─────────────────────────────────────────

@bot.tree.command(name="expedicao-encerrar", description="[ADMIN] Encerra uma expedição manualmente")
@app_commands.describe(expedicao_id="ID da expedição", sucesso="A expedição foi um sucesso?")
@app_commands.checks.has_permissions(administrator=True)
async def expedicao_encerrar(interaction: discord.Interaction, expedicao_id: int, sucesso: bool = True):
    await cmd_expedicao_encerrar(interaction, expedicao_id, sucesso)

# ─── /expedicao-status ───────────────────────────────────────────

@bot.tree.command(name="expedicao-status", description="Lista todas as expedições ativas")
async def expedicao_status(interaction: discord.Interaction):
    await cmd_expedicao_status(interaction)

# ─── /ajuda ──────────────────────────────────────────────────────

@bot.tree.command(name="ajuda", description="Lista todos os comandos do RPG")
async def ajuda(interaction: discord.Interaction):
    embed = discord.Embed(title="Comandos — Villa Eldoria RPG", color=0x7F77DD)
    embed.add_field(name="Personagem", value="`/criar_personagem` `/perfil` `/skills` `/setup` `/deletar_personagem`", inline=False)
    embed.add_field(name="Inventario", value="`/inventario` `/equipar` `/jogar-fora` `/dar`", inline=False)
    embed.add_field(name="Batalha",    value="`/treinar` `/desafiar` `/dungeon` `/treinar-dupla`", inline=False)
    embed.add_field(name="Economia",   value="`/loja` `/loja-sazonal` `/ferreiro` `/hospital` `/mercado` `/mercador`", inline=False)
    embed.add_field(name="Progresso",  value="`/missoes` `/conquistas` `/ranking` `/girar`", inline=False)
    embed.add_field(name="Admin",      value="`/set-item` `/set-moedas` `/set-nivel` `/set-giros`", inline=False)
    embed.add_field(name="Eventos",    value="`/criar-evento` `/eventos` `/evento-info` `/encerrar-evento` `/add-pontos`", inline=False)
    embed.add_field(name="Anuncios",   value="`/anunciar` `/anunciar-evento` `/agendar-anuncio`", inline=False)
    embed.add_field(name="Guildas",    value="`/guilda-criar` `/guilda-info` `/guilda-missoes` `/guilda-convidar` `/guilda-sair` `/guilda-promover` `/guilda-depositar` `/guilda-retirar` `/guilda-ranking`", inline=False)
    embed.add_field(name="Torneio",    value="`/torneio-criar` `/torneio-status` `/torneio-lutar` `/torneio-fechar-inscricoes` `/torneio-cancelar`", inline=False)
    embed.add_field(name="Dungeon Evento", value="`/dungeon-evento-criar` `/dungeon-evento-configurar` `/dungeon-evento-ativar` `/dungeon-evento-info` `/dungeon-evento-fechar`", inline=False)
    embed.add_field(name="Expedição",  value="`/expedicao-criar` `/expedicao-status` `/expedicao-iniciar` `/expedicao-encerrar`", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ─── SYNC MANUAL ─────────────────────────────────────────────────

@bot.command(name="sync")
async def sync_cmd(ctx):
    try:
        guild_id = int(os.getenv("GUILD_ID","0"))
        total = 0
        if guild_id:
            guild_obj = discord.Object(id=guild_id)
            bot.tree.copy_global_to(guild=guild_obj)
            s = await bot.tree.sync(guild=guild_obj)
            total += len(s)
        s2 = await bot.tree.sync()
        total += len(s2)
        await ctx.send(f"✅ {total} comandos sincronizados!")
    except Exception as e:
        await ctx.send(f"❌ Erro: {e}")

# ─── EVENTOS ─────────────────────────────────────────────────────

_synced = False

@bot.event
async def on_ready():
    global _synced
    print(f"Bot: {bot.user}")
    cmds_no_tree = len(bot.tree.get_commands())
    print(f"Comandos no tree: {cmds_no_tree}")

    # DB
    try:
        await init_db()
        await init_db_batalha()
        await init_db_hospital()
        await init_db_missoes()
        await init_conquistas()
        await init_db_eventos()
        await init_db_loja_sazonal()
        await init_db_guildas()
        await init_db_torneio()
        await init_db_dungeon_evento()
        await init_db_expedicao()
        print("DB OK!")
    except Exception as e:
        print(f"ERRO DB: {e}")

    if not _synced:
        try:
            guild_id = int(os.getenv("GUILD_ID","0"))
            if guild_id:
                guild_obj = discord.Object(id=guild_id)
                bot.tree.copy_global_to(guild=guild_obj)
                guild_synced = await bot.tree.sync(guild=guild_obj)
                print(f"Comandos no servidor: {len(guild_synced)}")
            else:
                global_synced = await bot.tree.sync()
                print(f"Comandos globais: {len(global_synced)}")
            _synced = True
        except Exception as e:
            print(f"ERRO sync: {e}")
    else:
        print("Sync ignorado — ja sincronizado anteriormente")

    print("Bot pronto!")

@bot.event
async def on_member_join(member: discord.Member):
    cargo = discord.utils.get(member.guild.roles, name="🌱 Recem-chegado")
    if cargo:
        try: await member.add_roles(cargo)
        except: pass

    try:
        canal_bv = (
            discord.utils.get(member.guild.text_channels, name="📌┃boas-vindas") or
            discord.utils.get(member.guild.text_channels, name="boas-vindas") or
            discord.utils.get(member.guild.text_channels, name="bem-vindo") or
            discord.utils.get(member.guild.text_channels, name="welcome")
        )
        if not canal_bv: return

        embed = discord.Embed(
            title=f"Bem-vindo a Villa Eldoria, {member.display_name}!",
            description=(
                "Villa Eldoria e um RPG textual de fantasia medieval!\n\n"
                "**O que te espera:**\n"
                "Combate com skills e equipamentos\n"
                "Dungeons com varios andares e chefes\n"
                "Torneios PvP, eventos e rankings\n"
                "Guildas com missoes semanais\n"
                "Roletas para desbloquear racas e classes raras\n\n"
                "**Para comecar:** Use `/criar_personagem`!\n"
                "Apos criar seu personagem voce recebera um canal privado com guia completo."
            ),
            color=0xE4AF3C
        )
        embed.set_footer(text="Villa Eldoria RPG — Sua jornada comeca agora!")
        await canal_bv.send(content=member.mention, embed=embed)
    except Exception as e:
        print(f"Erro boas-vindas: {e}")

# ─── MAIN ────────────────────────────────────────────────────────

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN","")
    if not token:
        try:
            with open("config.txt") as f:
                for l in f:
                    if l.startswith("DISCORD_TOKEN="):
                        token = l.split("=",1)[1].strip()
        except: pass
    if not token:
        print("ERRO: Token nao encontrado."); exit(1)
    bot.run(token)
