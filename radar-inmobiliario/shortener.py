import string

# El abecedario del acortador: 0-9, a-z, A-Z (62 caracteres)
CHARSET = string.digits + string.ascii_lowercase + string.ascii_uppercase

def encode(num):
    """Convierte un ID numérico en un slug Base62."""
    if num == 0:
        return CHARSET[0]
    arr = []
    base = len(CHARSET)
    while num:
        num, rem = divmod(num, base)
        arr.append(CHARSET[rem])
    arr.reverse()
    return ''.join(arr)

def decode(string):
    """Convierte un slug Base62 de vuelta a un ID numérico."""
    base = len(CHARSET)
    strlen = len(string)
    num = 0
    idx = 0
    for char in string:
        power = (strlen - (idx + 1))
        num += CHARSET.index(char) * (base ** power)
        idx += 1
    return num
