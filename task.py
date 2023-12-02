from celery import Celery
from recognition_tool import train
from sqlalchemy.orm.session import Session
import model
import dbtool

celery = Celery('fcr')
celery.conf.broker_url = "redis://localhost:6379"
celery.conf.result_backend = "redis://localhost:6379"

@celery.task(name="train_model")
def trainModelRunner(modelPath):
    train('dataset', model_save_path=modelPath, n_neighbors=2)

    with Session(dbtool.getEngine()) as session:
        modelToUpdate = session.query(model.RecognitionModel).filter(model.RecognitionModel.path == modelPath).first()

        if modelToUpdate:
            modelToUpdate.status = 'SUCCESS'
            session.commit()


    return True

