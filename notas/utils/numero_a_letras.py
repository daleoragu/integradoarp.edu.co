# notas/utils/numero_a_letras.py

UNIDADES = [
    '', 'UN ', 'DOS ', 'TRES ', 'CUATRO ', 'CINCO ', 'SEIS ', 'SIETE ', 'OCHO ', 'NUEVE '
]
DECENAS = [
    'DIEZ ', 'ONCE ', 'DOCE ', 'TRECE ', 'CATORCE ', 'QUINCE ', 'DIECISEIS ',
    'DIECISIETE ', 'DIECIOCHO ', 'DIECINUEVE ', 'VEINTE '
]
CENTENAS = [
    '', 'CIENTO ', 'DOSCIENTOS ', 'TRESCIENTOS ', 'CUATROCIENTOS ', 'QUINIENTOS ',
    'SEISCIENTOS ', 'SETECIENTOS ', 'OCHOCIENTOS ', 'NOVECIENTOS '
]

def numero_a_letras(numero):
    """
    Convierte un número entero a su representación en letras.
    Limitado hasta 999,999,999
    """
    try:
        numero = int(numero)
    except (ValueError, TypeError):
        return ""

    if numero == 0:
        return 'CERO'
    
    letras = ''
    
    # Millones
    if numero >= 1000000:
        if numero // 1000000 == 1:
            letras += 'UN MILLON '
        else:
            letras += _convertir_segmento(numero // 1000000) + 'MILLONES '
        numero %= 1000000

    # Miles
    if numero >= 1000:
        if numero // 1000 == 1:
            letras += 'MIL '
        else:
            letras += _convertir_segmento(numero // 1000) + 'MIL '
        numero %= 1000

    # Centenas, decenas y unidades
    if numero > 0:
        letras += _convertir_segmento(numero)

    return letras.strip()

def _convertir_segmento(n):
    """Convierte un número de hasta 3 dígitos a letras."""
    if n == 100:
        return 'CIEN '
    
    letras_segmento = ''
    
    # Centenas
    if n > 100:
        letras_segmento += CENTENAS[n // 100]
    
    n %= 100
    
    # Decenas y unidades
    if n > 0:
        if n < 10:
            letras_segmento += UNIDADES[n]
        elif n < 21:
            letras_segmento += DECENAS[n - 10]
        else:
            decena = n // 10
            unidad = n % 10
            if decena == 2:
                letras_segmento += 'VEINTI'
                if unidad > 0:
                    letras_segmento = letras_segmento[:-1] + UNIDADES[unidad]
            else:
                letras_segmento += ['TREINTA ', 'CUARENTA ', 'CINCUENTA ', 'SESENTA ', 'SETENTA ', 'OCHENTA ', 'NOVENTA '][decena - 3]
                if unidad > 0:
                    letras_segmento += 'Y ' + UNIDADES[unidad]
                    
    return letras_segmento
