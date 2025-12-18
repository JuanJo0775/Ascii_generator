"""
Sistema de rampas de caracteres adaptativas para ASCII art.
Cada rampa está optimizada para diferentes niveles de detalle.
"""


class CharacterRamps:
    """
    Gestiona múltiples rampas de caracteres Unicode/Braille
    para diferentes niveles de detalle en ASCII art.
    """

    # Rampa SIMPLE: Para imágenes pequeñas (15-40 caracteres)
    # Prioriza silueta y contraste sobre detalle
    SIMPLE = [
        '⠀',
        '⣀',
        '⣂',
        '⣆',
        '⣇',
        '⣻',
        '⣿'
    ]

    # Rampa MEDIA: Para uso general (40-90 caracteres)
    # Balance entre forma y detalle
    MEDIUM = [
        '⠀',  # blanco
        '⠁',
        '⠂',
        '⠃',
        '⠇',
        '⠏',
        '⠟',
        '⠿',
        '⡿',
        '⣿'  # negro
    ]

    # Rampa DETALLADA: Para imágenes grandes (90+ caracteres)
    # Máximo detalle con gradientes suaves
    DETAILED = [
        '⠀',  # blanco
        '⠁',
        '⠂',
        '⠃',
        '⠆',
        '⠇',
        '⠏',
        '⠗',
        '⠟',
        '⠯',
        '⠿',
        '⡿',
        '⢿',
        '⣻',
        '⣽',
        '⣾',
        '⣿'  # negro
    ]

    @classmethod
    def get_ramp_for_width(cls, width: int) -> list:
        """
        Selecciona la rampa apropiada según el ancho solicitado.

        Args:
            width: Ancho en caracteres de la imagen ASCII

        Returns:
            Lista de caracteres Unicode apropiada
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
            description = "Alto contraste, enfoque en silueta"
        elif ramp == cls.MEDIUM:
            profile = "MEDIUM"
            description = "Balance entre forma y detalle"
        else:
            profile = "DETAILED"
            description = "Máximo detalle con gradientes suaves"

        return {
            "profile": profile,
            "description": description,
            "ramp_length": len(ramp),
            "characters": ramp
        }