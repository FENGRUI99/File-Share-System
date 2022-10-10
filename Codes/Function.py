# coding=utf-8
import argparse

import os
import tarfile

import time

from os.path import join

from Crypto.Cipher import AES
import hashlib
import zlib



block_size = 150 * 1024
file_dir = join(os.getcwd(), 'share')


def _argparse():
    parser = argparse.ArgumentParser(description="This is description!")
    parser.add_argument('--ip', action='store', dest='path',
                        help='The hostname of server')
    parser.add_argument('--encryption', action='store', dest='encrypt',
                        help='Whether enable encryption', default='no')
    return parser.parse_args()




def get_file_md5(file_name, compress_flag, isEncrypt):
    md5 = hashlib.md5()
    if isEncrypt == 'yes':
        true_file_name = file_name + '_encrypt'
    else:
        if compress_flag == 0:
            true_file_name = file_name + '.gzz'
        else:
            true_file_name = join(file_dir, file_name)

    with open(true_file_name, 'rb') as f:
        while True:
            content = f.read(10240)
            if content:
                md5.update(content)
            else:
                break
    ret = md5.hexdigest()
    return ret


def get_md5(data):
    md5 = hashlib.md5()
    md5.update(data)
    ret = md5.hexdigest()
    return ret

def folder_comprss(folder_dir, folder_compress):
    with tarfile.open(folder_compress, "w:gz") as tar:
        tar.add(folder_dir, arcname=os.path.basename(folder_dir))

def folder_decompress(file_name_compress):
    tar = tarfile.open(file_name_compress)
    tar.extractall(file_dir)
    tar.close()



def eliminate_duplicated(source_set_list):
    list = []
    for name in source_set_list:
        list.append(name[0])
    name_list = set(list)
    print(name_list)
    list1 = []
    for name in name_list:
        for tuple in source_set_list:
            if name == tuple[0]:
                list1.append(tuple)
                break
    return list1


def encry(file_name, file_encrypt):
    key = '0523698741254512'
    with open(join(file_dir, file_name), 'rb') as f:
        f_in = f.read()
    print('file without encryption ', len(f_in))
    while len(f_in) % 32 != 0:
        f_in += '='.encode()
    cipher = AES.new(key.encode(), AES.MODE_ECB)
    f_out = cipher.encrypt(f_in)
    print(f' file AFTER encryption: {len(f_out)}\n')
    with open(file_encrypt, 'wb') as f:
        f.write(f_out)



def decry(file_encrypt, file_name, real_file_size):
    key = '0523698741254512'
    file_size = os.path.getsize(file_encrypt)
    print(f'\n{file_encrypt} size is {file_size}')
    with open(file_encrypt, 'rb') as f:
        f_in = f.read()
    cipher = AES.new(key.encode(), AES.MODE_ECB)
    f_out = cipher.decrypt(f_in)[0:real_file_size]
    with open(join(file_dir, file_name), 'wb') as f:
        f.write(f_out)









def file_compress(beginFile, zlibFile, level):
    start = time.time()
    with open(join(file_dir, beginFile), "rb") as infile:
        with open(zlibFile, "wb") as zfile:
            compressobj = zlib.compressobj(level)  # 压缩对象
            data = infile.read(10240)  # 10240为读取的size参数
            while data:
                zfile.write(compressobj.compress(data))  # 写入压缩数据
                data = infile.read(10240)  # 继续读取文件中的下一个size的内容
            zfile.write(compressobj.flush())  # compressobj.flush()包含剩余压缩输出的字节对象，将剩余的字节内容写入到目标文件中
    print('compress time is: ', time.time() - start)


def file_decompress(zlibFile, endFile):
    start = time.time()
    with open(zlibFile, "rb") as zlibFile:
        with open(join(file_dir, endFile), "wb") as endFile:
            decompressobj = zlib.decompressobj()
            data = zlibFile.read(10240)
            while data:
                endFile.write(decompressobj.decompress(data))
                data = zlibFile.read(10240)
    print('decompress time is: ', time.time() - start)




