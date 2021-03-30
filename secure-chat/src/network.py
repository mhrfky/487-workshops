import threading
import socket
import common
import message
import message_types
import concurrent.futures

def __send_tcp_message_sync(sender_name, sender_ip, message_type, receiver_ip, message_payload):
    if message_type in message_types.UDP_OPTIONS:
        raise ValueError('message_type DISCOVER or GOODBYE is not accepted.')
    message_to_send = message.encode_message(
        sender_name,
        sender_ip,
        message_type,
        message_payload
    )
    success = False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.settimeout(common.TIMEOUT)
            s.connect((receiver_ip, common.PORT))
            s.sendall(message_to_send)
            success = True
        except:
            pass
    return success


def __send_udp_broadcast_sync(sender_name, sender_ip, message_type):
    if message_type not in message_types.UDP_OPTIONS:
        raise ValueError('Only message_type DISCOVER or GOODBYE is accepted.')
    message_to_send = message.encode_message(
        sender_name,
        sender_ip,
        message_type,
    )
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('',0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
        s.sendto(message_to_send ,('<broadcast>', common.PORT))


def send_tcp_message(sender_name, sender_ip, message_type, receiver_ip, message_payload=""):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(__send_tcp_message_sync, sender_name, sender_ip, message_type, receiver_ip, message_payload)
        return future.result()


def send_udp_broadcast(sender_name, sender_ip, message_type):
    thread = threading.Thread(target=__send_udp_broadcast_sync,
                              args=(sender_name, sender_ip, message_type))
    thread.start()
