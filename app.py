import os
from sqlalchemy import desc, func
from werkzeug.utils import secure_filename
import model
import dbtool
import math
import logging
from flask import Flask, json, jsonify, request, url_for
from sqlalchemy.orm.session import Session
from flask_cors import CORS
from recognition_tool import train, predict
from ulid import ULID


logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)

UPLOAD_FOLDER = 'stash'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CORS(app)

@app.route('/api/dataset/')
def getDataset():
    data = request.args

    currentPath = getCurrentPath(request.path)

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
    response = {'status': 200, 'data': datasetDict, 'total': totalDataset, 'current_page': pageNumber, 'current_page_total': len(datasetDict)}

    return jsonify(**response, **pagination)

@app.route('/api/recognize', methods=['POST'])
def storeImage():
    if 'file' not in request.files:
        return responseMessage(status=422, message="File is empty!")

    file = request.files['file']

    if file.filename == '':
        return responseMessage(status=422, message="File is empty!")

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        latestModel = getLatestModel()

        prediction = predict(filepath, model_path=latestModel.path)
        logging.info(len(prediction))

        if len(prediction) == 0:
            return jsonify({
                'name': "unknown",
                'location': "unknown",
                'model': latestModel.name,
                'status': 200,
                'message': "SUCCESS"
            })

        else:
            return jsonify({
                'name': prediction['name'],
                'location': prediction['location'],
                'model': latestModel.name,
                'status': 200,
                'message': "SUCCESS"
            })


    return jsonify({
        'status': 400,
        'message': "SOMETHING WRONG"
    })

@app.route('/api/models', methods={'GET'})
def getModel():
    data = request.args

    currentPath = getCurrentPath(request.path)

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
                'created_at': result.created_at,
            }

            modelDict.append(data)

        totalModel = session.query(model.RecognitionModel).count()

        session.close()

    pagination = getPaginationUrl(currentPath, total=totalModel, currentPage=pageNumber)
    response = {'status': 200, 'data': modelDict, 'total': totalModel, 'current_page': pageNumber, 'current_page_total': len(modelDict)}

    return jsonify(**response, **pagination)

@app.route('/api/models/train', methods=['POST'])
def trainModel():
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


    return jsonify({
        'status': 200,
        'message': "SUCCESS"
    })

def getLatestModel():
    with Session(dbtool.getEngine()) as session:
        query = session.query(model.RecognitionModel).order_by(desc(model.RecognitionModel.created_at))

        latestModel = query.first()

        session.close()

        return latestModel


def responseMessage(status = 200, message = "SUCCESS"):
    return jsonify({
        'status': status,
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






def getCurrentPath(path):
    return path[:-1]

if __name__ == '__main__':
    app.run(debug=True)
