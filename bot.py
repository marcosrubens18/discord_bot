# Adicione no final do arquivo systems/missoes.py

async def iniciar_agendador_reset(bot):
    """Inicia o agendador de reset diário das missões"""
    import asyncio
    from datetime import datetime
    
    async def reset_loop():
        while True:
            agora = datetime.now()
            # Calcula próximo reset (meia-noite)
            meia_noite = datetime(agora.year, agora.month, agora.day + 1, 0, 0, 0)
            segundos_ate_reset = (meia_noite - agora).total_seconds()
            
            await asyncio.sleep(segundos_ate_reset)
            await resetar_missoes_diarias()
            print("[MISSOES] Reset diário executado!")
    
    # Inicia o loop em background
    asyncio.create_task(reset_loop())
