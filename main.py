import eel
import pandas as pd
import qdinstrument
#from Queue import Queue
from queue import Queue
from threading import Event
import random
q = Queue()


eel.init('web')

@eel.expose
def set_temperature_settings(setpoint,rate,mode):
    Dyna.set_temperature(setpoint,rate,mode)
    pass



def send_measure_data_to_page(stop_event):
    i=0
    print('start sending')
    while not stop_event.is_set():
        if not q.empty():
            value = q.get()
            T,R = value
            eel.get_RT_data(T,R)
        else:
            eel.sleep(0.5)
    print('thread is exiting.')


@eel.expose
def measure_rand():
    print('start measuring')
    eel.spawn(send_measure_data_to_page)
    for i in range(100):
        meas = random.randint(0,100)
        q.put((i,meas))
        #eel.sleep(0.5)
    print('end measuring')

def measure_resistance():
    ##GPIB Stuff
    eel.sleep(0.5)
    return random.randint(0,25)

def initialize_keithley(I,V_comp,nplc):
    #return keithly object
    pass


def initialize_file(file_name):
    #initial csv file
    #check if file exists, add 1 if yes
    #create pandas def
    #save to csv
    #delete file
    #return new file name
    pd.DataFrame(columns = ['time','Temperature[k]','Resistance[Ohm]']).to_csv(file_name)
    return file_name

@eel.expose
def start_RT_sequence(start_temp,end_temp,rate,I,V_comp,nplc,file_name):
    stop = Event()
    new_file_name = initialize_file(file_name)
    initialize_keithley(I,V_comp,nplc) # return keith object
    print('start RT measurement.')
    eel.spawn(send_measure_data_to_page, stop)
    Dyna.set_temperature(start_temp,20,0) #go to start, 20 K/min, Fast settle
    print('set Temperature and wait')
    error,Temp,status = Dyna.get_temperature()
    while status != 1 and status != 5: #add timeout
        #print(status)
        error,Temp,status = Dyna.get_temperature()
        eel.sleep(1)
    if (Temp != start_temp):
        print('start temp not achieved')
    Dyna.set_temperature(end_temp,rate,0) #go to end, in rate, Fast settle
    error,Temp,status = Dyna.get_temperature()
    while status == 1:
        #wait for start of movement
        print('waiting')
        error,Temp,status = Dyna.get_temperature()
    print('start measure')
    error,Temp,status = Dyna.get_temperature()
    while status == 2 or status == 5: #tracking, going in defined rate.
        ##measuring
        error,Temp,status = Dyna.get_temperature()
        #Time = Dyna.get_timestamp()
        Time = 0
        R = measure_resistance()
        new_row = pd.DataFrame({'Time':[Time],'Temperature[k]':[Temp],'Resistance[Ohm]':[R]})
        new_row.to_csv(new_file_name, mode='a', header=False,columns = ['time','Temperature[k]','Resistance[Ohm]']) #maybe keep file open?
        del new_row
        q.put((Temp,R))
    print('reached end Temperature.')
    stop.set() #kill thread


Dyna = qdinstrument.QDInstrument('DYNACOOL')
eel.start('index.html')
