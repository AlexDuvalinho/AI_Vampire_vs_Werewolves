import utils.server_interface as sv
import player_split_leo as leo
#import smart_player as sp
import greedy_smart_player as al

#IP = '127.0.0.1'
# IP = '138.195.48.159'
#IP= '15.188.65.243'
IP = '192.168.56.102'
#IP = '127.0.0.1'
SERVER = sv.ServerInterface(IP, '5555', 'leo')
leo.run(SERVER)