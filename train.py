import model
import dbtool
from ulid import ULID
from recognition_tool import train
from sqlalchemy.orm.session import Session

def run():
    print("Train model")

    modelPath = 'models/' + str(ULID()) + '.clf'

    train('dataset', model_save_path=modelPath, n_neighbors=2)

    with Session(dbtool.getEngine()) as session:
        data = model.RecognitionModel(
            name=modelPath.split('/')[1],
            path=modelPath
        )

        session.add(data)

        session.commit()

        session.close()

if  __name__ == '__main__':
    run()
