import socket
import threading
import sys
import common
import message
import message_types
import network
import select
import session_keys
import security


class Client:
    ip = ''
    base_ip = ''
    name = ''
    other_clients = {}  # Map from "client_name: string" to "client_ip: string"
    listening = False
    sessions = {}  # Map from "client_ip: string" to "session: { message_queue: list, cypher: string, private_key: string }"

    def __init__(self, name):
        self.name = name
        self.__get_ip()

    def __get_ip(self):
        ''' 
            Finds current machine's IP address by creating
            a dummy socket connection to "8.8.8.8:80"
        '''
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            self.ip = ip
            self.base_ip = self.__get_base_ip(ip)

    def __get_base_ip(self, ip):
        split = ip.split('.')
        return '.'.join(split[:-1])

    def __get_session_ip(self, other_client_ip):
        if other_client_ip == self.ip:
            return other_client_ip + 'x'
        return other_client_ip

    def __send_message(self, receiver_ip, message_type, message_payload="", receiver_name=""):
        if message_type == message_types.MESSAGE:
            # If there is no session for receiver_ip
            if receiver_ip not in self.sessions:
                # Generate values
                private_key = common.get_random()
                g_value = common.get_random_prime()
                p_value = common.get_random_prime()
                public_key = (g_value ** private_key) % p_value
                # Create session
                session = self.sessions[receiver_ip] = {}
                session[session_keys.PRIVATE_KEY] = private_key
                session[session_keys.P_VALUE] = p_value
                message_queue = session[session_keys.MESSAGE_QUEUE] = []
                # Add message to a queue
                message_queue.append(message_payload)
                if common.DEBUG:
                    print("Sender session created", self.sessions)
                # Prepare INIT_SEND message
                message_type = message_types.INIT_SEND
                message_payload = (g_value, p_value, public_key)
            else:
                # Encrypt message_payload
                session = self.sessions[receiver_ip]
                cypher = session[session_keys.CYPHER]
                p_value = session[session_keys.P_VALUE]
                # Get evolved cypher before encyripting it
                cypher_evolved = security.get_evolved_cypher(
                    message_payload, cypher, p_value)
                # Encyript the message
                message_payload = security.encrypt_message(
                    message_payload, cypher)
                # Update the cyhper with evolved one
                session[session_keys.CYPHER] = cypher_evolved
                if common.DEBUG:
                    print("Sender updated session with evolved cypher",
                          self.sessions)
            session['receiver_name'] = receiver_name

        success = network.send_tcp_message(
            self.name,
            self.ip,
            message_type,
            receiver_ip,
            message_payload,
        )
        if not success:
            print(f'Your message has not received by {receiver_name}')
            self.__remove_from_other_clients(receiver_name)

    def __add_to_other_clients(self, name, ip):
        if name not in self.other_clients.keys():
            self.other_clients[name] = ip
            if common.DEBUG:
                print('Online client map:', self.other_clients)
            print(f'{name} is online.')

    def __remove_from_other_clients(self, name):
        if name in self.other_clients.keys():
            other_client_ip = self.other_clients[name]
            session_ip = self.__get_session_ip(other_client_ip)
            # Remove other client from "name: ip" map
            self.other_clients.pop(name, None)
            # Remove other client from session map
            self.sessions.pop(other_client_ip, None)
            if other_client_ip != session_ip:
                self.sessions.pop(session_ip, None)
            if common.DEBUG:
                print('Online client map:', self.other_clients)
                print('Session map:', self.sessions)
            print(f'{name} is offline.')

    def __handle_received_data(self, data):
        sender_name, sender_ip, message_type, message_payload = message.decode_message(
            data)
        if message_type == message_types.DISCOVER:
            # Send a respond message
            self.__send_message(
                sender_ip, message_types.RESPOND)
            self.__add_to_other_clients(
                sender_name, sender_ip)
        elif message_type == message_types.RESPOND:
            self.__add_to_other_clients(
                sender_name, sender_ip)
        elif message_type == message_types.MESSAGE:
            # Read session
            session_ip = self.__get_session_ip(sender_ip)
            if session_ip in self.sessions:
                session = self.sessions[session_ip]
                cypher = session[session_keys.CYPHER]
                p_value = session[session_keys.P_VALUE]
                message_payload = security.decrypt_message(
                    message_payload, cypher)
                # Update cypher for this session
                cypher = security.get_evolved_cypher(
                    message_payload, cypher, p_value)
                session[session_keys.CYPHER] = cypher
                if common.DEBUG:
                    print('Receiver updated session with evolved cypher',
                          self.sessions)
            # Print out the message
            print(sender_name, ':', message_payload)
            self.__add_to_other_clients(
                sender_name, sender_ip)
        elif message_type == message_types.INIT_SEND:
            # Read public_key, g_value, p_value values of other client
            (g_value, p_value, other_public_key) = message_payload
            # Calculate public_key
            private_key = common.get_random()
            public_key = (g_value ** private_key) % p_value
            # Calculate cypher with public_key and other_public_key
            cypher = (other_public_key ** private_key) % p_value
            # Create session
            session_ip = self.__get_session_ip(sender_ip)
            session = self.sessions[session_ip] = {}
            session[session_keys.PRIVATE_KEY] = private_key
            session[session_keys.P_VALUE] = p_value
            # Store cypher of this session in dictionary
            session[session_keys.CYPHER] = cypher
            if common.DEBUG:
                print("Receiver stored cypher:", self.sessions)
            # Send INIT_RESPOND with public_key in it
            init_respond_payload = (g_value, p_value, public_key)
            self.__send_message(
                sender_ip, message_types.INIT_RESPOND, init_respond_payload)
        elif message_type == message_types.INIT_RESPOND:
            # Read public_key of other client
            (g_value, p_value, other_public_key) = message_payload
            # Calculate cypher with other_public_key
            session = self.sessions[sender_ip]
            private_key = session[session_keys.PRIVATE_KEY]
            cypher = (other_public_key ** private_key) % p_value
            # Store cypher of this session in dictionary
            session[session_keys.CYPHER] = cypher
            if common.DEBUG:
                print('Sender updated session with cypher', session)
            # Send messages in the queue
            for msg in session[session_keys.MESSAGE_QUEUE]:
                self.__send_message(sender_ip, message_types.MESSAGE, msg)
        else:
            if common.DEBUG:
                print('Message wasn\'t interpreted:', data)

    def __listen_tcp_sync(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if common.DEBUG:
                print('Start listening on TCP')
            s.bind((self.ip, common.PORT))
            s.listen(5)
            while True:
                conn, _ = s.accept()
                with conn:
                    while self.listening:
                        data = conn.recv(1024)
                        if not data:
                            break
                        if common.DEBUG:
                            print('TCP Data recieved:', data)
                        self.__handle_received_data(data)

    def __listen_udp_sync(self):
        if common.DEBUG:
            print('Start listening on UDP')

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('', common.PORT))
            s.setblocking(0)
            while self.listening:
                try:
                    result = select.select([s], [], [])
                    data = result[0][0].recv(common.BUFFER_SIZE)
                    if common.DEBUG:
                        print('UDP Data recieved:', data)
                    sender_name, sender_ip, message_type, message_payload = message.decode_message(
                        data)
                    if message_type == message_types.DISCOVER:
                        # Send a respond message
                        self.__send_message(
                            sender_ip, message_types.RESPOND)
                        self.__add_to_other_clients(
                            sender_name, sender_ip)
                    elif message_type == message_types.GOODBYE:
                        self.__remove_from_other_clients(sender_name)
                except KeyboardInterrupt:
                    print('Keyboard interrupt')
                    self.__stop_listening()

    def __start_listening(self):
        self.listening = True
        tcp_thread = threading.Thread(target=self.__listen_tcp_sync)
        tcp_thread.start()
        udp_thread = threading.Thread(target=self.__listen_udp_sync)
        udp_thread.start()

    def __stop_listening(self):
        self.listening = False
        self.__send_goodbye_messages()

    def __send_discovery_messages(self):
        if common.DEBUG:
            print('Send Discovery Messages...')
        for i in range(common.BROADCAST_COUNT):
            try:
                network.send_udp_broadcast(
                    self.name,
                    self.ip,
                    message_types.DISCOVER
                )
            except:
                pass

    def __send_goodbye_messages(self):
        if common.DEBUG:
            print('Send Goodbye Messages...')
        for i in range(common.BROADCAST_COUNT):
            try:
                network.send_udp_broadcast(
                    self.name,
                    self.ip,
                    message_types.GOODBYE
                )
            except:
                pass

    def __start_messaging(self):
        print('You can send messages with "Your message" -> "Arrival Name". Example: Hi! -> Eren')
        for line in sys.stdin:
            if ' -> ' not in line:
                print('Please give valid input: "Your message" -> "Arrival Name"')
                continue
            line = line[:-1]
            [message_input, other_client] = line.split(' -> ')
            if other_client not in self.other_clients:
                print(other_client, 'is not online')
                continue
            other_ip = self.other_clients[other_client]
            self.__send_message(
                other_ip, message_types.MESSAGE, message_input, other_client)

    def enter_chat(self):
        self.__start_listening()
        self.__send_discovery_messages()
        try:
            self.__start_messaging()
        except KeyboardInterrupt:
            print('\nYou\'ve stopped message sending. Press CTRL+C again to leave')
            self.__stop_listening()
