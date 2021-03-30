import json

encoding = 'utf-8'


def encode_message(name, ip, message_type, payload=''):
    data = {
        'NAME': name,
        'MY_IP': ip,
        'TYPE': message_type,
        'PAYLOAD': payload,
    }
    return json.dumps(data).encode(encoding) + b'\n'


def decode_message(message):
    decoded_message = json.loads(bytes.decode(message, encoding))
    return (
        decoded_message['NAME'],
        decoded_message['MY_IP'],
        decoded_message['TYPE'],
        decoded_message['PAYLOAD']
    )
