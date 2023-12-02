import os
from celery.result import AsyncResult
from sqlalchemy import desc, func
from werkzeug.utils import secure_filename
import model
import dbtool
import math
from flask import Flask, jsonify, request
from sqlalchemy.orm.session import Session
from flask_cors import CORS
from recognition_tool import predict
from db import initDatabase
from task import trainModelRunner
from ulid import ULID

app = Flask(__name__)

initDatabase()

UPLOAD_FOLDER = 'dataset'
TEMPORARY_FOLDER = 'temporary'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMPORARY_FOLDER'] = TEMPORARY_FOLDER

CORS(app)

@app.route('/api/dataset/', strict_slashes=False,)
def getDataset():
    data = request.args

    currentPath = request.path

    pageNumber = int(data.get('page', 1))
    pageSize = 10

    offset = (pageNumber - 1) * pageSize

    datasetDict = []

    with Session(dbtool.getEngine()) as session:
        query = session.query(model.Dataset, func.count(model.Image.id).label('image_count'))
        query = query.outerjoin(model.Image)
        query = query.group_by(model.Dataset)
        query = query.limit(pageSize).offset(offset)

        results = query.all()

        for result, image_count in results:
            data = {
                'id': result.id,
                'name': result.name,
                'image_count': image_count,
            }

            datasetDict.append(data)

        totalDataset = session.query(model.Dataset).count()

        session.close()

    pagination = getPaginationUrl(currentPath, total=totalDataset, currentPage=pageNumber)
    response = {'code': 200, 'data': datasetDict, 'total': totalDataset, 'current_page': pageNumber, 'current_page_total': len(datasetDict)}

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

        retrievedDataset = model.getDataset(folder)

        if retrievedDataset is None:
            with Session(dbtool.getEngine()) as session:
                data = model.Dataset(name = folder)

                session.add(data)

                session.commit()

                os.makedirs(path)

                retrievedDataset = model.getDataset(folder)

                session.close()

        filepath = os.path.join(path, filename)

        retrievedImage = model.getImage(
            datasetId=retrievedDataset.id,
            path=filepath
        )

        if retrievedImage is None:
            with Session(dbtool.getEngine()) as session:
                data = model.Image(
                    name = filename,
                    type = filename.split(".")[1],
                    path = filepath,
                    dataset_id = retrievedDataset.id
                )

                file.save(filepath)

                session.add(data)

                session.commit()

                session.close()
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
        'message': 'Something wrong!'
    }

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['TEMPORARY_FOLDER'], filename)
        file.save(filepath)

        latestModel = getLatestModel()

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
def getModel():
    data = request.args

    currentPath = request.path

    pageNumber = int(data.get('page', 1))
    pageSize = 10

    offset = (pageNumber - 1) * pageSize

    modelDict = []

    with Session(dbtool.getEngine()) as session:
        query = session.query(model.RecognitionModel)
        query = query.order_by(desc(model.RecognitionModel.created_at))
        query = query.limit(pageSize).offset(offset)

        results = query.all()

        for result in results:
            data = {
                'id': result.id,
                'name': result.name,
                'status': result.status,
                'task_id': result.task_id,
                'created_at': result.created_at,
            }

            modelDict.append(data)

        totalModel = session.query(model.RecognitionModel).count()

        session.close()

    pagination = getPaginationUrl(currentPath, total=totalModel, currentPage=pageNumber)
    response = {'code': 200, 'data': modelDict, 'total': totalModel, 'current_page': pageNumber, 'current_page_total': len(modelDict)}

    return jsonify(**response, **pagination)

@app.route('/api/models/train', methods=['POST'])
def trainModel():
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

    with Session(dbtool.getEngine()) as session:
        trainedModel = session.query(model.RecognitionModel).filter(model.RecognitionModel.task_id == taskId).first()


    result['name'] = trainedModel.name
    result['status'] = trainedModel.status

    return jsonify(result), 200


def getLatestModel():
    with Session(dbtool.getEngine()) as session:
        query = session.query(model.RecognitionModel).order_by(desc(model.RecognitionModel.created_at))

        latestModel = query.first()

        session.close()

        return latestModel

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
