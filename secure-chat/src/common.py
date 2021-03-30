import secrets

PORT = 12345
TIMEOUT = 5
BUFFER_SIZE = 1000
BROADCAST_COUNT = 3
DEBUG = False
PRIME_COUNT = 254
RANDOM_LIMIT = 1000


def is_prime(num: int):
    for i in range(2, num//2 + 1):
        if num % i == 0:
            return False
    return True


def generate_prime_numbers(amount: int):
    result = []
    number = 2
    count = 0
    while count < amount:
        if is_prime(number):
            result.append(number)
            count += 1
        number += 1
    return result


PRIME_NUMBERS = generate_prime_numbers(PRIME_COUNT)


def get_random_prime():
    rand_index = secrets.randbelow(PRIME_COUNT)
    return PRIME_NUMBERS[rand_index]


def get_random():
    return secrets.randbelow(RANDOM_LIMIT)
