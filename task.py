import os

import model
from celery import Celery
from recognition_tool import train, rotate, predict
import model
import redis
import json

celery = Celery('fcr')
celery.conf.broker_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
celery.conf.result_backend = os.getenv('REDIS_URL', 'redis://redis:6379/0')

redis_connection = redis.from_url(os.getenv('REDIS_URL', 'redis://redis:6379/0'))

@celery.task(name="train_model")
def trainModelRunner(modelPath):
    train('dataset', model_save_path=modelPath, n_neighbors=2)

    newModel = model.findRecognitionModel(modelPath)

    if newModel is None:
        print("MODEL NOT FOUND")
    else:
        newModel.status = 'SUCCESS'
        newModel.save()

    return True

@celery.task(name="verify")
def verify(image_path, identifier, publish_to, carrier = None):
    rotate(image_path)

    latestModel = model.getLatestModel()

    if latestModel is None:
        return True

    prediction = predict(image_path, model_path=latestModel.path)

    if len(prediction) == 0:
        response = {
            'name': None,
            'location': None,
            'code': 200,
            'model': latestModel.name,
            'message': "invalid",
            'carrier': carrier
        }
    else:
        response = {
            'name': prediction['name'],
            'location': prediction['location'],
            'code': 200,
            'model': latestModel.name,
            'message': "detected",
            'carrier': carrier
        }

    if identifier == response['name']:
        response['message'] = "valid"

    redis_connection.publish(publish_to, json.dumps(response))

    os.remove(image_path)

    return True