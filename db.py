import os
import model

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

if  __name__ == '__main__':
    seedDatabase()
