"""
Sistema de rampas de caracteres optimizadas para lectura de forma.
Prioriza contraste visual y bloques reconocibles sobre gradientes suaves.
"""


class CharacterRamps:
    """
    Rampas rediseñadas para maximizar legibilidad de silueta.
    Cada nivel tiene peso visual claramente diferenciado.
    """

    # Rampa SIMPLE: Para imágenes pequeñas (15-39 caracteres)
    # CAMBIO CLAVE: Menos niveles, saltos visuales más grandes
    SIMPLE = [
        '⠀',  # Vacío (blanco)
        '⠂',  # Punto mínimo
        '⠇',  # Barra vertical ligera
        '⠿',  # Media densidad con forma
        '⣿'   # Bloque completo (negro)
    ]

    # Rampa MEDIA: Para uso general (40-89 caracteres)
    # Balance entre forma y detalle, pero con saltos claros
    MEDIUM = [
        '⠀',  # blanco
        '⠁',  # punto superior
        '⠃',  # dos puntos
        '⠇',  # barra vertical
        '⠿',  # casi completo superior
        '⡿',  # completo superior + medio
        '⣿'   # negro completo
    ]

    # Rampa DETALLADA: Para imágenes grandes (90+ caracteres)
    # Aquí sí podemos permitir más matices
    DETAILED = [
        '⠀',  # blanco
        '⠁',
        '⠂',
        '⠃',
        '⠇',
        '⠏',
        '⠟',
        '⠿',
        '⡿',
        '⢿',
        '⣻',
        '⣿'  # negro
    ]

    # NUEVA: Rampa EDGE para detección de bordes
    EDGE = [
        '⠀',  # interior/exterior claro
        '│',  # borde vertical
        '─',  # borde horizontal
        '┼',  # intersección
        '█'   # masa sólida
    ]

    @classmethod
    def get_ramp_for_width(cls, width: int) -> list:
        """
        Selecciona la rampa apropiada según el ancho solicitado.
        """
        if width < 40:
            return cls.SIMPLE
        elif width < 90:
            return cls.MEDIUM
        else:
            return cls.DETAILED

    @classmethod
    def get_ramp_info(cls, width: int) -> dict:
        """
        Devuelve información sobre la rampa seleccionada.
        """
        ramp = cls.get_ramp_for_width(width)

        if ramp == cls.SIMPLE:
            profile = "SIMPLE"
            description = "Alto contraste, enfoque en silueta (5 niveles)"
        elif ramp == cls.MEDIUM:
            profile = "MEDIUM"
            description = "Balance entre forma y detalle (7 niveles)"
        else:
            profile = "DETAILED"
            description = "Máximo detalle con gradientes suaves (12 niveles)"

        return {
            "profile": profile,
            "description": description,
            "ramp_length": len(ramp),
            "characters": ramp
        }