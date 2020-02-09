import eel
import pandas as pd
#import qdinstrument
import socket
#from Queue import Queue
from queue import Queue
from threading import Event, Lock
import random
import numpy as np
import logging
import os
from datetime import date
from pymeasure.instruments.keithley import Keithley2400

data_path = os.path.join(os.getcwd(),'data')
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('logging.log')
c_handler.setLevel(logging.DEBUG)
f_handler.setLevel(logging.INFO)

logger.addHandler(c_handler)
logger.addHandler(f_handler)

q = Queue()
cmd_q = Queue()
data_q = Queue(maxsize = 1)
halt_meas = Event()
stop = Event()
set_temperature_lock = Lock()

eel.init('web')

@eel.expose
def set_temperature_settings(setpoint,rate,mode):
    if not set_temperature_lock.locked():
        #Dyna.set_temperature(setpoint,rate,mode)
        cmd_q.put("TEMP {0},{1},{2}".format(setpoint,20,0))
        logging.info('set Temp to {0} K at {1} K/min. mode:{2}'.format(setpoint,rate,mode))
    else:
        logging.info('temperature settings is locked.')

@eel.expose
def set_magnet_settings(setpoint,rate,mode):
    if not set_temperature_lock.locked():
        #Dyna.set_field(setpoint,rate,mode,-1)
        cmd_q.put("FIELD {0},{1},{2}".format(setpoint,rate,mode))
        logging.info('set magnet to {0} oe at {1} oe/min. mode:{2}'.format(setpoint,rate,mode))
    else:
        logging.info('magnet settings is locked.')



def send_measure_data_to_page():
    logging.debug('start sending')
    while not stop.is_set():
        if not q.empty():
            value = q.get()
            T,R = value
            eel.get_RT_data(T,R)
        else:
            eel.sleep(0.5)
    logging.debug('thread is exiting.')


@eel.expose
def measure_rand():
    logging.info('start measuring')
    eel.spawn(send_measure_data_to_page)
    for i in range(100):
        meas = random.randint(0,100)
        q.put((i,meas))
        #eel.sleep(0.5)
    logging.info('end measuring')

def measure_resistance(sourcemeter):
    if True: #'mocking'
        eel.sleep(0.5)
        return random.randint(0,25)
    sourcemeter.ramp_to_current(sourcemeter.source_current)
    sourcemeter.measure_voltage()
    V_p = sourcemeter.voltage
    eel.sleep(0.1)
    sourcemeter.ramp_to_current(-sourcemeter.source_current)
    sourcemeter.measure_voltage()
    V_m = sourcemeter.voltage
    sourcemetery.ramp_to_current(0)
    return (V_p - V_m)/sourcemeter.source_current

def initialize_keithley(I,V_comp,nplc):
    if False:
        sourcemeter = Keithley2400("GPIB::4")
        sourcemeter.reset()
        sourcemeter.use_front_terminals()
        sourcemeter.apply_current()
        sourcemeter.compliance_voltage = V_comp
        sourcemeter.measure_voltage(nplc=nplc, voltage=21.0, auto_range=True)
        sourcemeter.source_current = I
        sleep(0.1)
        return sourcemeter
    pass


def initialize_file(file_name):
    path = os.path.join(data_path,file_name+'_'+date.today().strftime('%d_%m_%Y'))
    logging.debug('path is {}'.format(path))
    if not os.path.exists(path):
        os.mkdir(path)
        logging.debug('created folder for file.')
    file_path = os.path.join(path,"RT.csv")
    i=1
    while os.path.exists(file_path):
        file_path = os.path.join(path,"RT"+str(i)+".csv")
        i = i +1
    pd.DataFrame(columns = ['time','Temperature[k]','Resistance[Ohm]']).to_csv(file_path)
    return file_path

@eel.expose
def halt_measurement():
    logging.info('sending stop command.')
    halt_meas.set()

@eel.expose
def start_RT_sequence(start_temp,end_temp,rate,I,V_comp,nplc,sample_name):
    eel.toggle_start_measure()
    breaked = False
    set_temperature_lock.acquire()
    stop.clear()
    halt_meas.clear()
    file_name = initialize_file(sample_name)
    keithley = initialize_keithley(I,V_comp,nplc) # return keith object
    logging.info('start RT measurement.')
    eel.spawn(send_measure_data_to_page)
    #Dyna.set_temperature(start_temp,20,0) #go to start, 20 K/min, Fast settle
    cmd_q.put("TEMP{0},{1},{2}".format(start_temp,20,0))
    while data_q.
    eel.set_meas_status('waiting for temperature.')
    logging.info('set Temperature and wait')
    error,Temp,status = Dyna.get_temperature()
    while status != 1 and status != 5: #add timeout
        if halt_meas.is_set():
            logging.info('stoped measurement.')
            eel.set_meas_status('measurement stoped.')
            set_temperature_lock.release()
            stop.set()
            halt_meas.clear()
            eel.toggle_start_measure()
            return False
        #print(status)
        error,Temp,status = Dyna.get_temperature()
        eel.sleep(1)
    if (Temp != start_temp):
        logging.warning('start temp not achieved. current temp: {0}'.format(Temp))
    #Dyna.set_temperature(end_temp,rate,0) #go to end, in rate, Fast settle
    cmd_q.put("TEMP {0},{1},{2}".format(end_temp,rate,0))
    error,Temp,status = Dyna.get_temperature()
    while status == 1:
        #wait for start of movement
        logging.info('waiting')
        error,Temp,status = Dyna.get_temperature()
    logging.info('start measure')
    eel.set_meas_status('start measurement.')
    error,Temp,status = Dyna.get_temperature()
    while status == 2 or status == 5: #tracking, going in defined rate.
        ##measuring
        error,Temp,status = Dyna.get_temperature()
        #Time = Dyna.get_timestamp()
        Time = 0
        R = measure_resistance(keithley)
        new_row = pd.DataFrame({'Time':[Time],'Temperature[k]':[Temp],'Resistance[Ohm]':[R]}).to_csv(file_name, mode='a', header=False,columns = ['time','Temperature[k]','Resistance[Ohm]']) #maybe keep file open?
        del new_row
        q.put((Temp,R))
        if halt_meas.is_set():
            logging.warning('stoped measurement.')
            eel.set_meas_status('measurement stopped.')
            breaked = True
            break

        if np.abs(Temp - float(end_temp)) < 0.01:
            break

    if not breaked:
        eel.set_meas_status('reached end Temperature.')
        logging.info('reached end Temperature.')
    if False: #mocking
        keithley.shutdown()
    set_temperature_lock.release()
    halt_meas.clear()
    eel.toggle_start_measure()
    stop.set() #kill thread

def QD_socket(HOST='localhost',PORT=5000):
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    logging.info('Attempt connect to server.')
    try:
        s.connect((HOST,PORT))
        logging.info('connected to server.')
        eel.change_connection_ind(True)
        while True:
            if not cmd_q.empty():
                command = cmd_q.get()
                s.sendall(bytes(command,'utf-8'))
                data = s.recv(1024)
                #if data != b'0\r\n':
                #    logging.error('error Recived from QD server, ' + data.decode())
                #    eel.change_connection_ind(False)
                #print('Recived: ', data.decode())11
                data_q.put(data)
            eel.sleep(0.5)
            pass
        s.send(b'disconnect')
        s.close()
    #except Exception as e:
    #    print(e)
    except WindowsError:
        eel.change_connection_ind(False)
        logging.info('Connection to server failed.')



eel.spawn(QD_socket)
#cmd_q.put('TEMP?')

#Dyna = qdinstrument.QDInstrument('DYNACOOL')
try:
    eel.start('index.html')
except (SystemExit, MemoryError, KeyboardInterrupt):
    # But if we don't catch these safely, the script will crash
    pass


## Set temperture everywhere and update on request.
