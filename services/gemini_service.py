import os
import google.generativeai as genai
from datetime import datetime, timedelta
import random

FALLBACK_EXCUSES = [
    "Mercúrio está retrógrado e isso afeta diretamente a sua motivação.",
    "O servidor de produtividade global está em manutenção não programada.",
    "As estrelas não estão alinhadas para essa tarefa hoje.",
    "Um estudo da Universidade de Nárnia comprovou que fazer isso agora reduz o QI em 12 pontos.",
    "Você precisa de mais 72 horas para processar o conceito emocionalmente.",
    "A vibração cósmica da semana não é compatível com essa tarefa.",
    "Seis dos sete chakras bloqueados detectados. Reagendamento recomendado.",
    "O algoritmo de procrastinação identificou sobreposição com a sua hora de lanche.",
    "Cientistas descobriram que segunda-feira é 40% mais produtiva. Aguarde.",
    "Você foi selecionado para o Programa Nacional de Descanso Estratégico.",
    "A matriz de decisão quântica sugere: não agora.",
    "Índice de Compatibilidade com Produtividade: 3%. Tente novamente em 48h.",
]

POSTPONE_HOURS = [24, 48, 72, 168]  # 1d, 2d, 3d, 1 semana


def _build_prompt(task_title: str, scheduled_at: str) -> str:
    return f"""Você é um assistente de procrastinação especializado em inventar desculpas criativas, absurdas e engraçadas para desenvolvedores adiarem tarefas.

Tarefa: "{task_title}"
Agendada para: {scheduled_at}

Crie UMA desculpa curta (máximo 2 frases) para justificar o adiamento desta tarefa.
A desculpa deve ser absurda, cômica e levemente conspiratória.
Pode envolver: astrologia, física quântica, lendas urbanas dev, bugs cósmicos, ou pseudociência.
Responda APENAS com a desculpa, sem introdução ou explicação.
Responda em português brasileiro."""


async def get_procrastination_excuse(
    task_title: str,
    scheduled_at: datetime = None,
) -> dict:
    scheduled_str = scheduled_at.strftime("%d/%m/%Y %H:%M") if scheduled_at else "agora"
    suggested_hours = random.choice(POSTPONE_HOURS)
    new_date = (scheduled_at or datetime.utcnow()) + timedelta(hours=suggested_hours)

    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(_build_prompt(task_title, scheduled_str))
        excuse = response.text.strip()
    except Exception:
        excuse = random.choice(FALLBACK_EXCUSES)

    return {
        "excuse": excuse,
        "suggested_postpone_hours": suggested_hours,
        "suggested_new_date": new_date.isoformat(),
        "confidence": random.randint(87, 99),
    }
