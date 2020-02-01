import eel
import pandas as pd
import qdinstrument
#from Queue import Queue
from queue import Queue
from threading import Event, Lock
import random
import numpy as np
import logging
import os
from datetime import date


data_path = os.path.join(os.getcwd(),'data')
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('logging.log')
c_handler.setLevel(logging.DEBUG)
f_handler.setLevel(logging.WARNING)

logger.addHandler(c_handler)
logger.addHandler(f_handler)

q = Queue()
halt_meas = Event()
stop = Event()
set_temperature_lock = Lock()

eel.init('web')

@eel.expose
def set_temperature_settings(setpoint,rate,mode):
    if not set_temperature_lock.locked():
        Dyna.set_temperature(setpoint,rate,mode)
        logging.info('set Temp to {0} K at {1} K/min. mode:{2}'.format(setpoint,rate,mode))
    else:
        logging.info('temperature settings is locked.')

@eel.expose
def set_magnet_settings(setpoint,rate,mode):
    if not set_temperature_lock.locked():
        Dyna.set_field(setpoint,rate,mode,-1)
        logging.info('set magnet to {0} oe at {1} oe/min. mode:{2}'.format(setpoint,rate,mode))
    else:
        logging.info('magnet settings is locked.')


def send_measure_data_to_page():
    i=0
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

def measure_resistance():
    ##GPIB Stuff
    eel.sleep(0.5)
    return random.randint(0,25)

def initialize_keithley(I,V_comp,nplc):
    #return keithly object
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
    initialize_keithley(I,V_comp,nplc) # return keith object
    logging.info('start RT measurement.')

    eel.spawn(send_measure_data_to_page)
    Dyna.set_temperature(start_temp,20,0) #go to start, 20 K/min, Fast settle
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
    Dyna.set_temperature(end_temp,rate,0) #go to end, in rate, Fast settle
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
        R = measure_resistance()
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
    set_temperature_lock.release()
    halt_meas.clear()
    eel.toggle_start_measure()
    stop.set() #kill thread


Dyna = qdinstrument.QDInstrument('DYNACOOL')
eel.start('index.html')
