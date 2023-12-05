import model
from celery import Celery
from recognition_tool import train

celery = Celery('fcr')
celery.conf.broker_url = "redis://localhost:6379"
celery.conf.result_backend = "redis://localhost:6379"

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

