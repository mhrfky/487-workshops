import pyDes
from functools import reduce

encoding = 'utf-8'


def encrypt_message(message: str, cypher: int):
    return pyDes.triple_des(str(cypher).ljust(24)).encrypt(message.encode(encoding), padmode=2).hex()


def decrypt_message(message: str, cypher: int):
    return pyDes.triple_des(str(cypher).ljust(24)).decrypt(bytearray.fromhex(message), padmode=2).decode(encoding)

def get_evolved_cypher(message: str, cypher: int, p_value: int):
    '''
        Calculates evolved cypher with:
        let magic_key be summation of integer values of each character in the message,
        evolved_cypher = ((cypher + magic_key) ** magic_key) % p_value
        where p_value is a prime number to calculate modulo for session of the cypher.
    ''' 
    magic_key = reduce(lambda x,y: x + y, [ord(c) for c in message])
    return ((cypher + magic_key) ** magic_key) % p_value
