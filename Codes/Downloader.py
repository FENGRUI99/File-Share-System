# coding=utf-8
import os
import time
import struct

from os.path import join
from socket import *


from Function import file_dir, decry, file_decompress, folder_decompress


def download(thread_socket, file_name, block_index, block_size, file_size, compress_flag, isEncrypt):
    while True:
        if block_index < file_size:
            w_data = thread_socket.recv(block_size)
            block_index += len(w_data)
            # print('block index is: ', block_index)
            if block_index <= file_size:
                if isEncrypt == 'yes':
                    true_file_name = file_name + '_encrypt'
                else:
                    if compress_flag == 0 or compress_flag == 2:
                        true_file_name = file_name + '.gzz'
                    else:
                        true_file_name = join(file_dir, file_name)

                with open(true_file_name, 'ab') as f:
                    f.write(w_data)

        # download is finished
        elif block_index >= file_size:
            print('file download is finished')
            break

    thread_socket.close()


def partial_download(download_socket, file_name, block_size):
    # only receive 300 * 1024 binary data from sender
    total_size = 300 * 1024
    data = b''
    while total_size > 0:
        rec = download_socket.recv(block_size)
        data += rec
        total_size -= len(rec)
    with open(join(file_dir, file_name), 'rb+') as f_write:
        f_write.write(data)



def downloader(listener_port, download_list, isEncrypt):
    while True:
        if len(download_list) > 0:
            start = time.time()
            print('initial state ', download_list)
            file_name, server_IP, download_code = download_list[0]
            print('start to download file ', file_name)
            file = download_list[0]
            clientSocket = socket(AF_INET, SOCK_STREAM)
            clientSocket.connect((server_IP, listener_port))
            operate_code = struct.pack('!H', 1)
            clientSocket.send(operate_code)
            # send file name to peers
            clientSocket.send(file_name.encode())
            # receive file information form peers
            rec_data = clientSocket.recv(14)
            file_size, block_size, real_file_size, compress_flag = struct.unpack('!IIIH', rec_data[0:14])
            print('file from host: ', server_IP)
            print('file name is: ', file_name)
            print('file size is: ', file_size)
            print('compress flag is: ', compress_flag)

            # whole file download
            if download_code == 0 or download_code == 2:
                # Breakpoint continuingly
                if os.path.isfile(join(file_dir, file_name)):
                    block_index = os.path.getsize(join(file_dir, file_name)) + 1
                else:
                    block_index = 1
            # partial updated
            elif download_code == 1:
                block_index = 0
            send_data = struct.pack('!I', block_index)
            clientSocket.send(send_data)

            # download
            if download_code == 0 or download_code == 2:
                download(clientSocket, file_name, block_index-1, block_size, file_size, compress_flag, isEncrypt)
            # partial download
            elif download_code == 1:
                partial_download(clientSocket, file_name, block_size)

            # Encrypt
            if isEncrypt == 'yes':
                print('ready to decrypt')
                decry(file_name + '_encrypt', file_name, real_file_size)
            # compress file
            if compress_flag == 0:
                file_decompress(file_name + '.gzz', file_name)
            # compress folder
            elif compress_flag == 2:
                folder_decompress(file_name + '.gzz')

            end_time = time.time() - start
            print('donwload file', file_name,'is finished. Total time is:', end_time)
            print('file size is: ', os.path.getsize(join(file_dir, file_name)) / 1024 / 1024, 'MB')
            print('donwload speed is: ', os.path.getsize(join(file_dir, file_name)) * 8/ end_time / 1024 / 1024,'Mbps')

            download_list.remove(file)
        else:

            # print('all files is downloaded')
            if os.path.isfile('download_list.log'):
                os.remove('download_list.log')
            time.sleep(0.1)
