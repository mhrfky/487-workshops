#!/usr/bin/env python3
#ulimit -Sn 10000
import json
import sys
import time
import os
import socket
import time
from _thread import *
from threading import Timer
import threading
import subprocess
import os
# import pandas as pd
import pickle


class PythonChat :
    total_unread = 0
    all_users = {}
    store_messages = {}
    def __init__(self, username, port):
        self.username = username
        self.ip = self.get_ip()
        self.network = self.ip[:self.ip.rfind('.')]
        self.port = port

    def get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def broadcast_thread_starter(self):
        __broadcast_thread__ = threading.Thread(target=self.broadcast)
        # __broadcast_thread__.setDaemon(True)
        __broadcast_thread__.start()

    def broadcast(self):
        while True:
            for i in range(1,255):
                target_ip = self.network + "." + str(i)

                if self.ip != target_ip:

                    

                    packet = {
                        "TYPE" : "DISCOVER",
                        "NAME": self.username,
                        "MY_IP": str(self.ip),
                        "PAYLOAD": ""
                        }
                    packet = json.dumps(packet)
                    # self.write_file("broadcast_log.txt", packet)
                    start_new_thread(self.send_packet, (target_ip, self.port, packet))
                    
                    
                else:
                    continue
            time.sleep(20)  


    def send_packet(self, target_ip, port, packet):
        try:
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect((target_ip, port))
                s.send(packet.encode('ascii', 'replace'))
                s.close()
        except:
            #print(target_ip,packet)
            pass

    def receivePacket(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.ip, self.port))
            s.listen()
            while(True):
                try:
                    conn, addr = s.accept()
                    data = conn.recv(2048)
                        
                    if not data:
                        break

                    
                    message = data.decode('ascii').replace("'", '"')
                    messagedic = json.loads(message)
                    
                    #discovery
                    if(messagedic["TYPE"] == "DISCOVER"):
                        if (messagedic["MY_IP"] not in self.all_users):
                            print("Notification: You have been discovered by", messagedic["NAME"]," with the ip ",messagedic["MY_IP"])
                        #-------------- add to onlines   ---------------------------#
                            self.all_users[messagedic["MY_IP"]] = messagedic["NAME"]
                            self.store_messages[messagedic["NAME"]] = [""]
                        # #-------------- reply            ----------------------------#
                        packet = {
                            "TYPE" : "RESPOND",
                            "NAME": self.username,
                            "MY_IP": str(self.ip),
                            "PAYLOAD": ""
                            }
                        packet = json.dumps(packet)
                        # self.write_file("broadcast_log.txt", packet)
                        start_new_thread(self.send_packet, (messagedic["MY_IP"], self.port, packet))
                        
                    #response
                    elif(messagedic["TYPE"] == "RESPOND"):
                        if (messagedic["MY_IP"] not in self.all_users):
                            print("Notification: You have discovered ", messagedic["NAME"]," with the ip ",messagedic["MY_IP"])
                            self.all_users[messagedic["MY_IP"]] = messagedic["NAME"]
                            self.store_messages[messagedic["NAME"]] = [""]
                        #add to onlines
                        
                    #message
                    elif(messagedic["TYPE"] == "MESSAGE"):
                        if(messagedic["MY_IP"] not in self.all_users):
                            self.all_users[messagedic["MY_IP"]] = messagedic["NAME"]
                            self.store_messages[messagedic["NAME"]] = [""]
                        sms = messagedic["NAME"] + " : " + messagedic["PAYLOAD"]
                        name = messagedic["NAME"]
                        print("Notification: ",messagedic["NAME"]," has messaged you.")
                        self.store_messages[messagedic["NAME"]].append(sms)

                    else:
                        print("Unindenfied Packet Received from this ip:", messagedic["MY_IP"])


                except ValueError:
                    print("Error receiving a packet")
        
    def receivePacket_thread(self):
        receive_thread = threading.Thread(target=self.receivePacket)
        # receive_thread.setDaemon(True)
        receive_thread.start()

    def respondPacket_thread(self):
        respond_thread = threading.Thread(target=self.respondPacket)
        # receive_thread.setDaemon(True)
        respond_thread.start()
    def respondPacket(self):
        packet = {
                        "TYPE" : "RESPOND",
                        "NAME": self.username,
                        "MY_IP": str(self.ip),
                        "PAYLOAD": ""
                        }
        packet = json.dumps(packet)
        while True:
            copy = self.all_users.copy()
            for ip in self.all_users:
                #print(ip, " to be sent a response")
                self.send_packet(ip,"12345",packet)
            time.sleep(30)
    
            
            

    def viewDiscovered(self):
        os.system('clear')
        print("Recently online friends in this LAN:")
        for x in self.all_users:
            print(self.all_users[x]," ",x)
        print("#--------------------------------------------------#")
        input("Press enter to return the main menu...")

    def showProfile(self):
        os.system('clear')
        print("Username:   ",self.username)
        print()
        print("IP :  ", self.ip)
        print()
        print("Network :  ",self.network)
        print()
        print("#--------------------------------------------------#")
        input("Press enter to return the main menu...")

    def commands(self):
        os.system('clear')
        os.system('clear')

        print("1) View Discovered Users:")
        print("2) Show my Profile")
        print("3) Send Message")
        print("4) Show Chats")
        print("5) Quit")
        
        command = input("Enter your command  : ") 
        
        if command == "1":
            self.viewDiscovered()
            self.commands()

        elif command == "2":
            self.showProfile()
            self.commands()
        elif command == "3":
            self.sendMessage()
            self.commands()
        elif command == "4":
            self.showChats()
            self.commands()
        elif command == "5":
            os.system('clear')
            print("[!]","Thank you for using this application dear",self.username)
            print("\n")
            for x in self.store_messages:
                strr = x + ".txt"
                f = open(strr,"w")
                for message in self.store_messages[x]:
                    f.write(message)
            sys.exit(0)
        else:
            self.commands()
            
    def showChats(self):
        for x in self.store_messages:
            print(x)
        name = input("Enter the name you want to see chat with : ")
        if (name not in self.store_messages):
            name = input("Please enter a name on the list : ")
        os.system('clear')
        for message in self.store_messages[name]:
            print(message)
        input("Press enter to go back to the main page")
        os.system('clear')

    def sendMessage(self):
        os.system('clear')
        os.system('clear')

        print("Recently online friends in this LAN:")
        for x in self.all_users:
            print(self.all_users[x]," ",x)
        print("#--------------------------------------------------#")
        

        ip = input("Enter the IP of the one you want to contact : ")
        
        while ip not in self.all_users:
            if ip == "" :
                return
            ip = input("Please enter a proper IP : ")
        os.system('clear')
        print("#--------------------------------------------------#")

        for x in self.store_messages:
                strr = x + ".txt"
                f = open(strr,"w")
                for message in self.store_messages[x]:
                    print(message)

        print("#--------------------------------------------------#")

        message = input("Enter empty line to go back to the main menu : ")
        if(message !=""):
            packet = {
                            "TYPE" : "MESSAGE",
                            "NAME": self.username,
                            "MY_IP": str(self.ip),
                            "PAYLOAD": message
                            }
            packet = json.dumps(packet)
            sms = self.username + " : " + message
            self.store_messages[self.all_users[ip]].append(sms)
            start_new_thread(self.send_packet, (ip, self.port, packet))
        

uname = input("Enter the name you want to use:")
asd = PythonChat(uname, 12345)


asd.broadcast_thread_starter()
asd.receivePacket_thread()
asd.respondPacket_thread()
asd.commands()