from datetime import date, timedelta

# National holidays 2024-2027.
# Moving holidays calculated from Easter: 2024-03-31, 2025-04-20, 2026-04-05, 2027-03-28.
_HOLIDAYS: frozenset[date] = frozenset([
    # 2024
    date(2024, 1, 1),   # Confraternização Universal
    date(2024, 2, 12),  # Carnaval (segunda)
    date(2024, 2, 13),  # Carnaval (terça)
    date(2024, 3, 29),  # Sexta-Feira Santa
    date(2024, 4, 21),  # Tiradentes
    date(2024, 5, 1),   # Dia do Trabalhador
    date(2024, 5, 30),  # Corpus Christi
    date(2024, 9, 7),   # Independência do Brasil
    date(2024, 10, 12), # Nossa Senhora Aparecida
    date(2024, 11, 2),  # Finados
    date(2024, 11, 15), # Proclamação da República
    date(2024, 11, 20), # Dia da Consciência Negra
    date(2024, 12, 25), # Natal
    # 2025
    date(2025, 1, 1),
    date(2025, 3, 3),   # Carnaval (segunda)
    date(2025, 3, 4),   # Carnaval (terça)
    date(2025, 4, 18),  # Sexta-Feira Santa
    date(2025, 4, 21),
    date(2025, 5, 1),
    date(2025, 6, 19),  # Corpus Christi
    date(2025, 9, 7),
    date(2025, 10, 12),
    date(2025, 11, 2),
    date(2025, 11, 15),
    date(2025, 11, 20),
    date(2025, 12, 25),
    # 2026
    date(2026, 1, 1),
    date(2026, 2, 16),  # Carnaval (segunda)
    date(2026, 2, 17),  # Carnaval (terça)
    date(2026, 4, 3),   # Sexta-Feira Santa
    date(2026, 4, 21),
    date(2026, 5, 1),
    date(2026, 6, 4),   # Corpus Christi
    date(2026, 9, 7),
    date(2026, 10, 12),
    date(2026, 11, 2),
    date(2026, 11, 15),
    date(2026, 11, 20),
    date(2026, 12, 25),
    # 2027
    date(2027, 1, 1),
    date(2027, 2, 8),   # Carnaval (segunda)
    date(2027, 2, 9),   # Carnaval (terça)
    date(2027, 3, 26),  # Sexta-Feira Santa
    date(2027, 4, 21),
    date(2027, 5, 1),
    date(2027, 5, 27),  # Corpus Christi
    date(2027, 9, 7),
    date(2027, 10, 12),
    date(2027, 11, 2),
    date(2027, 11, 15),
    date(2027, 11, 20),
    date(2027, 12, 25),
])


def is_business_day(d: date) -> bool:
    return d.weekday() < 5 and d not in _HOLIDAYS


def count_business_days(start: date, end: date) -> int:
    """Number of business days in (start, end], i.e., strictly after start through end inclusive."""
    count = 0
    d = start + timedelta(days=1)
    while d <= end:
        if is_business_day(d):
            count += 1
        d += timedelta(days=1)
    return count
