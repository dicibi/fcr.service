import model
from ulid import ULID
from datetime import datetime
from task import trainModelRunner

def run():
    print("Train model")

    modelPath = 'models/' + str(ULID()) + '.clf'

    task = trainModelRunner.delay(modelPath)

    model.RecognitionModel(
        name=modelPath.split('/')[1],
        path=modelPath,
        status="PENDING",
        task_id=task.id,
        created_at=datetime.now(),
    ).save()

if  __name__ == '__main__':
    run()
