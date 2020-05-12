import socket
import struct
import numpy as np

class ServerInterface:
    def __init__(self, host, port, name='SAL'):
        # define the server host, port, and socket
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # connect to the socket
        self.sock.connect((self.host, int(self.port)))
        # send the team name
        self.__setName(name)
        self.board_h, self.board_w = self.__getGridInformation()
        self.humanHousesPosition = self.getHumanHouses()
        self.startingPosition = self.getStartingPosition()
        self.mapInfo = self.getMapInfo()

    def __receiveData(self, sock, size, fmt):
        data = bytes()
        while len(data) < size:
            data += sock.recv(size - len(data))
        return struct.unpack(fmt, data)

    def __setName(self, name):
        self.sock.send("NME".encode("ascii"))
        self.sock.send(struct.pack("1B", 3))
        self.sock.send(name.encode("ascii"))

    def __getGridInformation(self):
        header = self.sock.recv(3).decode("ascii")
        if header != "SET":
            print("Protocol Error at SET")
        else:
            (height, width) = self.__receiveData(self.sock, 2, "2B")
            return height, width

    def getHumanHouses(self):
        header = self.sock.recv(3).decode("ascii")
        if header != "HUM":
            print("Protocol Error at HUM")
        else:
            number_of_homes = self.__receiveData(self.sock, 1, "1B")[0]
            homes_raw = self.__receiveData(self.sock, number_of_homes * 2, "{}B".format(number_of_homes * 2))
            return number_of_homes, len(homes_raw)

    def getStartingPosition(self):
        header = self.sock.recv(3).decode("ascii")
        if header != "HME":
            print("Protocol Error at HME")
        else:
            start_position = tuple(self.__receiveData(self.sock, 2, "2B"))
            return list(start_position)

    def getMapInfo(self):
        header = self.sock.recv(3).decode("ascii")
        if header != "MAP":
            print("Protocol Error at MAP")
        else:
            number_map_commands = self.__receiveData(self.sock, 1, "1B")[0]
            map_commands_raw = self.__receiveData(self.sock, number_map_commands * 5, "{}B".format(number_map_commands * 5))
            map_commands_raw = (np.reshape(np.array(map_commands_raw), (-1, 5)))
            return map_commands_raw

    def update(self):
        header = self.sock.recv(3).decode("ascii")
        if header != "UPD" and header != "END" and header != "BYE":
            print("Protocol Error at MAP")
        elif header == "UPD":
            number_upd_commands = self.__receiveData(self.sock, 1, "1B")[0]
            upd_commands_raw = self.__receiveData(self.sock, number_upd_commands * 5,
                                                  "{}B".format(number_upd_commands * 5))
            upd_commands_raw = (np.reshape(np.array(upd_commands_raw), (-1, 5)))
            return "UPD", upd_commands_raw
        elif header == "END":
            return "Game ENDED", []
        else:
            return "BYE", []


    def movePlayers(self, source, nb_creatures, target):
        #TODO manage multiple targets
        num_moves = len(nb_creatures)
        self.sock.send("MOV".encode("ascii"))
        self.sock.send(struct.pack("1B", num_moves))  # number of moves
        for i in range(0, num_moves):
            self.sock.send(struct.pack("2B", *source[i]))  # source coordinates
            self.sock.send(struct.pack("1B", nb_creatures[i]))  # number of creatures
            self.sock.send(struct.pack("2B", *target[i]))  # target coordinates
            
    def movePlayers_split(self, source, target):
        #TODO manage multiple targets
        num_moves = len(target)
        self.sock.send("MOV".encode("ascii"))
        self.sock.send(struct.pack("1B", num_moves))  # number of moves
        for i in range(0, num_moves):
            self.sock.send(struct.pack("2B", *source[i]))  # source coordinates
            self.sock.send(struct.pack("1B", target[i][2]))  # number of creatures
            self.sock.send(struct.pack("2B", target[i][0],target[i][1]))  # target coordinates

    def movePlayers_split_Leo(self, moveOption):
        self.sock.send("MOV".encode("ascii"))
        self.sock.send(struct.pack("1B", len(moveOption)))
        for move in moveOption:
            x_target, y_target, nb, x_orig, y_orig = move
            self.sock.send(struct.pack("2B", x_orig, y_orig))
            self.sock.send(struct.pack("1B", nb))
            self.sock.send(struct.pack("2B", x_target, y_target))

