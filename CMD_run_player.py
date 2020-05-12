#!/usr/bin/env python3
import utils.server_interface as sv
import player_alex_merge as alx
import sys

#python CMD_run_player.py 192.168.56.102 5555 leo&

def main():
    _, IP, port, name = sys.argv
    
    SERVER = sv.ServerInterface(IP, port, name)
    alx.run(SERVER)

if __name__ == "__main__":
    main()