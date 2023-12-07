import os
import model
from datetime import datetime

MODEL_FOLDER = 'models'

def seedDatabase():
    print("Seeding database using dataset")
    directoryPath = 'dataset'

    for folder in os.listdir(directoryPath):
        images = os.listdir(directoryPath + '/' + folder)

        dataset = model.findDataset(folder)

        if dataset is None:
            newDataset = model.Dataset(
                name=folder
            )

            newDataset.save()

        dataset = model.findDataset(folder)

        for image in images:
            fullPath = directoryPath  + '/' + folder + '/' + image

            imageModel = model.findImage(fullPath)

            if imageModel is None:
                model.Image(
                    name=image,
                    image_type=image.split(".")[1],
                    path=fullPath,
                    dataset_id=dataset.pk,
                ).save()

    validateRecognitionModels()

def validateRecognitionModels():
    for filename in os.listdir(MODEL_FOLDER):
        if 'clf' in filename:
            path = 'models/' + filename

            relatedModel = model.findRecognitionModel(path)

            if relatedModel:
                continue

            model.RecognitionModel(
                name=filename,
                path=path,
                status="SUCCESS",
                created_at=datetime.now(),
            ).save()

if  __name__ == '__main__':
    seedDatabase()
