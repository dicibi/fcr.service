import os
import model
import dbtool
import train
from sqlalchemy.orm.session import Session
from sqlalchemy import text

def initializeDatabase():
    print("initialize database")
    model.Base.metadata.create_all(dbtool.getEngine())

def seedDatabase():
    print("Seeding database using dataset")
    directoryPath = 'dataset'

    for folder in os.listdir(directoryPath):
        images = os.listdir(directoryPath + '/' + folder)

        retrievedDataset = model.getDataset(folder)

        if retrievedDataset is None:
            with Session(dbtool.getEngine()) as session:
                data = model.Dataset(name = folder)

                session.add(data)

                session.commit()

                retrievedDataset = model.getDataset(folder)

                session.close()

        retrievedDataset = model.getDataset(folder)

        for image in images:
            fullPath = directoryPath  + '/' + folder + '/' + image

            retrievedImage = model.getImage(
                datasetId=retrievedDataset.id,
                path=fullPath
            )

            if retrievedImage is None:
                with Session(dbtool.getEngine()) as session:
                    data = model.Image(
                        name = image,
                        type = image.split(".")[1],
                        path = fullPath,
                        dataset_id = retrievedDataset.id
                    )

                    session.add(data)

                    session.commit()

                    session.close()
    train.run()

def isAnyTableExists():
    with Session(dbtool.getEngine()) as session:
        result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='datasets'")).first()

        session.close()

    return result is not None

def initDatabase():
    if not isAnyTableExists():
        initializeDatabase()
        seedDatabase()
    else:
        print("Database already initialized")

if  __name__ == '__main__':
    initializeDatabase()
    seedDatabase()
    
