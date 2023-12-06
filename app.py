from datetime import datetime
import os
from celery.result import AsyncResult
from werkzeug.utils import secure_filename
import model as BaseModel
import math
from flask import Flask, jsonify, request
from flask_cors import CORS
from recognition_tool import predict
from task import trainModelRunner
from ulid import ULID
from db import seedDatabase

app = Flask(__name__)

UPLOAD_FOLDER = 'dataset'
TEMPORARY_FOLDER = 'temporary'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMPORARY_FOLDER'] = TEMPORARY_FOLDER

CORS(app)

seedDatabase()

@app.route('/api/dataset/', strict_slashes=False,)
def getDataset():
    data = request.args

    currentPath = request.path

    limit = 10
    pageNumber = int(data.get('page', 1))
    offset = (pageNumber - 1) * limit

    datasets = BaseModel.Dataset.find().page(offset, limit)

    datasetDict = []

    for dataset in datasets:
        data = {
            'id': dataset.pk,
            'name': dataset.name,
            'image_count': BaseModel.getDatasetImageTotal(dataset.pk)
        }

        datasetDict.append(data)

    totalDataset = BaseModel.Dataset.find().count()

    pagination = getPaginationUrl(currentPath, total=totalDataset, currentPage=pageNumber)

    response = {
        'code': 200,
        'data': datasetDict,
        'total': totalDataset,
        'current_page': pageNumber,
        'current_page_total': len(datasetDict)
    }

    return jsonify(**response, **pagination)

@app.route('/api/upload', methods=['POST'])
def uploadFile():
    if 'identifier' not in request.form:
        return jsonResponse(code=422, message="Identifier not found!")

    if 'file' not in request.files:
        return jsonResponse(code=422, message="File not found!")

    file = request.files['file']

    response = {
        'code': 200,
        'message': 'SUCCESS',
    }

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        folder = request.form['identifier']

        path = app.config['UPLOAD_FOLDER'] + '/' + folder

        dataset = BaseModel.findDataset(folder)

        if not os.path.exists(path) and dataset:
            os.makedirs(path)
        elif os.path.exists(path) and dataset is None:
            newDataset = BaseModel.Dataset(
                name=folder
            )

            newDataset.save()

            dataset = BaseModel.findDataset(folder)
        elif not os.path.exists(path) and dataset is None:
            newDataset = BaseModel.Dataset(
                name=folder
            )

            newDataset.save()

            os.makedirs(path)

            dataset = BaseModel.findDataset(folder)

        filepath = os.path.join(path, filename)

        image = BaseModel.findImage(filepath)

        if os.path.exists(filepath) and image is None:
            newModel = BaseModel.Image(
                name=filename,
                image_type=filename.split(".")[1],
                path=filepath,
                dataset_id=dataset.pk,
            )

            newModel.save()
        elif not os.path.exists(filepath) and image:
            file.save(filepath)
        elif not os.path.exists(filepath) and image is None:
            newModel = BaseModel.Image(
                name=filename,
                image_type=filename.split(".")[1],
                path=filepath,
                dataset_id=dataset.pk,
            )

            newModel.save()

            file.save(filepath)
        else:
            response['code'] = 422
            response['message'] = 'Image exists'

    return jsonify(response)


@app.route('/api/verify', methods=['POST'])
def storeImage():
    if 'file' not in request.files:
        return jsonResponse(code=422, message="File is empty!")

    file = request.files['file']

    if file.filename == '':
        return jsonResponse(code=422, message="File is empty!")

    response = {
        'code': 400,
        'message': 'Something wrong! Please try again!'
    }

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['TEMPORARY_FOLDER'], filename)
        file.save(filepath)

        latestModel = getLatestModel()

        if latestModel is None:
            return jsonify(response)

        prediction = predict(filepath, model_path=latestModel.path)

        if len(prediction) == 0:
            response = {
                'name': None,
                'location': None,
                'code': 200,
                'model': latestModel.name,
                'message': None
            }
        else:
            response = {
                'name': prediction['name'],
                'location': prediction['location'],
                'code': 200,
                'model': latestModel.name,
                'message': "SUCCESS"
            }

        os.remove(filepath)

    return jsonify(response)

@app.route('/api/models', methods={'GET'})
def getModels():
    data = request.args

    currentPath = request.path

    limit = 10
    pageNumber = int(data.get('page', 1))
    offset = (pageNumber - 1) * limit

    models = BaseModel.RecognitionModel.find().sort_by('-created_at').page(offset, limit)

    modelDict = []

    for model in models:
        if model.status == 'PENDING':
            updateModelStatus(model.task_id)

        data = {
            'id': model.pk,
            'name': model.name,
            'status': model.status,
            'task_id': model.task_id,
            'created_at': model.created_at,
        }

        modelDict.append(data)

    totalModel = BaseModel.RecognitionModel.find().count()

    pagination = getPaginationUrl(currentPath, total=totalModel, currentPage=pageNumber)

    response = {
        'code': 200,
        'data': modelDict,
        'total': totalModel,
        'current_page': pageNumber,
        'current_page_total': len(modelDict)
    }

    return jsonify(**response, **pagination)

@app.route('/api/models/train', methods=['POST'])
def trainModel():
    modelPath = 'models/' + str(ULID()) + '.clf'

    task = trainModelRunner.delay(modelPath)

    newModel = BaseModel.RecognitionModel(
        name=modelPath.split('/')[1],
        path=modelPath,
        status="PENDING",
        task_id=task.id,
        created_at=datetime.now(),
    )

    newModel.save()

    return jsonify({
        'code': 200,
        'task_id': task.id
    })

@app.route('/api/models/train/<taskId>', methods=['GET'])
def getTrainModelStatus(taskId):
    task_result = AsyncResult(taskId)

    result = {
        "task_id": taskId,
        "task_status": task_result.status,
        "task_result": task_result.result
    }

    updateModelStatus(taskId)

    trainedModel = BaseModel.RecognitionModel.find(BaseModel.RecognitionModel.task_id == taskId).first()

    result['name'] = trainedModel.name
    result['status'] = trainedModel.status

    return jsonify(result), 200


def updateModelStatus(taskId):
    trainedModel = BaseModel.RecognitionModel.find(BaseModel.RecognitionModel.task_id == taskId).first()

    if os.path.exists(trainedModel.path):
        trainedModel.status = 'SUCCESS'
        trainedModel.save()


def getLatestModel():
    return BaseModel.getLatestModel()

def jsonResponse(code = 200, message = "SUCCESS"):
    return jsonify({
        'code': code,
        'message': message
    })

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def getPaginationUrl(path, total, currentPage):
    data = {}

    for key in ['first', 'last', 'prev', 'next']:
        if key == 'first':
            data['first_page_url'] = path + '?page=1'
        elif key == 'last':
            data['last_page_url'] = path + '?page=' + str(math.ceil(total / 10))
        elif key == 'next':
            if total - (currentPage * 10) > 0:
                data['next_page_url'] = path + '?page=' + str(currentPage + 1)                
            else:
                data['next_page_url'] = None
        else:
            if currentPage > 1:
                data['prev_page_url'] = path + '?page=' + str(currentPage - 1)
            else:
                data['prev_page_url'] = None

    return data

if __name__ == '__main__':
    app.run(debug=False)
