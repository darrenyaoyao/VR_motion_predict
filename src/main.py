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
        # for i in range(result.shape[0]):
        #     for j in range(result.shape[1]):
        #         bytes_to_send += struct.pack('<f', float(result[i,j]))
        
        for i in range(25):
            for j in range(18):
                bytes_to_send+=struct.pack('<f', result[i][j])
        


        s.sendall(bytes_to_send) #sending back
    except Exception as e:
        logging.error(traceback.format_exc())
        print("sending result error!")
        

# class MLService(threading.Thread):
#     def __init__(self,s,queue_map,model):
#         threading.Thread.__init__(self,name="mlservice")
#         self.s=s
#         self.queue_map = queue_map
#         self.model=model
#         self.doRun= True
    
#     def run(self):
#         print("ML running!!\n")
#         while self.doRun:
#             if(len(self.queue_map)==2):
#                 for _id,queue in self.queue_map.items():
#                     print("ml _id: ",_id,", length: ",len(queue))
#                     if len(queue)==100:
#                         print("full!!!!!!!!!!!")
#                         poses = np.array(queue)
#                         # start_time = time.time()
#                         result = self.model.sample(poses)
#                         # end_time = time.time()
#                         # header = [end_time-start_time]
                        
#                         # print(result.shape)
#                         sending(self.s,_id,result)

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

    

    print('socket listensing ... ')
    while True: # for connect multiple times
        try:
            
            conn, addr = s.accept()
            print(addr[0] + 'connect!!')

            # mlservice = MLService(conn,queue_map,model)
            # mlservice.start()
            #handle one client!!
            while True:
                try:
                    # health_check(conn)

                    _id, input_pose = receivepacket(conn)
                    print("Input ")
                    print(_id)
                    print(input_pose)
                    if _id not in queue_map.keys():
                        queue_map[_id]=[]
                        
                    data_ = queue_map[_id]
                        
                    if(len(data_)==100):
                        data_[0:99] = data_[1:100]
                        data_[99] = input_pose
                    else:
                        data_.append(input_pose)
                    
                    # 改到這確認不是thread的問題
                    queue = queue_map[_id]
                        
                    if len(queue)==100:
                           
                        poses = np.array(queue)
                            # start_time = time.time()
                        result = model.sample(poses)
                            # end_time = time.time()
                            # header = [end_time-start_time]
                            
                            # # print(result.shape)
                            # print("Output")
                            # print(_id)
                            # print(result[0])
                        sending(conn,_id,result)



                except Exception as e:
                    logging.error(traceback.format_exc())
                    queue_map.clear()
                    break

            #end of handle client
            # mlservice.doRun=False
            # mlservice.join()

        except socket.timeout:
            pass


