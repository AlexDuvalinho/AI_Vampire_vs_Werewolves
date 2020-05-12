import utils.server_interface as sv
import player_alex_merge as alx
#import smart_player as sp
import player_split_AL as al

#IP = '127.0.0.1'
#IP = '138.195.48.159'
#IP= '15.188.65.243'
IP = '192.168.56.102'

SERVER = sv.ServerInterface(IP, '5555', 'alx')
alx.run(SERVER)
