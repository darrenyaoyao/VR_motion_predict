import socket
import struct
import traceback
import logging
import time
import numpy as np
import queue
import random,threading,time
from translate import pose_predict

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port = 60000
s.connect(("192.168.50.14", port))
print('socket created ')

print('socket listensing ... ')



# def kinect_transform_to_model(poses):
#     new_pose = np.zeros((poses.shape[0],poses.shape[1]+3))

#     # base
#     new_pose[:,0:3] = poses[:,0:3]
#     # left leg
#     new_pose[:,3:12] = poses[:,54:63]
#     new_pose[:,12:15] = poses[:,63:66]
#     new_pose[:,15:18] = poses[:,63:66]

#     # right leg
#     new_pose[:,18:27] = poses[:,66:75]
#     new_pose[:,27:30] = poses[:,75:78]
#     new_pose[:,30:33] = poses[:,75:78]

#     #spine
#     new_pose[:,33:42] = poses[:,3:12]
    
#     # head
#     new_pose[:,42:48] = poses[:,78:84]

#     # left arm
#     new_pose[:,48:69] = poses[:,12:33]
#     new_pose[:,69:72] = poses[:,27:30]

#     # right arm
#     new_pose[:,72:93] = poses[:,33:54]
#     new_pose[:,93:96] = poses[:,48:51]

#     return new_pose

# def model_transform_to_kinect(poses):
#     new_pose = np.zeros((poses.shape[0],poses.shape[1]-3))

#     #base
#     new_pose[:,0:3] = poses[:,0:3]

#     #spine
#     new_pose[:,3:12] = poses[:,33:42]

#     # left arm
#     new_pose[:,12:33] = poses[:,48:69]
#     # new_pose[:,27:30] = poses[:,69:72]

#     # right arm
#     new_pose[:,33:54] = poses[:,72:93]
#     # new_pose[:,48:51] = poses[:,93:96]

#     # left leg
#     new_pose[:,54:66] = poses[:,3:15]
#     # new_pose[:,63:66] = poses[:,12:15]
   
#     # right leg
#     new_pose[:,66:75] = poses[:,18:27]
#     # new_pose[:,75:78] = poses[:,27:30]

#     # head
#     new_pose[:,78:84] = poses[:,42:48]

    
def reciveing():
    
    try:
        bytes_received = s.recv(388)
        pose_received = bytes_received[0:384]
        array_received = np.frombuffer(pose_received, dtype=np.float32) #converting into float array
        return array_received
        # print(array_received.shape)
        # input_pose = np.vstack((input_pose,array_received))
        # input_pose = transform(input_pose)
        
    except Exception as e:
        logging.error(traceback.format_exc())
        print("error")
        
        

def sending(result):
    print("sending result")
    try:
        bytes_to_send = struct.pack('%sf' % len(result), *result) #converting float to byte
        s.sendall(bytes_to_send) #sending back
    except Exception as e:
        print("sending result error!")
        

class Producer(threading.Thread):
    def __init__(self,t_name,data):
        threading.Thread.__init__(self,name=t_name)
        self.data =data
    
    def run(self):
        while 1 :
            input_pose = reciveing()
            if(len(self.data)==102):
                self.data[0:101] = self.data[1:102]
                self.data[101] = input_pose
            else:
                self.data.append(input_pose)

"""
q = []

model = pose_predict()
producer = Producer("get.",q)
producer.start()

while 1 :
    if(len(q)==102):
        poses = q
        poses = np.array(poses)
        poses = kinect_transform_to_model(poses)

        result = model.sample(poses)
        result = model_transform_to_kinect(result)
        result = model(input_pose)
        
        sending(result)
        
    else:
        continue


"""
import csv
import pandas as pd

save = open("test.csv", mode="w", newline="")
writer = csv.writer(save)

input_pose = np.zeros((100,99))

data = pd.read_csv('IRL_0_pose_4.csv', encoding = 'big5',header = None, dtype = np.float32)
data = data.to_numpy()
data = data[:,0:-1]

input_pose[:,0:96] = data[0:100,:]

header = ["ground"]
writer.writerow(header)
for idx,i in enumerate(data[100:110,:]):
    if(idx%2 ==0):
        writer.writerow(i)

model = pose_predict()

result = model.sample(input_pose)
header = ["predict"]
writer.writerow(header)
for i in result:
    writer.writerow(i)



