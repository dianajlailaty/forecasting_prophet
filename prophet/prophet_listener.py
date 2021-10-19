import messaging
import morphemic
import prophet_forecaster
from time import time
import logging
import signal
import threading
import numpy as np

# Libraries required for training and prediction
import os
import json
import pickle
import ast
from time import sleep
from dataset_maker import CSVData
from multiprocessing import Process


APP_NAME = os.environ.get("APP_NAME")
ACTIVEMQ_USER = os.environ.get("ACTIVEMQ_USER")
ACTIVEMQ_PASSWORD = os.environ.get("ACTIVEMQ_PASSWORD")
ACTIVEMQ_HOSTNAME = os.environ.get("ACTIVEMQ_HOSTNAME")
ACTIVEMQ_PORT = os.environ.get("ACTIVEMQ_PORT")

predictionTimes = dict()
models = dict()
#flags = {'avgResponseTime':0 , 'memory': 0}
metrics_processes=dict()
metrics = set()
directory_path = "/morphemic_project/prophet/"

def worker(self,body,metric):

    timestamp = body['timestamp']
    prediction_horizon = body["prediction_horizon"]
    number_of_forward_predictions = body["number_of_forward_predictions"]   
    epoch_start= body["epoch_start"]
    predictionTimes[metric] = epoch_start
    messages=list()
    f=0
    if  os.path.isfile(directory_path+'models/prophet_'+metric+".pkl"):  
        logging.debug("Loading the trained model for metric: " + metric)

    while(True):
        #if flags[metric] == 0:
            #epoch_start = predictionTimes[metric]
            #flags[metric] = 1
            #load the model
        with open(directory_path+"models/prophet_"+metric+".pkl", 'rb') as f:
            models[metric] = pickle.load(f)
        timestamp = int(time())   
        if (timestamp >= predictionTimes[metric]):
            predictions=prophet_forecaster.predict(models[metric] , number_of_forward_predictions , prediction_horizon , epoch_start)
            yhats = predictions['yhat'].values.tolist()
            yhat_lowers = predictions['yhat_lower'].values.tolist()
            yhat_uppers = predictions['yhat_upper'].values.tolist()
            
            prediction_time= epoch_start+ prediction_horizon
           # change it to the time of the start_forecasting was sent
            
            #read probabilities file
            probs = np.load(directory_path+'prob_file.npy' , allow_pickle='TRUE').item()

            for k in range(0,len(predictions['yhat'].values.tolist())):
                yhat = yhats[k]
                yhat_lower = yhat_lowers[k]
                yhat_upper = yhat_uppers[k]
                
                #wait until epoch_start to send
                
                message = {
                    "metricValue": yhat,
                    "level": 3,
                    "timestamp": timestamp,
                    "probability": probs[metric],
                    "confidence_interval" : [yhat_lower,yhat_upper],
                    "horizon": prediction_horizon,
                    "predictionTime" : int(prediction_time), # 
                    "refersTo": "todo",
                    "cloud": "todo",
                    "provider": "todo"  
                    }
                
                
                
                self.connector.send_to_topic('intermediate_prediction.prophet.'+metric, message) 
                prediction_time=prediction_time + prediction_horizon
            epoch_start = epoch_start+ prediction_horizon
            sleep(prediction_horizon)


class Prophet(morphemic.handler.ModelHandler,messaging.listener.MorphemicListener):
    id = "prophet"
    metrics = set()

    def __init__(self):
        self._run =  False
        self.connector = messaging.morphemic.Connection(ACTIVEMQ_USER,ACTIVEMQ_PASSWORD, host=ACTIVEMQ_HOSTNAME, port=ACTIVEMQ_PORT)
        
    def run(self):
        logging.debug("setting up")
        self.connector.connect()
        self.connector.set_listener(self.id, self)
        self.connector.topic("start_forecasting.prophet", self.id)
        self.connector.topic("stop_forecasting.prophet", self.id)
        self.connector.topic("metrics_to_predict", self.id)

    def reconnect(self):
        print('Reconnecting to ActiveMQ')
        self.connector.disconnect()
        self.run()
        pass

    def on_start_forecasting_prophet(self, body):
        logging.debug("Prophet Start Forecasting the following metrics :") 
        sent_metrics = body["metrics"]
        logging.debug(sent_metrics)
        for metric in sent_metrics:
            if metric not in metrics:
                metrics.add(metric)
            #thread = threading.Thread(target=worker , args=(self, body, metric,))
            if  metric not in metrics_processes:
                metrics_processes[metric] = Process(target=worker, args=(self, body, metric,))
                metrics_processes[metric] .start()

    def on_metrics_to_predict(self, body):
        #getting data from datasetmaker
        #dataset_preprocessor = CSVData(APP_NAME,start_collection='2h')
        #dataset_preprocessor.prepare_csv()
        #logging.debug("DATASET DOWNLOADED")
        
        for r in body:
            metric = r['metric']
        #for metric in metrics:
            if not os.path.isfile(directory_path+'models/prophet_'+metric+".pkl"): 
                logging.debug("Training a Prophet model for metric : " + metric)
                model=prophet_forecaster.train(metric)
                pkl_path = directory_path+"models/prophet_"+metric+".pkl"
                with open(pkl_path, "wb") as f:
                    pickle.dump(model, f)
            metrics.add(metric)
        
        self.connector .send_to_topic("training_models",
            {

            "metrics": list(metrics),

            "forecasting_method": "Prophet",

            "timestamp": int(time())
            }   
        )

    def on_stop_forecasting_prophet(self, body):
        logging.debug("Prophet Stop Forecasting the following metrics :")
        logging.debug(body["metrics"])
        for metric in body["metrics"]:
            if metric in metrics:
                metrics_processes[metric] .terminate()
                metrics.remove(metric)
                metrics_processes.pop(metric)
        logging.debug(metrics)

    def start(self):
        logging.debug("Staring Prophet Forecaster")
        self.run()
        self._run = True 

    def on_disconnected(self):
        print('Disconnected from ActiveMQ')
        self.reconnect()
