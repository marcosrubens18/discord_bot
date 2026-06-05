# views/batalha_view.py — Views de batalha

import discord
from data.skills import get_skill_by_id


class BatalhaView(discord.ui.View):
    def __init__(self, user_id, skills, pocoes, nivel=1):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.acao = None
        self.acao_feita = False
        self._pocoes = list(pocoes) if pocoes else []
        self._skills = list(skills) if skills else []

        if nivel <= 9:
            max_slots = 2
        elif nivel <= 19:
            max_slots = 3
        else:
            max_slots = 4

        for i, sk in enumerate(skills[:max_slots]):
            mana_txt = f" ({sk.get('mana', 0)}💙)" if sk.get("mana", 0) > 0 else ""
            btn = discord.ui.Button(
                label=f"{sk['emoji']} {sk['nome']}{mana_txt}",
                style=discord.ButtonStyle.primary,
                row=i // 2,
                custom_id=f"skill_{i}"
            )
            btn.callback = self._fazer_skill(i)
            self.add_item(btn)

        atk_btn = discord.ui.Button(
            label="⚔️ Ataque Básico",
            style=discord.ButtonStyle.secondary,
            row=2,
            custom_id="atk_basico"
        )
        atk_btn.callback = self._atk_basico
        self.add_item(atk_btn)

        def_btn = discord.ui.Button(
            label="🛡️ Defesa",
            style=discord.ButtonStyle.secondary,
            row=2,
            custom_id="defesa_basica"
        )
        def_btn.callback = self._defesa_basica
        self.add_item(def_btn)

        mochila_btn = discord.ui.Button(
            label=f"🎒 Mochila ({len(self._pocoes)})" if self._pocoes else "🎒 Mochila (vazia)",
            style=discord.ButtonStyle.secondary,
            disabled=len(self._pocoes) == 0,
            row=3,
            custom_id="mochila"
        )
        mochila_btn.callback = self._abrir_mochila
        self.add_item(mochila_btn)

        fugir_btn = discord.ui.Button(
            label="🏃 Fugir", style=discord.ButtonStyle.danger,
            row=3, custom_id="fugir"
        )
        fugir_btn.callback = self._fugir
        self.add_item(fugir_btn)

    async def on_timeout(self):
        self.acao = ("timeout", None)
        self.stop()

    def _fazer_skill(self, idx):
        async def callback(inter: discord.Interaction):
            try:
                await inter.response.defer()
            except:
                pass
            if inter.user.id != self.user_id or self.acao_feita:
                return
            self.acao_feita = True
            self.acao = ("skill", idx)
            self.stop()
        return callback

    async def _abrir_mochila(self, inter: discord.Interaction):
        if inter.user.id != self.user_id or self.acao_feita:
            try:
                await inter.response.defer()
            except:
                pass
            return
        if not self._pocoes:
            try:
                await inter.response.send_message("Mochila vazia!", ephemeral=True)
            except:
                pass
            return
        opcoes = [
            discord.SelectOption(
                label=f"{p['emoji']} {p['nome']} (x{p['quantidade']})",
                value=p["item_id"]
            ) for p in self._pocoes[:10]
        ]
        sel = discord.ui.Select(placeholder="Qual poção usar?", options=opcoes)
        parent = self

        async def usar(inter2: discord.Interaction):
            try:
                await inter2.response.defer()
            except:
                pass
            if inter2.user.id != parent.user_id or parent.acao_feita:
                return
            parent.acao_feita = True
            parent.acao = ("pocao", inter2.data["values"][0])
            parent.stop()

        sel.callback = usar
        v = discord.ui.View(timeout=20)
        v.add_item(sel)
        try:
            await inter.response.send_message("Escolha a poção:", view=v, ephemeral=True)
        except:
            pass

    async def _atk_basico(self, inter: discord.Interaction):
        try:
            await inter.response.defer()
        except:
            pass
        if inter.user.id != self.user_id or self.acao_feita:
            return
        self.acao_feita = True
        self.acao = ("atk_basico", None)
        self.stop()

    async def _defesa_basica(self, inter: discord.Interaction):
        try:
            await inter.response.defer()
        except:
            pass
        if inter.user.id != self.user_id or self.acao_feita:
            return
        self.acao_feita = True
        self.acao = ("defesa_basica", None)
        self.stop()

    async def _fugir(self, inter: discord.Interaction):
        try:
            await inter.response.defer()
        except:
            pass
        if inter.user.id != self.user_id or self.acao_feita:
            return
        self.acao_feita = True
        self.acao = ("fugir", None)
        self.stop()


class DungeonBatalhaView(discord.ui.View):
    def __init__(self, user_id, skills, pocoes):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.acao = None
        self.acao_feita = False
        self._pocoes = list(pocoes) if pocoes else []
        self._skills = list(skills) if skills else []

        for i, sk in enumerate(skills[:4]):
            mana_txt = f"({sk.get('mana', 0)}💙)" if sk.get("mana", 0) > 0 else ""
            btn = discord.ui.Button(
                label=f"{sk['emoji']} {sk['nome']} {mana_txt}".strip(),
                style=discord.ButtonStyle.primary,
                row=0 if i < 2 else 1,
                custom_id=f"sk_{i}"
            )
            btn.callback = self._make_skill_callback(i)
            self.add_item(btn)

        atk_btn = discord.ui.Button(
            label="⚔️ Ataque Básico",
            style=discord.ButtonStyle.secondary,
            row=2, custom_id="atk_basico"
        )
        atk_btn.callback = self._atk_basico
        self.add_item(atk_btn)

        def_btn = discord.ui.Button(
            label="🛡️ Defesa",
            style=discord.ButtonStyle.secondary,
            row=2, custom_id="defesa_basica"
        )
        def_btn.callback = self._defesa_basica
        self.add_item(def_btn)

        mochila_btn = discord.ui.Button(
            label=f"🎒 Mochila ({len(self._pocoes)})" if self._pocoes else "🎒 Mochila (vazia)",
            style=discord.ButtonStyle.secondary,
            disabled=not self._pocoes,
            row=3, custom_id="mochila"
        )
        mochila_btn.callback = self._abrir_mochila
        self.add_item(mochila_btn)

        fugir_btn = discord.ui.Button(
            label="🏃 Fugir da Dungeon",
            style=discord.ButtonStyle.danger,
            row=3, custom_id="fugir"
        )
        fugir_btn.callback = self._fugir
        self.add_item(fugir_btn)

    def _make_skill_callback(self, idx):
        async def callback(inter: discord.Interaction):
            try:
                await inter.response.defer()
            except:
                pass
            if inter.user.id != self.user_id or self.acao_feita:
                return
            self.acao_feita = True
            self.acao = ("skill", idx)
            self.stop()
        return callback

    async def _abrir_mochila(self, inter: discord.Interaction):
        if inter.user.id != self.user_id or self.acao_feita:
            try:
                await inter.response.defer()
            except:
                pass
            return
        if not self._pocoes:
            try:
                await inter.response.send_message("Mochila vazia!", ephemeral=True)
            except:
                pass
            return
        
        opcoes = [
            discord.SelectOption(
                label=f"{p['emoji']} {p['nome']} (x{p['quantidade']})",
                value=p["item_id"]
            ) for p in self._pocoes[:10]
        ]
        sel = discord.ui.Select(placeholder="Usar poção...", options=opcoes)
        
        async def usar(inter2: discord.Interaction):
            try:
                await inter2.response.defer()
            except:
                pass
            if inter2.user.id != self.user_id or self.acao_feita:
                return
            self.acao_feita = True
            self.acao = ("pocao", sel.values[0])
            self.stop()
        
        sel.callback = usar
        v = discord.ui.View(timeout=20)
        v.add_item(sel)
        try:
            await inter.response.send_message("🎒 Escolha uma poção:", view=v, ephemeral=True)
        except:
            pass

    async def _atk_basico(self, inter: discord.Interaction):
        try:
            await inter.response.defer()
        except:
            pass
        if inter.user.id != self.user_id or self.acao_feita:
            return
        self.acao_feita = True
        self.acao = ("atk_basico", None)
        self.stop()

    async def _defesa_basica(self, inter: discord.Interaction):
        try:
            await inter.response.defer()
        except:
            pass
        if inter.user.id != self.user_id or self.acao_feita:
            return
        self.acao_feita = True
        self.acao = ("defesa_basica", None)
        self.stop()

    async def _fugir(self, inter: discord.Interaction):
        try:
            await inter.response.defer()
        except:
            pass
        if inter.user.id != self.user_id or self.acao_feita:
            return
        self.acao_feita = True
        self.acao = ("fugir", None)
        self.stop()


class EscolherArenaView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.arena = None
        from data.constantes import ARENAS
        opcoes = [
            discord.SelectOption(
                label=f"{a['emoji']} {a['nome']}",
                value=a["id"],
                description=f"Bonus: {a['bonus']}",
                default=False
            ) for a in ARENAS
        ]
        sel = discord.ui.Select(
            placeholder="🏟️ Escolha uma arena...",
            options=opcoes,
            min_values=1,
            max_values=1
        )
        sel.callback = self._escolher
        self.add_item(sel)

    async def _escolher(self, inter: discord.Interaction):
        if inter.user.id != self.user_id:
            await inter.response.defer()
            return
        from data.constantes import ARENAS
        self.arena = next(a for a in ARENAS if a["id"] == inter.data["values"][0])
        await inter.response.edit_message(
            embed=discord.Embed(
                title=f"{self.arena['emoji']} Arena: {self.arena['nome']}",
                description=f"Bonus: **{self.arena['bonus']}**",
                color=self.arena["cor"]
            ),
            view=None
        )
        self.stop()

    async def on_timeout(self):
        if not self.arena:
            from data.constantes import ARENAS
            import random
            self.arena = random.choice(ARENAS)
        self.stop()


class AceitarDueloView(discord.ui.View):
    def __init__(self, desafiante_id, desafiado_id):
        super().__init__(timeout=300)
        self.desafiante_id = desafiante_id
        self.desafiado_id = desafiado_id
        self.resposta = None

    @discord.ui.button(label="✅ Aceitar", style=discord.ButtonStyle.success)
    async def aceitar(self, inter: discord.Interaction, b):
        if inter.user.id != self.desafiado_id:
            await inter.response.send_message("Não é você que foi desafiado!", ephemeral=True)
            return
        self.resposta = True
        await inter.response.defer()
        self.stop()

    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger)
    async def recusar(self, inter: discord.Interaction, b):
        if inter.user.id not in (self.desafiado_id, self.desafiante_id):
            await inter.response.send_message("Não é sua batalha!", ephemeral=True)
            return
        self.resposta = False
        await inter.response.defer()
        self.stop()