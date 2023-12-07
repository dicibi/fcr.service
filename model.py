import datetime
from typing import Optional
from redis_om.model.model import NotFoundError
from redis_om import (
    Field,
    HashModel,
    Migrator
)

class Dataset(HashModel):
    name: str = Field(index=True)

    def __repr__(self):
        return f"(id={self.pk!r}, name={self.name!r})"
    
class Image(HashModel):
    name: str
    image_type: str
    path: str = Field(index=True)
    dataset_id: str = Field(index=True)

    def __repr__(self) -> str:
        return f"(id = {self.pk}, name = {self.name}, type = {self.type}, path = {self.path}, dataset_id = {self.dataset_id})"


class RecognitionModel(HashModel):
    name: str
    path: str = Field(index=True)
    status: str = Field(index=True)
    task_id: Optional[str] = Field(index=True)
    created_at: datetime.datetime = Field(index=True, sortable=True)

    def __repr__(self) -> str:
        return f"(id = {self.pk}, name = {self.name}, path = {self.path}, status = {self.status}, task_id = {self.task_id}), created_at = {self.created_at}"

def findDataset(name):
    Migrator().run()

    try:
        return Dataset.find(Dataset.name == name).first()
    except NotFoundError as e:
        return None

def findImage(path):
    Migrator().run()

    try:
        return Image.find(Image.path == path).first()
    except NotFoundError as e:
        return None

def findRecognitionModel(path):
    Migrator().run()

    try:
        return RecognitionModel.find(RecognitionModel.path == path).first()
    except NotFoundError as e:
        return None

def getLatestModel():
    Migrator().run()

    try:
        return RecognitionModel.find(RecognitionModel.status == 'SUCCESS').sort_by("-created_at").first()
    except NotFoundError:
        return None

def getDatasetImageTotal(datasetId):
    Migrator().run()

    return Image.find(Image.dataset_id == datasetId).count()
