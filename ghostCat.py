#!/usr/bin/python3
import socket
import subprocess
import os
import threading
import sys
import argparse


class Server():
    def __init__(self,ip,port,v=0,file=None):
        self.ip = ip
        self.port = port
        self.v = v
        self.file = file
        self.__server__()
        
    def verbose(self,msg):
        if(self.v):
            print(msg)
      
    def __server__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:            
            self.s.bind((self.ip,self.port))
            self.s.listen(1)
            self.verbose("[+] Listening For Connection...")            
            self.c , self.a = self.s.accept()
            self.verbose(f"[+] Conntected To: {self.a[0]} {self.a[1]}")

        except Exception as e:
            print(f"[-] {str(e)[str(e).find(']')+2:]}")
            sys.exit(1)

    def msg_rcv(self):
        while(1):
            try:
                msg = self.c.recv(1024)
            except OSError:
                self.c.close()
                sys.exit(0)
            if msg.decode() == "!quit":
                try:
                    self.verbose("[+]Host Disconnected")
                    self.c.shutdown(socket.SHUT_RDWR)
                    self.c.close()
                    sys.exit(0)
                except Exception as e:
                    self.c.shutdown(socket.SHUT_RDWR)
                    self.c.close()
                    sys.exit(0)
            if len(msg.strip()) > 0:
                print(msg.decode())
       
    def msg_sent(self):
        while(1):
            msg = input()
            if msg == "!quit":
                try:
                    self.c.send(msg.encode())
                    self.c.shutdown(socket.SHUT_RDWR)
                    self.c.close()
                    self.verbose("[+] Disconnected")
                    sys.exit(0)
                except Exception as e:
                    self.c.close()
                    sys.exit(0)
            try:
                self.c.send(msg.encode())
            except Exception as e:
                self.c.close()
                sys.exit(0)
           
    def peer_msg(self):
        m1 = threading.Thread(target=self.msg_rcv)
        m1.start()
        m2 = threading.Thread(target=self.msg_sent)
        m2.start()
        m1.join()
        m2.join()

    def upload_file(self):
        try:
            f = open(self.file,"rb")
            data = f.read()
            self.verbose(f"[+] Successfully Read {self.file}...")
        except Exception as e:
            print(f"[-] {str(e)[str(e).find(']')+2:]}")
            self.c.send(b"<ERROR>")
            self.c.shutdown(socket.SHUT_RDWR)
            self.c.close()
            sys.exit(0)
        
 
        self.c.sendall(data)
        self.verbose(f"[+] Successfully Sent {self.file}...")
        f.close()
        self.c.shutdown(socket.SHUT_RDWR)
        self.c.close()

    def reverse_shell(self):
        while(1):
            cmd = self.c.recv(1024).decode()

            if cmd == "!quit":
                self.c.shutdown(socket.SHUT_RDWR)
                self.c.close()
                break

            elif cmd [:2] == "cd":
                try:
                    os.chdir(cmd[3:])
                    m = "[+] Directory Changed To " + cmd[3:]
                except Exception as e:
                    m = "[-] Error"
                self.c.send(m.encode())
                
            else:
                try:
                    output = subprocess.getoutput(cmd)
                except Exception as e:
                    output = e
                if len(output) == 0:
                    output = "     "
                self.c.send(output.encode())
         

class Client():
    def __init__(self,ip,port,v=0,file=None):
        self.ip = ip
        self.port = port
        self.v = v
        self.file = file
        self.__connect__()
        
    def verbose(self,msg):
        if(self.v):
            print(msg)
      
    def __connect__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:    
            self.s.connect((self.ip,self.port))
            self.verbose(f"[+] Connected To: {self.ip} {self.port}") 
        except Exception as e:
            print(f"[-] {str(e)[str(e).find(']')+2:]}")
            sys.exit(1)

    def msg_rcv(self):
        while(1):
            try:
                msg = self.s.recv(1024)
            except OSError:
                self.s.close()
                sys.exit(0)
            if msg.decode() == "!quit":
                try:
                    self.verbose("[+]Host Disconnected")
                    self.s.shutdown(socket.SHUT_RDWR)
                    self.s.close()
                    sys.exit(0)
                except Exception as e:
                    self.s.shutdown(socket.SHUT_RDWR)
                    self.s.close()
                    sys.exit(0)
            if len(msg.strip()) > 0:
                print(msg.decode())
       
    def msg_sent(self):
        while(1):
            msg = input()
            if msg == "!quit":
                try:
                    self.s.send(msg.encode())
                    self.s.shutdown(socket.SHUT_RDWR)
                    self.s.close()
                    self.verbose("[+] Disconnected")
                    sys.exit(0)
                except Exception as e: 
                    self.s.close()
                    sys.exit(0)
            try:
                self.s.send(msg.encode())
            except Exception as e:
                self.s.close()
                sys.exit(0)
           
    def peer_msg(self):
        m1 = threading.Thread(target=self.msg_rcv)
        m1.start()
        m2 = threading.Thread(target=self.msg_sent)
        m2.start()
        m1.join()
        m2.join()

    def receive_file(self):
        data = b""
        size = 1024
        self.s.settimeout(2)
        try:
            f = open(self.file,"wb")
            self.verbose(f"[+] Successfully Opened {self.file}...")            
        except Exception as e:
            print(f"[-] {str(e)[str(e).find(']')+2:]}")
            self.s.shutdown(socket.SHUT_RDWR)
            self.s.close()
            sys.exit(0)

        byts = self.s.recv(1024)
        if len(byts) == 7 and byts == b"<ERROR>":
            print("[-] Server Site had A ERROR...")
            f.close()
            os.remove(self.file)
            self.s.shutdown(socket.SHUT_RDWR)
            self.s.close()
            sys.exit(0)

        
        while(byts):
            self.verbose(f"[+] File Size: {float(size/1000)}KB")
            data+= byts
            size+= size
            try:
                byts = self.s.recv(size)
            except TimeoutError:
                        break
             
        f.write(data)
        self.verbose(f"[+] Successfully Received {self.file}...")
        f.close()
        self.s.shutdown(socket.SHUT_RDWR)
        self.s.close()
                
    def remote_shell(self):
        while(1):
            cmd = input("$>")
            
            if cmd == "!quit":
                self.s.send(cmd.encode())
                self.s.close()
                break
            else:
                self.s.send(cmd.encode())
                self.s.settimeout(0.5)
                output = self.s.recv(1024) 
                while(len(output)):
                    print(output.decode())
                    try:
                        output = self.s.recv(1024)
                    except TimeoutError:
                        break
                    
def main():
    parser = argparse.ArgumentParser(description='A General NetWork Utility')
    parser.add_argument("-t",help="Target IP",metavar="",dest="t")
    parser.add_argument("-p",type=int,help="Port Number",metavar="",dest="port")
    parser.add_argument("-l",help="Listen For Connection",dest="listen",action='store_true')
    parser.add_argument("-v",help="Enable Verbose Mode",dest="v",action='store_true')
    parser.add_argument("-uf",help="Upload A File,  ex: -uf=path/file.to.send",dest="uf")
    parser.add_argument("-rf",help="Receive A File, ex: -rf=path/file.to.save",dest="rf")
    parser.add_argument("-shell",help="Reverse Sh3ll, ex: ./ghostCat.py -lp [port] -shell ",dest="shell",action='store_true')

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(0)

    else:
        if args.t and args.port and not args.rf and not args.uf and not args.shell:
            x = Client(socket.gethostbyname(args.t),args.port,args.v)
            x.peer_msg()


        elif args.listen and args.port and not args.uf and not args.rf and not args.shell:
            x = Server(socket.gethostbyname(socket.gethostname()),args.port,args.v)
            x.peer_msg()
        
        elif args.uf:
            x = Server(socket.gethostbyname(socket.gethostname()),args.port,args.v,args.uf)
            x.upload_file()

        elif args.rf:
            x = Client(socket.gethostbyname(args.t),args.port,args.v,args.rf)
            x.receive_file() 

        elif args.listen and args.port and args.shell:
            x = Server(socket.gethostbyname(socket.gethostname()),args.port,args.v)
            x.reverse_shell()

        elif args.t and args.port and args.shell:
            x = Client(socket.gethostbyname(socket.gethostname()),args.port,args.v)
            x.remote_shell()           
            
        else:
            parser.print_help(sys.stderr)
                         
try:
    main()
except KeyboardInterrupt:
    sys.exit(0)
except TypeError:
    print("usage: ghostCat [-h] [-t] [-p] [-l] [-v] [-uf UF] [-rf RF]")
except:
    pass
    
    
