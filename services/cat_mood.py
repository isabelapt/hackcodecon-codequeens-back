"""Pure-function cat mood calculation shared by both sync and async code paths."""

import random

MOOD_THRESHOLDS = [
    (75, "happy"),
    (50, "neutral"),
    (25, "grumpy"),
]


def compute_cat_state(
    total: int, done: int, desistiu: int, adiadas: int
) -> tuple[str, float, float]:
    """Derive mood, happiness and hunger from task statistics.

    Returns:
        (mood, happiness, hunger)
    """
    if total == 0:
        happiness = 70.0
        hunger = 30.0
    else:
        happiness = min(100.0, (done / total) * 120)
        hunger = min(100.0, ((desistiu + adiadas * 0.3) / max(total, 1)) * 100)

    mood = "monster"
    for threshold, name in MOOD_THRESHOLDS:
        if happiness >= threshold:
            mood = name
            break

    return mood, round(happiness, 1), round(hunger, 1)


DESTRUCTION_MESSAGES = [
    "O gatinho deletou um comentário do seu código.",
    "O gatinho trocou todos os seus 'true' por 'false'.",
    "O gatinho adicionou um `time.sleep(5)` em produção.",
    "O gatinho renomeou sua variável principal para 'coisaNome2'.",
    "O gatinho commitou com a mensagem 'asdfghjkl'.",
    "O gatinho abriu 47 abas do Stack Overflow e não fechou nenhuma.",
]


def maybe_destruction_event(
    current_destruction_level: int, mood: str
) -> tuple[bool, int, str | None]:
    """Determine whether a destruction event should fire.

    Returns:
        (should_fire, new_level, message_or_None)
    """
    if mood != "monster" or random.random() >= 0.3:
        return False, current_destruction_level, None
    new_level = min(5, current_destruction_level + 1)
    msg = random.choice(DESTRUCTION_MESSAGES)
    return True, new_level, f"💥 DESTRUIÇÃO NÍVEL {new_level}: {msg}"
