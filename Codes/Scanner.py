# coding=utf-8
import json
import os
import shutil
import time
import struct
from os.path import join
from socket import *
from Function import get_md5, file_dir


def file_scanner(IP, IP1, listener_port, file_header_dic, download_list):
    """
    When the "say Hello" process is created
    it is required to send the file list toPeers
    receive the file from Peers
    """
    IP_list = [IP, IP1]
    download_name_list = []
    for p in download_list:
        name, _, _ = p
        download_name_list.append(name)
    list = os.listdir('share')
    send_list = []
    for p in list:
        if p not in download_name_list:
            send_list.append(p)
    list_data = json.dumps(send_list).encode()
    # say hello to another two vm
    for i in range(2):
        try:
            thread_socket = socket(AF_INET, SOCK_STREAM)
            thread_socket.connect((IP_list[i], listener_port))
            print('yes')
            # code = 0 means say hello
            operate_code = struct.pack('!H', 2)
            thread_socket.send(operate_code)
            # send dir to peers
            thread_socket.send(list_data)
            rec_data = thread_socket.recv(1024)
            peer_list = json.loads(rec_data.decode())
            for p in peer_list:
                # new file for me
                if (p not in list) and (p not in download_name_list):
                    download_list.append((p, IP_list[i], 0))
                    download_name_list.append(p)
            thread_socket.close()
        except:
            print('vm is not started')
    if len(download_list) > 0:
        list = []
        for p in download_list:
            list.append(p)
        with open('download_list.log', 'w') as f:
            json.dump(list, f)
    # Iterate through the Share folder
    while True:
        list = os.listdir('share')
        end_time = time.time() + 0.01
        while time.time() <= end_time:
            for p in list:
                download_name_list = []
                for i in download_list:
                    name, _, _ = i
                    download_name_list.append(name)
                if p not in file_header_dic:
                    file_header_dic.setdefault(p, "")
                if os.path.isdir(join(file_dir, p)):
                    md5 = "isfolder000000000000000000000000"
                    if not os.path.isdir(p):
                        shutil.copytree(join(file_dir, p), p)
                else:
                    with open(join(file_dir, p), 'rb') as f:
                        content = f.read(10)
                        md5 = get_md5(content)
                # When new file is found, send peers
                if (md5 != file_header_dic[p]) and (p not in download_name_list):
                    for i in range(2):
                        try:
                            thread_socket = socket(AF_INET, SOCK_STREAM)
                            thread_socket.connect((IP_list[i], listener_port))
                            # code = 0 means that new file
                            operate_code = struct.pack('!H', 0)
                            thread_socket.send(operate_code)
                            # send file information
                            send_data = md5 + p
                            thread_socket.send(send_data.encode())
                            file_header_dic[p] = md5
                            thread_socket.close()
                        except:
                            # print('vm is not connected')
                            continue

        time.sleep(0.1)





