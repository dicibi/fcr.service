import model
import dbtool
from ulid import ULID
from sqlalchemy.orm.session import Session
from task import trainModelRunner

def run():
    print("Train model")

    modelPath = 'models/' + str(ULID()) + '.clf'

    task = trainModelRunner.delay(modelPath)

    with Session(dbtool.getEngine()) as session:
        data = model.RecognitionModel(
            name=modelPath.split('/')[1],
            path=modelPath,
            status="PENDING",
            task_id=task.id
        )

        session.add(data)

        session.commit()

        session.close()

if  __name__ == '__main__':
    run()
