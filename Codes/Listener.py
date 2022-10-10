# coding=utf-8
import json
import os
import struct
from os.path import join
from socket import *
from threading import Thread


from Function import file_dir, get_md5, folder_comprss, file_compress, encry, block_size


def listener(listener_port, file_header_dic, download_list, isEncrypt):
    listener_socket = socket(AF_INET, SOCK_STREAM)  # create a welcome sokcet
    listener_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1) # avoid duplicate binding
    listener_socket.bind(('', listener_port))
    listener_socket.listen(20)
    print('waiting for connection')
    while True:
        thread_socket, addr = listener_socket.accept()
        server_IP, port = addr
        t = Thread(target=sub_connection, args=(thread_socket, server_IP, file_header_dic, download_list, isEncrypt))
        t.start()
        t.join()

def sub_connection(thread_socket, server_IP, file_header_dic, download_list, isEncrypt):
    recv_data = thread_socket.recv(2)
    operate_code = struct.unpack('!H', recv_data)[0]
    print('operate code is: ', operate_code)

    # Peers sent you this file to see if you have it
    if operate_code == 0:
        recv_data = thread_socket.recv(100)
        file_header = recv_data[:32].decode()
        file_name = recv_data[32:].decode()
        print('file name is: ', file_name)
        download_name_list = []
        for p in download_list:
            name, _, _ = p
            download_name_list.append(name)
        if file_name not in file_header_dic:
            file_header_dic.setdefault(file_name, "")
        # file exits and not in download list
        if os.path.isfile(join(file_dir, file_name)) and (file_name not in download_name_list):
            with open(join(file_dir, file_name), 'rb') as f:
                content = f.read(10)
                md5 = get_md5(content)
            if (md5 != file_header) and (file_name not in download_name_list):
                # file is partial updated
                # add file in download list
                download_list.append((file_name, server_IP, 1))
                file_header_dic[file_name] = file_header
                print('partial updated')
        # file has already existed in download list
        elif file_name in download_name_list:
            print('already in donwload list')
        # folder has already existed in share dir
        elif os.path.isdir(join(file_dir, file_name)):
            print('folder already exists')
        # download a folder
        elif file_header[:8] == "isfolder":
            file_header_dic[file_name] = file_header
            download_list.append((file_name, server_IP, 2))
            print(download_list)
            print('it is a folder')
        # download a file
        else:
            print('new file')
            download_list.append((file_name, server_IP, 0))
            file_header_dic[file_name] = file_header
            print('file header dic is:', file_header)


    # send file to peers
    elif operate_code == 1:
        recv_data = thread_socket.recv(100)
        file_name = recv_data.decode()
        if os.path.isdir(join(file_dir, file_name)):
            file_size = -1
        else:
            file_size = os.path.getsize(join(file_dir, file_name))
        # if file is larger than 600MB, then compress
        if file_size > 600 * 1024 * 1024:
            compress_flag = 0
        # if file is small, than do not compress
        elif file_size > 0:
            compress_flag = 1
        # folder
        else:
            compress_flag = 2
        # compress
        if compress_flag == 0 or compress_flag == 2:
            if os.path.isfile(file_name+'.gzz'):
                print('compression file has already existed')
            else:
                if compress_flag == 2:
                    folder_comprss(file_name, file_name+'.gzz')
                else:
                    print('start compressing')
                    file_compress(file_name, file_name + '.gzz', 1)
        # encrypt
        if isEncrypt == 'yes':
            encry(file_name, file_name + '_encrypt')
        try:
            # send file information
            send_file_information(file_name, block_size, thread_socket, compress_flag, isEncrypt)
            recv_data = thread_socket.recv(4)
            # send data from block index
            block_index = struct.unpack('!I', recv_data[:4])[0]
            if block_index > 0:
                send(file_name, block_index-1, block_size, thread_socket, compress_flag, isEncrypt)
            else:
                partial_send(file_name, block_size, thread_socket)
        except:
            print('connnection is broken')

    # say hello to peeers, exchange share dir
    elif operate_code == 2:
        list = os.listdir('share')
        download_name_list = []
        for p in download_list:
            name, _, _ = p
            download_name_list.append(name)
        send_list = []
        for p in list:
            # avoid sending file which is not complete
            if p not in download_name_list:
                send_list.append(p)
        recv_data = thread_socket.recv(1024)
        peer_list = json.loads(recv_data.decode())
        send_data = json.dumps(send_list).encode()
        thread_socket.send(send_data)
        for p in peer_list:
            if (p not in list) and (p not in download_name_list):
                download_list.append((p, server_IP, 0))
                download_name_list.append(p)

    # Write the file to JSON for breakpoint continuingly
    if len(download_list) > 0:
        list = []
        for p in download_list:
            list.append(p)
        with open('download_list.log', 'w') as f:
            json.dump(list, f)

    thread_socket.close()
    exit()

def send(file_name, block_index, block_size, connection_socket, compress_flag, isEncrypt):
    # encrypt
    if isEncrypt == 'yes':
        file_size = os.path.getsize(file_name + '_encrypt')
        true_file_name = file_name + '_encrypt'
    else:
        # compress but not encrypt
        if compress_flag == 0 or compress_flag == 2:
            file_size = os.path.getsize(file_name + '.gzz')
            true_file_name = file_name + '.gzz'
        # neither compressed nor encrypted
        else:
            file_size = os.path.getsize(join(file_dir, file_name))
            true_file_name = join(file_dir, file_name)

    with open(true_file_name, 'rb') as f:
        f.seek(block_index)
        while True:
            data = f.read(block_size)
            # print('block index is: ', block_index)
            send_data = data
            connection_socket.send(send_data)
            block_index += len(data)
            if block_index >= file_size:
                print('sending file is finished')
                break


def partial_send(file_name, block_size, connection_socket):
    total_size = 300 * 1024
    print('partial download')
    with open(join(file_dir, file_name), 'rb') as f:
        while total_size > 0:
            content = f.read(block_size)
            total_size -= len(content)
            connection_socket.send(content)


def send_file_information(file_name, block_size, connectionSocket, compress_flag, isEncrypt):
    if isEncrypt == 'yes':
        true_file_name = file_name + '_encrypt'
    else:
        if compress_flag == 0 or compress_flag == 2:
            true_file_name = file_name + '.gzz'
        else:
            true_file_name = join(file_dir, file_name)

    file_size = os.path.getsize(true_file_name)
    real_file_size = os.path.getsize(join(file_dir, file_name))
    send_data = struct.pack('!IIIH', file_size, block_size, real_file_size,compress_flag)
    connectionSocket.send(send_data)
    print('sending file is: ', file_name)
