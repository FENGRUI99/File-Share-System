# coding=utf-8
import multiprocessing as mp
from multiprocessing import Process
from Downloader import *
from Function import _argparse
from Listener import *
from Scanner import *

listener_port = 20006
file_dir = join(os.getcwd(), 'share')


def main():
    global listener_port
    parser = _argparse()
    IP = parser.path.split(',')[0]
    IP1 = parser.path.split(',')[1]
    isEncrypt = parser.encrypt
    print(isEncrypt, type(isEncrypt))
    download_list = mp.Manager().list([])
    file_header_dic = mp.Manager().dict({})
    # Breakpoint continuingly
    # When you start the program, you first read from the JSON file that you didn't have time to download last time
    if os.path.isfile('download_list.log'):
        with open('download_list.log', 'r') as f:
            list = json.load(f)
        for p in list:
            download_list.append(tuple(p))

    file_scanner_process = Thread(target=file_scanner, args=(IP, IP1, listener_port, file_header_dic, download_list))
    file_scanner_process.daemon = True
    file_scanner_process.start()
    downloader_process = Thread(target=downloader, args=(listener_port, download_list, isEncrypt))
    downloader_process.daemon = True
    downloader_process.start()
    listener_process = Thread(target=listener, args=(listener_port, file_header_dic, download_list, isEncrypt))
    listener_process.daemon = True
    listener_process.start()
    file_scanner_process.join()
    downloader_process.join()
    listener_process.join()


if __name__ == '__main__':
    main()
