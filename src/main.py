import select
import socket
import struct
import traceback
import logging
import time
import numpy as np
import queue
import random,threading,time
from translate import pose_predict
import csv
import time

def health_check(s):
    readable,writeable,err = select.select([s],[s],[s],0)
    if len(readable)<1 or len(writeable)<1 or len(err)>0: 
        raise socket.error("discon")

def getbytes(s,num):
    recv_num=0
    recv_data=b""
    while recv_num<num:
        data = s.recv(num-recv_num)
        recv_num += len(data)
        recv_data += data
    return recv_data


def receivepacket(s):
    try:
        bytes_received = getbytes(s,76)
        _id = struct.unpack('<I', bytes_received[:4])[0]
        pose = np.frombuffer(bytes_received[4:], dtype=np.float32) #converting into float array
        return _id,pose
    except Exception as e:
        print("receiving packet error!")
        

def sending(s,_id,result):
    try:
        bytes_to_send=struct.pack('<I', _id)
        
        for i in range(25):
            for j in range(18):
                bytes_to_send+=struct.pack('<f', result[i][j])

        s.sendall(bytes_to_send) #sending back
    except Exception as e:
        logging.error(traceback.format_exc())
        print("sending result error!")

def interpolation(data_queue, time_queue):
    interpolated_data_queue = []
    for i in range(len(data_queue)):
        if i != 0 and (time_queue[i] - time_queue[i-1]) > 40:
            interpolated_data_queue.append((data_queue[i]+data_queue[i-1])/2)
        interpolated_data_queue.append(data_queue[i])
    return interpolated_data_queue
        

class MLService(threading.Thread):
    def __init__(self, s, queue_map, queue_time_map, model):
        threading.Thread.__init__(self,name="mlservice")
        self.s=s
        self.queue_map = queue_map
        self.queue_time_map = queue_time_map
        self.model = model
        self.doRun = True
    
    def run(self):
        print("ML running!!\n")
        while self.doRun:
            if(len(self.queue_map)==2):
                for _id,queue in self.queue_map.items():
                    print("ml _id: ",_id,", length: ",len(queue))
                    interpolated_data_queue = interpolation(queue_map,queue_time_map)
                    if len(interpolated_data_queue)==100:
                        poses = np.array(interpolated_data_queue)
                        result = self.model.sample(poses)
                        sending(self.s,_id,result)

if __name__=="__main__":
    # create  model
    model = pose_predict()
    # create socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.bind(("127.0.0.1", 60000))
    print('socket created ')
    s.listen()

    queue_map = {}
    queue_time_map = {}

    print('socket listensing ... ')
    while True: # for connect multiple times
        try:
            
            conn, addr = s.accept()
            print(addr[0] + 'connect!!')

            mlservice = MLService(conn,queue_map,queue_time_map,model)
            mlservice.start()
            #handle one client!!
            while True:
                try:
                    # health_check(conn)

                    _id, input_pose = receivepacket(conn)
                    print("Input ")
                    print(_id)
                    if _id not in queue_map.keys():
                        queue_map[_id]=[]
                        
                    data_ = queue_map[_id]
                        
                    if(len(data_)==100):
                        data_[0:99] = data_[1:100]
                        data_[99] = input_pose
                    else:
                        data_.append(input_pose)

                    if _id not in queue_time_map.keys():
                        queue_time_map[_id]=[]
                        
                    time_data_ = queue_time_map[_id]
                        
                    if(len(time_data_)==100):
                        time_data_[0:99] = time_data_[1:100]
                        time_data_[99] = int(round(time.time() * 1000))
                    else:
                        time_data_.append(int(round(time.time() * 1000)))


                except Exception as e:
                    logging.error(traceback.format_exc())
                    queue_map.clear()
                    break

            #end of handle client
            mlservice.doRun=False
            mlservice.join()

        except socket.timeout:
            pass