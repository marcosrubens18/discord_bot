# data_skills.py — Todas as skills do jogo

SKILLS = {
    # ══════════════════════════════════════════════════════════════════
    # GUERREIRO
    # ══════════════════════════════════════════════════════════════════
    "golpe_basico": {
        "nome": "Golpe Básico", "classe": "guerreiro", "nivel": 1,
        "raridade": "Comum", "emoji": "⚔️", "mana": 0, "dano_mult": 1.0,
        "efeito": None,
        "desc": "Um golpe direto e confiável. Sem custo de mana, sempre disponível.",
        "desc_batalha": "causou dano com um golpe direto",
    },
    "escudo_guerreiro": {
        "nome": "Postura de Escudo", "classe": "guerreiro", "nivel": 3,
        "raridade": "Comum", "emoji": "🛡️", "mana": 8, "dano_mult": 0,
        "efeito": "defesa",
        "desc": "Assume postura defensiva. Reduz 50% do dano recebido no próximo turno.",
        "desc_batalha": "assumiu postura defensiva (-50% dano recebido)",
    },
    "golpe_brutal": {
        "nome": "Golpe Brutal", "classe": "guerreiro", "nivel": 8,
        "raridade": "Incomum", "emoji": "💥", "mana": 18, "dano_mult": 2.2,
        "efeito": None,
        "desc": "Concentra toda a força em um golpe devastador. Dano dobrado, ignora parte da defesa.",
        "desc_batalha": "desferiu um golpe brutal",
    },
    "investida": {
        "nome": "Investida", "classe": "guerreiro", "nivel": 12,
        "raridade": "Incomum", "emoji": "🏃", "mana": 15, "dano_mult": 1.4,
        "efeito": "atordoar",
        "desc": "Corre em direção ao inimigo com força total. Causa dano e tem 30% de chance de atordoar.",
        "desc_batalha": "investiu contra o inimigo",
    },
    "grito_de_guerra": {
        "nome": "Grito de Guerra", "classe": "guerreiro", "nivel": 18,
        "raridade": "Raro", "emoji": "😤", "mana": 22, "dano_mult": 0,
        "efeito": "buff_ataque",
        "desc": "Um grito que aterroriza inimigos e inspira aliados. +35% de ataque por 3 turnos.",
        "desc_batalha": "soltou um grito de guerra (+35% ATK por 3 turnos)",
    },
    "lamina_giratoria": {
        "nome": "Lâmina Giratória", "classe": "guerreiro", "nivel": 22,
        "raridade": "Raro", "emoji": "🌀", "mana": 28, "dano_mult": 1.8,
        "efeito": None,
        "desc": "Gira a lâmina em alta velocidade causando dano múltiplo. Ataca 2 vezes.",
        "desc_batalha": "girou a lâmina causando 2 golpes",
        "hits": 2,
    },
    "escudo_de_aco": {
        "nome": "Escudo de Aço", "classe": "guerreiro", "nivel": 28,
        "raridade": "Epico", "emoji": "🪨", "mana": 35, "dano_mult": 0,
        "efeito": "escudo_total",
        "desc": "Cria um escudo impenetrável por 2 turnos. Absorve todo o dano recebido.",
        "desc_batalha": "criou um escudo de aço (2 turnos imune)",
    },
    "furia_berserker": {
        "nome": "Fúria Berserker", "classe": "guerreiro", "nivel": 35,
        "raridade": "Epico", "emoji": "🔥", "mana": 40, "dano_mult": 1.5,
        "efeito": "berserker",
        "desc": "ÉPICO: Entra em estado de fúria. +60% ATK, -20% DEF por 3 turnos. Regenera vida a cada golpe.",
        "desc_batalha": "entrou em fúria berserker (ÉPICO)",
    },

    # ══════════════════════════════════════════════════════════════════
    # MAGO
    # ══════════════════════════════════════════════════════════════════
    "bola_fogo": {
        "nome": "Bola de Fogo", "classe": "mago", "nivel": 1,
        "raridade": "Comum", "emoji": "🔥", "mana": 12, "dano_mult": 1.3,
        "efeito": "queimadura",
        "desc": "Lança uma esfera de fogo que explode no alvo. 25% de chance de queimadura (dano ao longo do tempo).",
        "desc_batalha": "lançou uma bola de fogo",
    },
    "missil_arcano": {
        "nome": "Míssil Arcano", "classe": "mago", "nivel": 3,
        "raridade": "Comum", "emoji": "✨", "mana": 8, "dano_mult": 1.1,
        "efeito": None,
        "desc": "Dispara 3 mísseis de energia arcana. Confiável e eficiente.",
        "desc_batalha": "disparou 3 mísseis arcanos",
        "hits": 3,
    },
    "escudo_arcano": {
        "nome": "Escudo Arcano", "classe": "mago", "nivel": 6,
        "raridade": "Comum", "emoji": "💜", "mana": 20, "dano_mult": 0,
        "efeito": "escudo",
        "desc": "Cria uma barreira mágica que absorve o próximo ataque completamente.",
        "desc_batalha": "criou um escudo arcano",
    },
    "raio_congelante": {
        "nome": "Raio Congelante", "classe": "mago", "nivel": 10,
        "raridade": "Incomum", "emoji": "❄️", "mana": 22, "dano_mult": 1.5,
        "efeito": "congelar",
        "desc": "Raio de gelo que causa dano alto e tem 40% de chance de congelar o inimigo (perde 1 turno).",
        "desc_batalha": "disparou um raio congelante",
    },
    "tempestade_relampagos": {
        "nome": "Tempestade de Relâmpagos", "classe": "mago", "nivel": 16,
        "raridade": "Raro", "emoji": "⚡", "mana": 35, "dano_mult": 1.7,
        "efeito": "paralisia",
        "desc": "Invoca uma tempestade elétrica. Alto dano e 35% de chance de paralisar o alvo.",
        "desc_batalha": "invocou uma tempestade de relâmpagos",
    },
    "meteor": {
        "nome": "Meteoro", "classe": "mago", "nivel": 24,
        "raridade": "Raro", "emoji": "☄️", "mana": 45, "dano_mult": 2.8,
        "efeito": None,
        "desc": "Chama um meteoro do céu. Dano massivo em área. Uma das magias mais poderosas.",
        "desc_batalha": "invocou um meteoro destruidor",
    },
    "campo_forca": {
        "nome": "Campo de Força", "classe": "mago", "nivel": 28,
        "raridade": "Epico", "emoji": "🔮", "mana": 30, "dano_mult": 0,
        "efeito": "reflexo",
        "desc": "ÉPICO: Cria um campo que reflete 40% de todo dano recebido de volta ao atacante por 2 turnos.",
        "desc_batalha": "ativou campo de força reflexivo (ÉPICO)",
    },
    "sobrecarga_arcana": {
        "nome": "Sobrecarga Arcana", "classe": "mago", "nivel": 35,
        "raridade": "Epico", "emoji": "🌟", "mana": 60, "dano_mult": 3.5,
        "efeito": "sobrecarga",
        "desc": "ÉPICO: Libera toda a energia arcana acumulada. Dano DEVASTADOR mas fica sem mana por 2 turnos.",
        "desc_batalha": "soltou uma sobrecarga arcana (ÉPICO)",
    },

    # ══════════════════════════════════════════════════════════════════
    # ARQUEIRO
    # ══════════════════════════════════════════════════════════════════
    "tiro_preciso": {
        "nome": "Tiro Preciso", "classe": "arqueiro", "nivel": 1,
        "raridade": "Comum", "emoji": "🎯", "mana": 0, "dano_mult": 1.0,
        "efeito": "critico_bonus",
        "desc": "Mira com cuidado antes de atirar. +40% de chance de acerto crítico.",
        "desc_batalha": "mirou e atirou com precisão",
    },
    "tiro_rapido": {
        "nome": "Tiro Rápido", "classe": "arqueiro", "nivel": 3,
        "raridade": "Comum", "emoji": "💨", "mana": 5, "dano_mult": 0.8,
        "efeito": None,
        "desc": "Dois disparos rápidos em sequência. Menor dano individual mas total compensado pela velocidade.",
        "desc_batalha": "disparou dois tiros rápidos",
        "hits": 2,
    },
    "esquiva": {
        "nome": "Esquiva", "classe": "arqueiro", "nivel": 5,
        "raridade": "Comum", "emoji": "💨", "mana": 15, "dano_mult": 0,
        "efeito": "esquiva",
        "desc": "Rola para o lado evitando completamente o próximo ataque recebido.",
        "desc_batalha": "preparou uma esquiva perfeita",
    },
    "flecha_venenosa": {
        "nome": "Flecha Venenosa", "classe": "arqueiro", "nivel": 10,
        "raridade": "Incomum", "emoji": "🟢", "mana": 18, "dano_mult": 1.1,
        "efeito": "veneno",
        "desc": "Flecha envenenada que causa dano imediato e veneno por 3 turnos (10% HP/turno).",
        "desc_batalha": "disparou uma flecha venenosa",
    },
    "tiro_multiplo": {
        "nome": "Tiro Múltiplo", "classe": "arqueiro", "nivel": 14,
        "raridade": "Incomum", "emoji": "🏹", "mana": 22, "dano_mult": 0.7,
        "efeito": None,
        "desc": "Atira 3 flechas simultaneamente em arco. Cada uma causa dano individual.",
        "desc_batalha": "disparou 3 flechas simultaneamente",
        "hits": 3,
    },
    "flecha_perfurante": {
        "nome": "Flecha Perfurante", "classe": "arqueiro", "nivel": 20,
        "raridade": "Raro", "emoji": "🔱", "mana": 30, "dano_mult": 2.0,
        "efeito": "ignorar_defesa",
        "desc": "Flecha de aço temperado que perfura armaduras. Ignora 60% da defesa do alvo.",
        "desc_batalha": "disparou uma flecha perfurante",
    },
    "chuva_flechas": {
        "nome": "Chuva de Flechas", "classe": "arqueiro", "nivel": 28,
        "raridade": "Raro", "emoji": "☄️", "mana": 40, "dano_mult": 0.5,
        "efeito": None,
        "desc": "Dispara 5 flechas em rápida sucessão. Impressionante no total.",
        "desc_batalha": "soltou uma chuva de flechas",
        "hits": 5,
    },
    "tiro_fantasma": {
        "nome": "Tiro Fantasma", "classe": "arqueiro", "nivel": 35,
        "raridade": "Epico", "emoji": "👻", "mana": 50, "dano_mult": 2.5,
        "efeito": "invisivel_pos",
        "desc": "ÉPICO: Atira uma flecha espectral que atravessa qualquer defesa. Ignora 100% da defesa e deixa o arqueiro invisível por 1 turno.",
        "desc_batalha": "disparou um tiro fantasma (ÉPICO)",
    },

    # ══════════════════════════════════════════════════════════════════
    # PALADINO
    # ══════════════════════════════════════════════════════════════════
    "golpe_sagrado": {
        "nome": "Golpe Sagrado", "classe": "paladino", "nivel": 1,
        "raridade": "Comum", "emoji": "⚡", "mana": 10, "dano_mult": 1.2,
        "efeito": None,
        "desc": "Combina força física com energia sagrada. Efetivo contra criaturas das trevas.",
        "desc_batalha": "desferiu um golpe sagrado",
    },
    "cura": {
        "nome": "Cura", "classe": "paladino", "nivel": 3,
        "raridade": "Comum", "emoji": "💚", "mana": 25, "dano_mult": 0,
        "efeito": "cura",
        "desc": "Canaliza energia sagrada para curar ferimentos. Restaura 35% do HP máximo.",
        "desc_batalha": "canalizou energia de cura",
    },
    "martelo_sagrado": {
        "nome": "Martelo Sagrado", "classe": "paladino", "nivel": 8,
        "raridade": "Incomum", "emoji": "🔨", "mana": 20, "dano_mult": 1.6,
        "efeito": "atordoar",
        "desc": "Golpe pesado com martelo abençoado. 40% de chance de atordoar o alvo.",
        "desc_batalha": "golpeou com o martelo sagrado",
    },
    "aura_sagrada": {
        "nome": "Aura Sagrada", "classe": "paladino", "nivel": 14,
        "raridade": "Incomum", "emoji": "🌟", "mana": 30, "dano_mult": 0,
        "efeito": "buff_all",
        "desc": "Emana uma aura divina. +25% ATK, +25% DEF e regenera 5% HP por turno por 3 turnos.",
        "desc_batalha": "ativou a aura sagrada",
    },
    "escudo_divino": {
        "nome": "Escudo Divino", "classe": "paladino", "nivel": 20,
        "raridade": "Raro", "emoji": "🛡️", "mana": 35, "dano_mult": 0,
        "efeito": "escudo_total",
        "desc": "Um escudo de luz pura que bloqueia completamente 2 ataques seguidos.",
        "desc_batalha": "invocou um escudo divino (2 bloqueios)",
    },
    "cura_em_area": {
        "nome": "Cura em Área", "classe": "paladino", "nivel": 25,
        "raridade": "Raro", "emoji": "💗", "mana": 45, "dano_mult": 0,
        "efeito": "cura_grande",
        "desc": "Cura poderosa que restaura 60% do HP máximo instantaneamente.",
        "desc_batalha": "canalizou uma cura poderosa",
    },
    "ressureicao": {
        "nome": "Ressurreição", "classe": "paladino", "nivel": 32,
        "raridade": "Epico", "emoji": "✝️", "mana": 80, "dano_mult": 0,
        "efeito": "ressurreicao",
        "desc": "ÉPICO: Se usado antes de morrer, restaura para 50% HP ao invés de morrer. Uso único por batalha.",
        "desc_batalha": "preparou um feitiço de ressurreição (ÉPICO)",
    },
    "juizo_final": {
        "nome": "Juízo Final", "classe": "paladino", "nivel": 35,
        "raridade": "Epico", "emoji": "☀️", "mana": 60, "dano_mult": 3.0,
        "efeito": "sagrado_bonus",
        "desc": "ÉPICO: Invoca o julgamento divino. Dano massivo sagrado que escala com o HP perdido.",
        "desc_batalha": "invocou o Juízo Final (ÉPICO)",
    },

    # ══════════════════════════════════════════════════════════════════
    # NECROMANTE
    # ══════════════════════════════════════════════════════════════════
    "drenar_vida": {
        "nome": "Drenar Vida", "classe": "necromante", "nivel": 1,
        "raridade": "Comum", "emoji": "🌑", "mana": 10, "dano_mult": 1.1,
        "efeito": "dreno",
        "desc": "Absorve a força vital do inimigo. Metade do dano causado é convertida em HP.",
        "desc_batalha": "drenou a vida do inimigo",
    },
    "maldicao": {
        "nome": "Maldição", "classe": "necromante", "nivel": 4,
        "raridade": "Comum", "emoji": "🩸", "mana": 12, "dano_mult": 0.6,
        "efeito": "veneno",
        "desc": "Amaldiçoa o alvo com energia sombria. Causa veneno por 4 turnos.",
        "desc_batalha": "lançou uma maldição sombria",
    },
    "invocar_esqueleto": {
        "nome": "Invocar Esqueleto", "classe": "necromante", "nivel": 8,
        "raridade": "Incomum", "emoji": "💀", "mana": 20, "dano_mult": 0.9,
        "efeito": None,
        "desc": "Invoca um guerreiro esqueleto que ataca por você. Dano baseado no seu ATK.",
        "desc_batalha": "invocou um esqueleto guerreiro",
    },
    "toque_necrotico": {
        "nome": "Toque Necrótico", "classe": "necromante", "nivel": 12,
        "raridade": "Incomum", "emoji": "☠️", "mana": 25, "dano_mult": 1.4,
        "efeito": "enfraquecer",
        "desc": "Toque que corrói o corpo do inimigo. Dano direto + -20% ATK do inimigo por 2 turnos.",
        "desc_batalha": "aplicou um toque necrótico",
    },
    "onda_sombria": {
        "nome": "Onda Sombria", "classe": "necromante", "nivel": 18,
        "raridade": "Raro", "emoji": "🌊", "mana": 35, "dano_mult": 1.8,
        "efeito": "drenar_mana",
        "desc": "Lança uma onda de energia negra. Dano alto e drena 30 de mana do oponente.",
        "desc_batalha": "lançou uma onda sombria",
    },
    "banshee": {
        "nome": "Grito da Banshee", "classe": "necromante", "nivel": 24,
        "raridade": "Raro", "emoji": "👻", "mana": 40, "dano_mult": 1.5,
        "efeito": "terror",
        "desc": "Evoca o grito mortal de uma banshee. Causa dano e aterroriza o alvo (-30% ATK por 2 turnos).",
        "desc_batalha": "evocou o grito da banshee",
    },
    "exercito_mortos": {
        "nome": "Exército dos Mortos", "classe": "necromante", "nivel": 30,
        "raridade": "Epico", "emoji": "💀", "mana": 55, "dano_mult": 2.2,
        "efeito": "multi_invocar",
        "desc": "ÉPICO: Invoca 3 mortos-vivos que atacam simultaneamente.",
        "desc_batalha": "invocou o exército dos mortos (ÉPICO)",
        "hits": 3,
    },
    "abraco_da_morte": {
        "nome": "Abraço da Morte", "classe": "necromante", "nivel": 35,
        "raridade": "Epico", "emoji": "💀", "mana": 65, "dano_mult": 1.0,
        "efeito": "instakill_chance",
        "desc": "ÉPICO: Dano direto + 20% de chance de morte instantânea. Drena todo o HP restante se ativar.",
        "desc_batalha": "usou o Abraço da Morte (ÉPICO)",
    },

    # ══════════════════════════════════════════════════════════════════
    # DRACOMANTE
    # ══════════════════════════════════════════════════════════════════
    "baforada": {
        "nome": "Baforada", "classe": "dracomante", "nivel": 1,
        "raridade": "Comum", "emoji": "🔥", "mana": 15, "dano_mult": 1.4,
        "efeito": "queimadura",
        "desc": "Sopra chamas dracônicas. Dano de fogo + queimadura por 2 turnos.",
        "desc_batalha": "soltou uma baforada de fogo",
    },
    "garra_dragao": {
        "nome": "Garra do Dragão", "classe": "dracomante", "nivel": 4,
        "raridade": "Comum", "emoji": "🐾", "mana": 10, "dano_mult": 1.2,
        "efeito": None,
        "desc": "Ataque físico poderoso com garras dracônicas. Dano alto e confiável.",
        "desc_batalha": "atacou com as garras do dragão",
    },
    "escamas_dragao": {
        "nome": "Escamas do Dragão", "classe": "dracomante", "nivel": 8,
        "raridade": "Incomum", "emoji": "🐉", "mana": 20, "dano_mult": 0,
        "efeito": "armadura",
        "desc": "Endurece as escamas dracônicas. -35% dano recebido por 3 turnos.",
        "desc_batalha": "endureceu as escamas (-35% dano recebido)",
    },
    "rugido_dragao": {
        "nome": "Rugido do Dragão", "classe": "dracomante", "nivel": 14,
        "raridade": "Incomum", "emoji": "😤", "mana": 18, "dano_mult": 0,
        "efeito": "terror",
        "desc": "Um rugido que aterroriza o inimigo. -40% ATK do inimigo por 2 turnos.",
        "desc_batalha": "soltou um rugido aterrorizante",
    },
    "cauda_dragao": {
        "nome": "Chicote de Cauda", "classe": "dracomante", "nivel": 18,
        "raridade": "Raro", "emoji": "🌪️", "mana": 25, "dano_mult": 1.6,
        "efeito": "atordoar",
        "desc": "Golpe poderoso com a cauda. 45% de chance de atordoar o inimigo por 1 turno.",
        "desc_batalha": "acertou com a cauda do dragão",
    },
    "voo_dragao": {
        "nome": "Voo do Dragão", "classe": "dracomante", "nivel": 22,
        "raridade": "Raro", "emoji": "🦅", "mana": 30, "dano_mult": 0,
        "efeito": "esquiva",
        "desc": "Levanta voo tornando-se intocável por 1 turno e prepara um ataque mergulhante poderoso.",
        "desc_batalha": "levantou voo (intocável por 1 turno)",
    },
    "forma_menor_dragao": {
        "nome": "Forma Menor do Dragão", "classe": "dracomante", "nivel": 28,
        "raridade": "Epico", "emoji": "🌋", "mana": 45, "dano_mult": 0,
        "efeito": "buff_all",
        "desc": "ÉPICO: Assume forma parcial de dragão. +40% ATK, +40% DEF, regenera HP por 3 turnos.",
        "desc_batalha": "assumiu a forma menor do dragão (ÉPICO)",
    },
    "dragao_eterno": {
        "nome": "Dragão Eterno", "classe": "dracomante", "nivel": 35,
        "raridade": "Epico", "emoji": "💎", "mana": 70, "dano_mult": 4.0,
        "efeito": "dragao_completo",
        "desc": "ÉPICO: Assume a forma completa de dragão. ATK quadruplicado por 1 turno.",
        "desc_batalha": "assumiu a forma completa do dragão (ÉPICO)",
    },

    # ══════════════════════════════════════════════════════════════════
    # ARCANO
    # ══════════════════════════════════════════════════════════════════
    "faisca_arcana": {
        "nome": "Faísca Arcana", "classe": "arcano", "nivel": 1,
        "raridade": "Comum", "emoji": "✨", "mana": 8, "dano_mult": 1.2,
        "efeito": None,
        "desc": "Uma descarga de energia arcana pura que ignora resistências elementais.",
        "desc_batalha": "disparou uma faísca arcana",
    },
    "distorcao": {
        "nome": "Distorção", "classe": "arcano", "nivel": 4,
        "raridade": "Comum", "emoji": "🌀", "mana": 15, "dano_mult": 0.8,
        "efeito": "confusao",
        "desc": "Distorce a percepção do inimigo. -50% de precisão por 2 turnos (50% de chance de errar).",
        "desc_batalha": "distorceu a percepção do inimigo",
    },
    "campo_forca_arcano": {
        "nome": "Campo de Força", "classe": "arcano", "nivel": 6,
        "raridade": "Incomum", "emoji": "🔮", "mana": 22, "dano_mult": 0,
        "efeito": "reflexo",
        "desc": "Campo mágico que reflete 30% de todo dano recebido por 2 turnos.",
        "desc_batalha": "criou um campo de força reflexivo",
    },
    "explosao_arcana": {
        "nome": "Explosão Arcana", "classe": "arcano", "nivel": 10,
        "raridade": "Incomum", "emoji": "💥", "mana": 28, "dano_mult": 2.0,
        "efeito": None,
        "desc": "Concentra energia arcana e libera em uma explosão devastadora. Dano massivo.",
        "desc_batalha": "causou uma explosão arcana",
    },
    "teletransporte": {
        "nome": "Teletransporte", "classe": "arcano", "nivel": 15,
        "raridade": "Raro", "emoji": "🌟", "mana": 25, "dano_mult": 1.5,
        "efeito": "esquiva",
        "desc": "Se teletransporta atrás do inimigo e ataca pela retaguarda. Ignora defesa + esquiva.",
        "desc_batalha": "se teletransportou e atacou pela retaguarda",
    },
    "drenar_magia": {
        "nome": "Drenar Magia", "classe": "arcano", "nivel": 20,
        "raridade": "Raro", "emoji": "💜", "mana": 0, "dano_mult": 1.0,
        "efeito": "drenar_mana",
        "desc": "Absorve a mana do inimigo. Drena 40 de mana do oponente e adiciona à sua.",
        "desc_batalha": "drenou a mana do inimigo",
    },
    "tempestade_arcana": {
        "nome": "Tempestade Arcana", "classe": "arcano", "nivel": 26,
        "raridade": "Epico", "emoji": "⭐", "mana": 55, "dano_mult": 2.5,
        "efeito": "multi_hit",
        "desc": "ÉPICO: Invoca uma tempestade de energia arcana. Acerta 4 vezes em rápida sucessão.",
        "desc_batalha": "invocou uma tempestade arcana (ÉPICO)",
        "hits": 4,
    },
    "singularidade": {
        "nome": "Singularidade", "classe": "arcano", "nivel": 35,
        "raridade": "Epico", "emoji": "🕳️", "mana": 75, "dano_mult": 5.0,
        "efeito": "singularidade",
        "desc": "ÉPICO: Cria um colapso dimensional. O dano mais alto do jogo, mas fica sem mana por 3 turnos.",
        "desc_batalha": "criou uma singularidade dimensional (ÉPICO)",
    },

    # ══════════════════════════════════════════════════════════════════
    # MAGIAS DE SUPORTE (qualquer classe pode usar via roleta)
    # ══════════════════════════════════════════════════════════════════
    "bencao_divina": {
        "nome": "Bênção Divina", "classe": "suporte", "nivel": 1,
        "raridade": "Incomum", "emoji": "🙏", "mana": 30, "dano_mult": 0,
        "efeito": "buff_all",
        "desc": "Bênção que aumenta todos os stats em 20% por 3 turnos. Qualquer classe pode usar.",
        "desc_batalha": "invocou uma bênção divina",
    },
    "cura_universal": {
        "nome": "Cura Universal", "classe": "suporte", "nivel": 1,
        "raridade": "Incomum", "emoji": "💗", "mana": 40, "dano_mult": 0,
        "efeito": "cura_grande",
        "desc": "Cura poderosa disponível para qualquer classe. Restaura 50% do HP máximo.",
        "desc_batalha": "usou uma cura universal",
    },
    "escudo_magico": {
        "nome": "Escudo Mágico", "classe": "suporte", "nivel": 1,
        "raridade": "Raro", "emoji": "🛡️", "mana": 35, "dano_mult": 0,
        "efeito": "escudo",
        "desc": "Escudo mágico universal. Absorve o próximo ataque independente da classe.",
        "desc_batalha": "criou um escudo mágico",
    },
    "frenesi": {
        "nome": "Frenesi", "classe": "suporte", "nivel": 1,
        "raridade": "Raro", "emoji": "🔥", "mana": 35, "dano_mult": 0,
        "efeito": "buff_ataque",
        "desc": "Entra em estado de frenesi. +50% de ataque por 2 turnos. Para qualquer classe.",
        "desc_batalha": "entrou em estado de frenesi",
    },
    "muralha": {
        "nome": "Muralha", "classe": "suporte", "nivel": 1,
        "raridade": "Epico", "emoji": "🪨", "mana": 50, "dano_mult": 0,
        "efeito": "escudo_total",
        "desc": "ÉPICO: Cria uma muralha impenetrável que bloqueia os próximos 3 ataques.",
        "desc_batalha": "criou uma muralha impenetrável (ÉPICO)",
    },
    "ressurreicao_suporte": {
        "nome": "Ressurreição", "classe": "suporte", "nivel": 1,
        "raridade": "Epico", "emoji": "✝️", "mana": 80, "dano_mult": 0,
        "efeito": "ressurreicao",
        "desc": "ÉPICO: Ressurreição universal. Se usar antes de morrer, volta com 50% HP. Uso único.",
        "desc_batalha": "preparou um feitiço de ressurreição (ÉPICO)",
    },
}

# ==================================================
# SKILLS_COMPLETAS (para compatibilidade com batalha.py)
# ==================================================

SKILLS_COMPLETAS = {
    "guerreiro": [
        {"id": "golpe_basico", "nome": "Golpe Basico", "nivel": 1, "emoji": "⚔️", "dano": 1.3, "mana": 0, "desc": "Ataque fisico direto.", "efeito": None},
        {"id": "escudo", "nome": "Postura de Escudo", "nivel": 3, "emoji": "🛡️", "dano": 0, "mana": 8, "desc": "Reduz 50% do dano recebido.", "efeito": "defesa"},
        {"id": "golpe_brutal", "nome": "Golpe Brutal", "nivel": 8, "emoji": "💥", "dano": 2.2, "mana": 18, "desc": "Golpe devastador.", "efeito": None},
        {"id": "investida", "nome": "Investida", "nivel": 12, "emoji": "🏃", "dano": 1.4, "mana": 15, "desc": "30% chance atordoar.", "efeito": "atordoar"},
        {"id": "grito_guerra", "nome": "Grito de Guerra", "nivel": 16, "emoji": "😤", "dano": 0, "mana": 22, "desc": "+35% de ataque por 3 turnos.", "efeito": "buff_ataque"},
        {"id": "lamina_girat", "nome": "Lamina Giratoria", "nivel": 20, "emoji": "🌀", "dano": 1.8, "mana": 28, "desc": "2 golpes consecutivos.", "efeito": "hits2"},
        {"id": "escudo_aco", "nome": "Escudo de Aco", "nivel": 28, "emoji": "🪨", "dano": 0, "mana": 35, "desc": "Escudo impenetravel por 2 turnos.", "efeito": "escudo_total"},
        {"id": "furia", "nome": "Furia Berserker", "nivel": 35, "emoji": "🔥", "dano": 2.5, "mana": 40, "desc": "+60% ATK, regenera vida.", "efeito": "berserker"},
        {"id": "golpe_final", "nome": "Golpe Final", "nivel": 45, "emoji": "💢", "dano": 3.5, "mana": 50, "desc": "Ignora 50% defesa.", "efeito": None},
        {"id": "lendario_atk", "nome": "Golpe Lendario", "nivel": 70, "emoji": "⚡", "dano": 5.0, "mana": 80, "desc": "Golpe lendario.", "efeito": None},
    ],
    "arqueiro": [
        {"id": "tiro_preciso", "nome": "Tiro Preciso", "nivel": 1, "emoji": "🎯", "dano": 1.3, "mana": 0, "desc": "+40% critico.", "efeito": "critico_bonus"},
        {"id": "tiro_rapido", "nome": "Tiro Rapido", "nivel": 3, "emoji": "💨", "dano": 0.8, "mana": 5, "desc": "2 tiros rapidos.", "efeito": "hits2"},
        {"id": "esquiva", "nome": "Esquiva", "nivel": 5, "emoji": "💨", "dano": 0, "mana": 15, "desc": "Evita proximo ataque.", "efeito": "esquiva"},
        {"id": "flecha_veneno", "nome": "Flecha Venenosa", "nivel": 10, "emoji": "🟢", "dano": 1.1, "mana": 18, "desc": "Veneno 3 turnos.", "efeito": "veneno"},
        {"id": "tiro_multiplo", "nome": "Tiro Multiplo", "nivel": 14, "emoji": "🏹", "dano": 0.7, "mana": 22, "desc": "3 flechas.", "efeito": "hits3"},
        {"id": "flecha_perfurante", "nome": "Flecha Perfurante", "nivel": 20, "emoji": "🔱", "dano": 2.0, "mana": 30, "desc": "Ignora 60% defesa.", "efeito": "ignorar_defesa"},
        {"id": "chuva_flechas", "nome": "Chuva de Flechas", "nivel": 28, "emoji": "☄️", "dano": 0.5, "mana": 40, "desc": "5 flechas.", "efeito": "hits5"},
        {"id": "tiro_fantasma", "nome": "Tiro Fantasma", "nivel": 35, "emoji": "👻", "dano": 2.5, "mana": 50, "desc": "Ignora 100% defesa.", "efeito": "ignorar_defesa"},
    ],
    "mago": [
        {"id": "bola_fogo", "nome": "Bola de Fogo", "nivel": 1, "emoji": "🔥", "dano": 1.3, "mana": 12, "desc": "25% chance queimadura.", "efeito": "queimadura"},
        {"id": "missil_arcano", "nome": "Missil Arcano", "nivel": 3, "emoji": "✨", "dano": 1.1, "mana": 6, "desc": "3 misseis.", "efeito": "hits3"},
        {"id": "escudo_arcano", "nome": "Escudo Arcano", "nivel": 6, "emoji": "💜", "dano": 0, "mana": 20, "desc": "Absorve proximo ataque.", "efeito": "escudo"},
        {"id": "raio_congelante", "nome": "Raio Congelante", "nivel": 10, "emoji": "❄️", "dano": 1.5, "mana": 22, "desc": "40% chance congelar.", "efeito": "congelar"},
        {"id": "tempestade", "nome": "Tempestade", "nivel": 16, "emoji": "⚡", "dano": 1.7, "mana": 35, "desc": "35% chance paralisar.", "efeito": "paralisia"},
        {"id": "meteor", "nome": "Meteoro", "nivel": 24, "emoji": "☄️", "dano": 2.8, "mana": 45, "desc": "Dano massivo.", "efeito": None},
        {"id": "campo_forca", "nome": "Campo de Forca", "nivel": 28, "emoji": "🔮", "dano": 0, "mana": 30, "desc": "Reflete 40% do dano.", "efeito": "reflexo"},
        {"id": "sobrecarga", "nome": "Sobrecarga", "nivel": 35, "emoji": "🌟", "dano": 3.5, "mana": 60, "desc": "Dano devastador.", "efeito": None},
        {"id": "chuva_meteoros", "nome": "Chuva de Meteoros", "nivel": 50, "emoji": "💥", "dano": 4.0, "mana": 70, "desc": "Multiplos meteoros.", "efeito": "hits3"},
        {"id": "singularidade_m", "nome": "Singularidade", "nivel": 70, "emoji": "🌌", "dano": 7.0, "mana": 100, "desc": "Dano absoluto.", "efeito": None},
    ],
    "paladino": [
        {"id": "golpe_sagrado", "nome": "Golpe Sagrado", "nivel": 1, "emoji": "⚡", "dano": 1.2, "mana": 10, "desc": "Ataque sagrado.", "efeito": None},
        {"id": "cura", "nome": "Cura", "nivel": 3, "emoji": "💚", "dano": 0, "mana": 25, "desc": "Cura 35% HP.", "efeito": "cura"},
        {"id": "martelo_sagrado", "nome": "Martelo Sagrado", "nivel": 8, "emoji": "🔨", "dano": 1.6, "mana": 20, "desc": "40% atordoar.", "efeito": "atordoar"},
        {"id": "aura_sagrada", "nome": "Aura Sagrada", "nivel": 14, "emoji": "🌟", "dano": 0, "mana": 30, "desc": "+25% ATK/DEF, regen 5% HP.", "efeito": "buff_all"},
        {"id": "escudo_divino", "nome": "Escudo Divino", "nivel": 20, "emoji": "🛡️", "dano": 0, "mana": 35, "desc": "Bloqueia 2 ataques.", "efeito": "escudo_total"},
        {"id": "cura_area", "nome": "Cura em Area", "nivel": 25, "emoji": "💗", "dano": 0, "mana": 45, "desc": "Cura 60% HP.", "efeito": "cura_grande"},
        {"id": "ressureicao", "nome": "Ressurreição", "nivel": 32, "emoji": "✝️", "dano": 0, "mana": 40, "desc": "Revive com 60% HP.", "efeito": "ressurreicao"},
        {"id": "juizo_final", "nome": "Juizo Final", "nivel": 35, "emoji": "☀️", "dano": 3.0, "mana": 60, "desc": "Escala com HP perdido.", "efeito": "sagrado_bonus"},
    ],
    "necromante": [
        {"id": "drenar_vida", "nome": "Drenar Vida", "nivel": 1, "emoji": "🌑", "dano": 1.1, "mana": 10, "desc": "Drena 50% do dano.", "efeito": "dreno"},
        {"id": "maldicao", "nome": "Maldicao", "nivel": 4, "emoji": "🩸", "dano": 0.8, "mana": 8, "desc": "Veneno 4 turnos.", "efeito": "veneno"},
        {"id": "invocar_morto", "nome": "Invocar Morto", "nivel": 8, "emoji": "💀", "dano": 0.9, "mana": 20, "desc": "Invoca esqueleto.", "efeito": None},
        {"id": "toque_necrotico", "nome": "Toque Necrotico", "nivel": 12, "emoji": "☠️", "dano": 1.4, "mana": 25, "desc": "-20% ATK inimigo.", "efeito": "enfraquecer"},
        {"id": "onda_sombria", "nome": "Onda Sombria", "nivel": 18, "emoji": "🌊", "dano": 1.8, "mana": 35, "desc": "Drena 30 mana.", "efeito": "drenar_mana"},
        {"id": "banshee", "nome": "Grito da Banshee", "nivel": 24, "emoji": "👻", "dano": 1.5, "mana": 40, "desc": "-30% ATK inimigo.", "efeito": "terror"},
        {"id": "exercito_mortos", "nome": "Exercito Mortos", "nivel": 30, "emoji": "💀", "dano": 2.2, "mana": 55, "desc": "3 ataques.", "efeito": "hits3"},
        {"id": "abraco_morte", "nome": "Abraço da Morte", "nivel": 35, "emoji": "💀", "dano": 1.0, "mana": 65, "desc": "20% instakill.", "efeito": "instakill_chance"},
    ],
    "dracomante": [
        {"id": "baforada", "nome": "Baforada", "nivel": 1, "emoji": "🔥", "dano": 1.6, "mana": 12, "desc": "Queimadura 2 turnos.", "efeito": "queimadura"},
        {"id": "garra_dragao", "nome": "Garra do Dragão", "nivel": 4, "emoji": "🐾", "dano": 1.2, "mana": 10, "desc": "Ataque fisico.", "efeito": None},
        {"id": "escamas_dragao", "nome": "Escamas do Dragão", "nivel": 8, "emoji": "🐉", "dano": 0, "mana": 20, "desc": "-35% dano 3 turnos.", "efeito": "armadura"},
        {"id": "rugido_dragao", "nome": "Rugido do Dragão", "nivel": 14, "emoji": "😤", "dano": 0, "mana": 18, "desc": "-40% ATK inimigo.", "efeito": "terror"},
        {"id": "cauda_dragao", "nome": "Chicote de Cauda", "nivel": 18, "emoji": "🌪️", "dano": 1.6, "mana": 25, "desc": "45% atordoar.", "efeito": "atordoar"},
        {"id": "voo_dragao", "nome": "Voo do Dragão", "nivel": 22, "emoji": "🦅", "dano": 0, "mana": 30, "desc": "Esquiva por 1 turno.", "efeito": "esquiva"},
        {"id": "forma_menor", "nome": "Forma Menor do Dragão", "nivel": 28, "emoji": "🌋", "dano": 0, "mana": 45, "desc": "+40% ATK/DEF, regen.", "efeito": "buff_all"},
        {"id": "dragao_eterno", "nome": "Dragão Eterno", "nivel": 35, "emoji": "💎", "dano": 4.0, "mana": 70, "desc": "Forma completa.", "efeito": None},
        {"id": "chamas_ancestrais", "nome": "Chamas Ancestrais", "nivel": 45, "emoji": "🌋", "dano": 3.0, "mana": 45, "desc": "Queimadura garantida 3 turnos.", "efeito": "queimadura"},
        {"id": "coracao_dragao", "nome": "Coracao de Dragao", "nivel": 60, "emoji": "❤️‍🔥", "dano": 0, "mana": 50, "desc": "+50% ATK/DEF, regen 8% HP 4 turnos.", "efeito": "buff_all"},
    ],
    "arcano": [
        {"id": "faisca_arcana", "nome": "Faisca Arcana", "nivel": 1, "emoji": "✨", "dano": 1.2, "mana": 8, "desc": "Energia arcana.", "efeito": None},
        {"id": "distorcao", "nome": "Distorcao", "nivel": 4, "emoji": "🌀", "dano": 1.1, "mana": 12, "desc": "-50% precisao.", "efeito": "confusao"},
        {"id": "campo_forca_arcano", "nome": "Campo de Forca", "nivel": 6, "emoji": "🔮", "dano": 0, "mana": 22, "desc": "Reflete 30% dano.", "efeito": "reflexo"},
        {"id": "explosao_arcana", "nome": "Explosao Arcana", "nivel": 10, "emoji": "💥", "dano": 2.0, "mana": 28, "desc": "Dano massivo.", "efeito": None},
        {"id": "teletransporte", "nome": "Teletransporte", "nivel": 15, "emoji": "🌟", "dano": 1.5, "mana": 25, "desc": "Ignora defesa.", "efeito": "ignorar_defesa"},
        {"id": "drenar_magia", "nome": "Drenar Magia", "nivel": 20, "emoji": "💜", "dano": 1.0, "mana": 0, "desc": "Drena 40 mana.", "efeito": "drenar_mana"},
        {"id": "tempestade_arcana", "nome": "Tempestade Arcana", "nivel": 26, "emoji": "⭐", "dano": 2.5, "mana": 55, "desc": "4 ataques.", "efeito": "hits4"},
        {"id": "singularidade", "nome": "Singularidade", "nivel": 35, "emoji": "🕳️", "dano": 4.5, "mana": 60, "desc": "Perde 30% da mana restante.", "efeito": "singularidade_v2"},
    ],
}

# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

def get_skill_by_id(skill_id):
    """Retorna uma skill pelo ID"""
    for classe, skills in SKILLS_COMPLETAS.items():
        for skill in skills:
            if skill["id"] == skill_id:
                return {**skill, "classe_origem": classe}
    return None


def get_skills_classe(classe_id):
    """Retorna todas as skills de uma classe"""
    return SKILLS_COMPLETAS.get(classe_id, [])