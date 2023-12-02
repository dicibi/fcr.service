import datetime
import dbtool
from typing import List
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm.session import Session
from sqlalchemy import DateTime, String, ForeignKey, func, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

    images: Mapped[List["Image"]] = relationship(back_populates="dataset")

    def __repr__(self):
        return f"Dataset(id={self.id!r}, name={self.name!r})"

class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(255))
    path: Mapped[str] = mapped_column(String(255))
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"))

    dataset: Mapped[Dataset] = relationship(back_populates="images")

    def __repr__(self) -> str:
        return f"Image( id = {self.id}, name = {self.name}, type = {self.type}, path = {self.path})"

class RecognitionModel(Base):
    __tablename__ = "recognition_models"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    path: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(255))
    task_id: Mapped[int] = mapped_column(String(255))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())

    def __repr__(self) -> str:
        return f"RecognitionModel( id = {self.id}, name = {self.name}, path = {self.path})"

def getDataset(name):
    with Session(dbtool.getEngine()) as session:
        result = session.scalars(select(Dataset).where(Dataset.name == name)).first()

        session.close()

    return result
        

def getImage(datasetId, path):
    with Session(dbtool.getEngine()) as session:
        result = session.scalars(select(Image).where(Image.dataset_id == datasetId).where(Image.path == path)).first()

        session.close()

    return result
