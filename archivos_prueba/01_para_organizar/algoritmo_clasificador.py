"""Módulo de clasificación automatizada."""

def clasificar_dato(valor: float) -> str:
    if valor > 100.0:
        return "Alto"
    elif valor > 50.0:
        return "Medio"
    return "Bajo"

if __name__ == "__main__":
    print(clasificar_dato(75.5))
