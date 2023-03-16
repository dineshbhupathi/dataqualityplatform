import uvicorn
import os.path
from typing import List, Any, Union, Optional
from fastapi import *
from fastapi.middleware.cors import CORSMiddleware
# from app.databse import SessionLocal, engine
from app import models, database, schemas, crud, csv_processing, data_analytics
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.responses import FileResponse
# Rule Engine Dependencies
import rule_engine
import os
import csv
from unidecode import unidecode
import re
import datetime
import pandas as pd
import json
from fastapi import Response
import fuzzymatcher

# Anomalies Detection Dependencies
import sys
import random as rd
import numpy as np
from fastapi import FastAPI, Query
# importing pytorch libraries
import torch
from torch import nn
from torch import autograd
from torch.utils.data import DataLoader

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
    allow_credentials=True

)


def get_db():
    try:
        db = database.SessionLocal()
        yield db
    finally:
        db.close()


@app.get('/')
def main():
    return RedirectResponse(url='/docs/')


@app.post('/v1/upload_csv')
async def upload(project_name: str = Form(...), description: str = Form(...), uploaded_file: UploadFile = File(...),
                 data_check: str = Form(...), link_project: str = Form(...), db: Session = Depends(get_db)):
    projects = db.query(models.Project).all()
    if projects:
        last_project_id = projects[-1].id + 1
    else:
        last_project_id = 1
    if link_project != "0":
        csv_name = 'input_file_' + str(link_project) + "_" + str(last_project_id) + ".csv"
    else:
        csv_name = 'input_file_' + str(last_project_id) + ".csv"
    csv_path = 'csv_dir/'
    file_path = os.path.join(csv_path, csv_name)
    with open(file_path, mode='wb+') as f:
        f.write(uploaded_file.file.read())

    project = schemas.Project(
        project_name=project_name,
        description=description,
        file=csv_name,
        data_check=data_check,
        link_project=link_project
    )
    if link_project != "0":
        session = Session(bind=database.engine, expire_on_commit=False)
        pr = session.query(models.Project).get(link_project)
        if pr:
            pr.data_check = "dedupe_data"
            session.commit()
        session.close()

    return crud.create_project(db=db, project=project)


@app.get('/v1/projects', response_model=List[schemas.ProjectsList])
async def show_projects(db: Session = Depends(get_db)):
    projects = db.query(models.Project).all()
    return projects


@app.get('/v1/read_csv/{project_id}')
async def read_csv(project_id, db: Session = Depends(get_db)):
    project = db.query(models.Project).get(project_id)

    if project.link_project != "0":
        linked_project_id = project.link_project + "_" + str(project_id)
        csv_value = csv_processing.get_data(linked_project_id)
        column_names = csv_processing.column_names(project.link_project)
        column_List = list(column_names.keys())
    else:
        csv_value = csv_processing.get_data(project_id)
        column_names = csv_processing.column_names(project_id)
        column_List = list(column_names.keys())

    child_project = db.query(models.Project).all()
    child_project_columns_lis = []
    for i in child_project:
        if str(i.id) == project_id and str(i.link_project) != "0":
            link_id = str(i.link_project) + "_" + str(i.id)
            child_columns = csv_processing.column_names(link_id)
            child_project_columns_lis.append(list(child_columns.keys()))

    # with open("json_dir/input.json")

    if child_project_columns_lis:
        return {'message': 'Data Reading Successful', 'columns': column_List,
                'child_columns': child_project_columns_lis[0], 'project': project}
    else:
        return {'message': 'Data Reading Successful', 'columns': column_List, 'project': project}


@app.get('/v1/compare_dataset_project/', response_model=List[schemas.ProjectsList])
async def show_dataset_project(db: Session = Depends(get_db)):
    projects = db.query(models.Project).all()
    lst_projects = []
    for i in projects:
        if i.data_check == 'compare_data':
            lst_projects.append(i)

    return lst_projects


@app.post('/v1/active-learning')
async def active_learning(
        payload: dict = Body(...)
):
    project = payload['project']
    field_values = payload['check_columns']
    active_learning_response = csv_processing.active_learning(field_values, project)
    return active_learning_response


@app.post('/v1/active-training')
async def csv_active_training(
        payload: dict = Body(...)
):
    project = payload.get('data')[-1]
    project_data = project.get('project')
    del payload['data'][-1]['project']
    data = payload
    training_response = csv_processing.active_training(data, project_data)
    return training_response


@app.post('/v1/file_download')
async def file_download(
        payload: dict = Body(...),
        db: Session = Depends(get_db)
):
    id = payload.get('id')
    project = db.query(models.Project).get(id)
    if project.link_project != "0":
        file_name = 'data_matching_output_' + str(project.link_project) + '_' + str(id) + '.csv'
    else:
        file_name = 'output_file_project_' + str(id) + '.csv'
    file_path = os.path.join(os.getcwd(), "output", file_name)

    return FileResponse(path=file_path, media_type="application/octet-stream", filename=file_name)


@app.get('/v1/project_data/{project_id}')
async def projectCheck(project_id, db: Session = Depends(get_db)):
    project = db.query(models.Project).get(project_id)
    res_dic = {}

    if project.link_project != "0":
        res_dic['is_link'] = "true"
    else:
        res_dic['is_link'] = "false"

    return res_dic


'''
    Linkage Fun Start
'''


@app.post('/v1/active_learning_link')
async def active_learning_link(
        payload: dict = Body(...)
):
    project = payload['project']
    field_values = payload['check_columns']

    clean_fields = []
    for i in field_values:
        if i.get('field2'):
            clean_dic = {}
            clean_dic['field'] = i['field2']
            clean_dic['type'] = i['type']
            clean_dic['has missing'] = i['has missing']
            del i['field2']
            clean_fields.append(i)
            # clean_fields.append(clean_dic)
    session = Session(bind=database.engine, expire_on_commit=False)
    project_id = project.get('id')
    pr = session.query(models.Project).get(project_id)
    clean_project_dic = {"project_1": pr.link_project, "project_2": project_id}
    active_learning_res = csv_processing.active_learning_link(clean_fields, clean_project_dic)
    return active_learning_res


@app.post('/v1/active_training_link')
async def active_training_link(
        payload: dict = Body(...)
):
    project = payload.get('data')[-1]
    project_id = project.get('project').get('id')
    session = Session(bind=database.engine, expire_on_commit=False)
    pr = session.query(models.Project).get(project_id)
    cleaned_project_dic = {"project_1": pr.link_project, "project_2": project_id}
    del payload['data'][-1]['project']
    data = payload
    res = csv_processing.active_training_link(data, cleaned_project_dic)
    return res


@app.get('/v1/project/{project_id}')
async def show_project(project_id: int, db: Session = Depends(get_db)):
    # with Session(database.engine) as session:
    #     project = session.get(models.Project, project_id)
    #     if not project:
    #         raise HTTPException(status_code=404, detail="project not fount")
    #     return {"response": project}
    project = db.query(models.Project).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")
    return {"response": project}


@app.delete("/v1/delete_project/{project_id}")
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    # with Session(database.engine) as session:
    #     project = session.get(models.Project, project_id)
    #     print(project)
    #     if not project:
    #         raise HTTPException(status_code=404, detail="project not found")
    #     session.delete(project)
    #     session.commit()
    #     return {"ok": True}
    project = db.query(models.Project).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")
    db.delete(project)
    db.commit()
    return {"ok": True}


@app.post('/v1/data_reporting')
async def data_report(project_name: str = Form(...), uploaded_file: UploadFile = File(...),
                      db: Session = Depends(get_db)):
    projects = db.query(models.DataReportProject).all()
    if projects:
        last_project_id = projects[-1].id + 1
    else:
        last_project_id = 1
    csv_name = 'data_reporting_file' + str(last_project_id) + ".csv"
    csv_path = 'csv_dir/'
    file_path = os.path.join(csv_path, csv_name)
    with open(file_path, mode='wb+') as f:
        f.write(uploaded_file.file.read())

    project = schemas.DataReportingProject(
        project_name=project_name,

    )
    data_reporting = data_analytics.data_analysis(file_path, last_project_id)
    return crud.create_data_reporting_project(db=db, project=project)


@app.post('/v1/data_analytics_report')
async def data_analytics_file(
        payload: dict = Body(...)):
    id = payload.get('id')
    file_name = 'data_analytics_project_' + str(id) + '.html'
    file_path = os.path.join(os.getcwd(), "output", file_name)
    return FileResponse(path=file_path, filename=file_name)


@app.get('/v1/data_analytics_projects', response_model=List[schemas.DataReportingProjectList])
async def show_projects(db: Session = Depends(get_db)):
    projects = db.query(models.DataReportProject).all()
    return projects


@app.delete("/v1/delete_data_analysis_project/{project_id}")
async def delete_data_analysis_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.DataReportProject).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")
    db.delete(project)
    db.commit()
    return {"ok": True}


######################################
# Rule Engine Functionality Started
######################################

def get_data_rule_engine():
    dt = str(datetime.datetime.now())
    dt = "_".join(dt.split()).replace(":", "-")
    dt = dt[:-16]
    csv_name = 'input_file_' + dt + '.csv'
    csv_path = 'csv_dir/'
    data_path = os.path.join(csv_path, csv_name)
    df = pd.read_csv(data_path)
    formated_df = df.to_dict(orient='records')
    return formated_df


def get_column_name():
    dt = str(datetime.datetime.now())
    dt = "_".join(dt.split()).replace(":", "-")
    dt = dt[:-16]
    csv_name = 'rules_input_file_' + dt + '.csv'
    csv_path = 'csv_dir/'
    data_path = os.path.join(csv_path, csv_name)
    df = pd.read_csv(data_path, sep=',', encoding='utf-8')
    columns = []
    columns_datatype = []

    for column in df.columns:
        columns.append(column)
        columns_datatype.append(df[column].dtype.name)

    comb_lis = zip(columns, columns_datatype)
    new_dict = dict(comb_lis)
    return new_dict


def rule_engine_execution(value):
    try:
        print("Entering try Block")
        formated_df = get_data_rule_engine()
        rule = rule_engine.Rule(value)
        rule_execution = rule.filter(formated_df)
        return rule_execution

    except Exception as e:
        print("Entering Exception Block")
        return e


@app.post('/v2/upload_rules_csv/')
async def upload(uploaded_file: UploadFile = File(...)):
    # save csv to local dir
    dt = str(datetime.datetime.now())
    dt = "_".join(dt.split()).replace(":", "-")
    dt = dt[:-16]
    csv_name = 'rules_input_file_' + dt + '.csv'
    csv_path = 'csv_dir/'
    file_path = os.path.join(csv_path, csv_name)

    with open(file_path, mode='wb+') as f:
        f.write(uploaded_file.file.read())
        return {'message': 'Input File Successfully Uploaded'}


# @app.get('/v2/get_data_format/')
# async def get_formatted_data():
#     data= get_data_rule_engine()
#     #Serializing json
#     #columns_name_json= json.dumps(data)
#     #Dumping Input CSV to JSON
#     with open('json_dir/data.json','w') as outfile:
#         json.dump(data, outfile)
#     return {'message': 'Data Formated Successfully'}

@app.get('/v2/column_name_n_datatype')
async def get_column_name_n_datatype():
    column_names = get_column_name()

    # Serializing json
    column_names_json = json.dumps(column_names)
    res_dicts = list()
    count = 1
    for i in column_names.items():
        temp_dict = dict()
        temp_dict["sr_no"] = count
        temp_dict["column_name"] = i[0]
        temp_dict["column_data_type"] = i[1]
        res_dicts.append(temp_dict)
        count += 1

    return {'message': 'Column Names with Dtype Retrved', 'response': res_dicts}


@app.post('/v2/filtered_data/')
async def get_filtered_data(payload: dict = Body(...)):
    # writer = pd.ExcelWriter('output/rules_output.csv')
    try:
        value = payload.get('value')
        filter_df = rule_engine_execution(value)
        lst = list(filter_df)
        output_df = pd.DataFrame.from_records(lst)
        # create excel writer object
        # write dataframe to excel
        output_df.to_csv('output/rules_output.csv')
        # writer.save()

        # return {'message': 'Rule Engine Execution Successfully'}
        file_name = 'rules_output.csv'
        file_path = os.path.join(os.getcwd(), "output", file_name)
        return FileResponse(path=file_path, media_type="application/octet-stream", filename=file_name)

    except Exception as e:
        return e


@app.post("/v1/trained_data")
async def is_trained_data(payload: dict = Body(...)
                          ):
    project_id = payload.get("id")
    file = os.getcwd()
    file_name = 'csv_learned_settings_' + str(project_id)
    file_path = os.path.join(file, "model_dir", file_name)
    if os.path.exists(file_path):
        return {"message": "exits"}
    else:
        return {"message": "doesn't exits"}


####Data Matching

@app.post('/v1/upload_csv_Datamatching')
async def upload(uploaded_file1: UploadFile = File(...), uploaded_file2: UploadFile = File(...)):
    # save csv to local dir
    dt = str(datetime.datetime.now())
    dt = "_".join(dt.split()).replace(":", "-")
    dt = dt[:-16]
    csv_name1 = 'left_' + dt + '.csv'
    csv_name2 = 'right_' + dt + '.csv'
    csv_path = 'csv_dir'
    csv_path = os.path.join(os.getcwd(), 'csv_dir')
    # print(os.getcwd())
    # csv_path = 'D:\\Users\\Kotti\\Documents\\GitHub\\DataQualityPlatform\\data-quality-platform\\csv_dir\\'

    file_path1 = os.path.join(csv_path, csv_name1)
    file_path2 = os.path.join(csv_path, csv_name2)
    with open(file_path1, mode='wb+') as f:
        f.write(uploaded_file1.file.read())
    with open(file_path2, mode='wb+') as f:
        f.write(uploaded_file2.file.read())

    return {'message': 'Input File Successfully Uploaded', 'files': [csv_name1, csv_name2]}


@app.post('/v1/file_download_matching')
async def file_download(
        payload: dict = Body(...),
        db: Session = Depends(get_db)
):
    # dt= str(datetime.datetime.now())
    # dt= "_".join(dt.split()).replace(":","-")
    # dt= dt[:-16]
    # csv_name1= 'left_'+dt+'.csv'
    # csv_name2= 'right_'+dt+'.csv'
    csv_path = 'csv_dir'
    csv_name1 = payload.get('file1')
    csv_name2 = payload.get('file2')
    csv_path = os.path.join(os.getcwd(), 'csv_dir')
    data_path1 = os.path.join(csv_path, csv_name1)
    df_left = pd.read_csv(data_path1)
    data_path2 = os.path.join(csv_path, csv_name2)
    df_right = pd.read_csv(data_path2)
    # Columns to match on from df_left
    left_on = payload.get("file_1_columns")
    # ["fname", "mname", "lname", "dob"]
    # Columns to match on from df_right
    right_on = payload.get("file_2_columns")
    # ["name", "middlename", "surname", "date"]
    # Note that if left_id_col or right_id_col are admitted a unique id will be autogenerated
    lt_df = fuzzymatcher.link_table(df_left, df_right, left_on, right_on, left_id_col="id", right_id_col="id")
    file_name = "Matching_output.csv"
    out_path = os.path.join(csv_path, "Matching_output.csv")
    lt_df.to_csv(out_path)
    file_path = out_path

    return FileResponse(path=file_path, media_type="application/octet-stream", filename=file_name)


def read_data_matching_csv(file):
    read_file = pd.read_csv(file)
    col_lst = []
    for col in read_file.columns:
        col_lst.append(col)

    return col_lst


@app.get('/v1/get_data_matching_columns')
async def get_data_matching_columns(
):
    dt = str(datetime.datetime.now())
    dt = "_".join(dt.split()).replace(":", "-")
    dt = dt[:-16]
    csv_name1 = 'left_' + dt + '.csv'
    csv_name2 = 'right_' + dt + '.csv'
    csv_path = os.path.join(os.getcwd(), 'csv_dir')
    data_path1 = os.path.join(csv_path, csv_name1)
    data_path2 = os.path.join(csv_path, csv_name2)
    file_1_columns = read_data_matching_csv(data_path1)
    file_2_columns = read_data_matching_csv(data_path2)
    return {"file1": csv_name1, "file2": csv_name2, "file_1_columns": file_1_columns, "file_2_columns": file_2_columns}


#####Data MissingValues

@app.post('/v1/upload_csv_MissingValues/')
async def upload(uploaded_file1: UploadFile = File(...)):
    # save csv to local dir
    dt = str(datetime.datetime.now())
    dt = "_".join(dt.split()).replace(":", "-")
    dt = dt[:-16]
    csv_name1 = 'Property_data_' + dt + '.csv'
    csv_path = 'csv_dir'
    csv_path = os.path.join(os.getcwd(), 'csv_dir')
    # print(os.getcwd())
    # csv_path = 'D:\\Users\\Kotti\\Documents\\GitHub\\DataQualityPlatform\\data-quality-platform\\csv_dir\\'

    file_path1 = os.path.join(csv_path, csv_name1)
    with open(file_path1, mode='wb+') as f:
        f.write(uploaded_file1.file.read())
    return {'message': 'Input File Successfully Uploaded', "files": [csv_name1]}


@app.post('/v1/file_download_MissingValues')
async def file_download(
        payload: dict = Body(...),
        db: Session = Depends(get_db)
):
    dt = str(datetime.datetime.now())
    dt = "_".join(dt.split()).replace(":", "-")
    dt = dt[:-16]
    csv_name1 = payload.get("file")
    csv_path = 'csv_dir'
    csv_path = os.path.join(os.getcwd(), 'csv_dir')
    data_path1 = os.path.join(csv_path, csv_name1)
    df = pd.read_csv(data_path1)
    cols1 = df.select_dtypes([np.number]).columns
    cols2 = df.select_dtypes(exclude=[np.number]).columns
    df[cols1] = df[cols1].fillna(df[cols1].mean())
    df[cols2] = df[cols2].fillna(df[cols2].mode().iloc[0])
    file_name = "Property_Data_output.csv"
    out_path = os.path.join(csv_path, "Property_Data_output.csv")
    df.to_csv(out_path)
    file_path = out_path

    return FileResponse(path=file_path, media_type="application/octet-stream", filename=file_name)


##########################################
####Anomalies Detection Started############
###########################################
def column_names():
    dt = str(datetime.datetime.now())
    dt = "_".join(dt.split()).replace(":", "-")
    dt = dt[:-16]
    csv_name = 'input_file_' + dt + '.csv'
    csv_path = 'csv_dir/'
    data_path = os.path.join(csv_path, csv_name)
    df = pd.read_csv(data_path, sep=',', encoding='utf-8')
    columns = []
    columns_datatype = []
    for column in df.columns:
        columns.append(column)
        columns_datatype.append(df[column].dtype.name)
    comb_lis = zip(columns, columns_datatype)
    new_dict = dict(comb_lis)
    return new_dict


def get_categorical_cols():
    list_of_categorical_cols = list()
    col_details = column_names()

    for i in col_details.keys():
        if col_details.get(i) == 'object':
            list_of_categorical_cols.append(i)
    list_of_categorical_cols.remove('label')
    return list_of_categorical_cols


def get_numerical_cols():
    list_of_numerical_cols = list()
    col_details = column_names()
    for i in col_details.keys():
        if col_details.get(i) != 'object':
            list_of_numerical_cols.append(i)
    return list_of_numerical_cols


def data_preprocess():
    dt = str(datetime.datetime.now())
    dt = "_".join(dt.split()).replace(":", "-")
    dt = dt[:-16]
    csv_name = 'input_file_' + dt + '.csv'
    csv_path = 'csv_dir/'
    data_path = os.path.join(csv_path, csv_name)
    # Reading CSV File
    ori_dataset = pd.read_csv(data_path)
    # print(ori_dataset.columns)
    return ori_dataset


def one_hot_encoding():
    ori_dataset = data_preprocess()
    label = ori_dataset.pop('label')
    # categorical_attr_names = get_categorical_cols()
    categorical_attr_names = ['KTOSL', 'PRCTR', 'BSCHL', 'HKONT']
    # print(categorical_attr_names)
    # One hot encoding the categorical attributes
    ori_dataset_categ_transformed = pd.get_dummies(ori_dataset[categorical_attr_names])
    # print(ori_dataset_categ_transformed.head())
    return ori_dataset_categ_transformed


def numeric_data_normalization():
    ori_dataset = data_preprocess()
    # numeric_attr_names = get_numerical_cols()
    numeric_attr_names = ['DMBTR', 'WRBTR']
    # add a small epsilon to eliminate zero values from data for log scaling
    numeric_attr = ori_dataset[numeric_attr_names] + 1e-7
    numeric_attr = numeric_attr.apply(np.log)
    # normalize all numeric attributes to the range [0,1]
    ori_dataset_numeric_attr = (numeric_attr - numeric_attr.min()) / (numeric_attr.max() - numeric_attr.min())
    # print(ori_dataset_numeric_attr)
    return ori_dataset_numeric_attr


def merging_of_cat_n_numeric():
    ori_dataset_categ_transformed = one_hot_encoding()
    ori_dataset_numeric_attr = numeric_data_normalization()
    ori_subset_transformed = pd.concat([ori_dataset_categ_transformed, ori_dataset_numeric_attr], axis=1)
    # print(ori_subset_transformed.head())
    return ori_subset_transformed


def get_shape_of_input():
    ori_subset_transformed = merging_of_cat_n_numeric()
    no_of_colums = ori_subset_transformed.shape[1]
    return no_of_colums


# implementation of the encoder network
class encoder(nn.Module):

    def __init__(self):
        super(encoder, self).__init__()
        input_shape = get_shape_of_input()

        # specify layer 1 - in 618, out 512
        self.encoder_L1 = nn.Linear(in_features=input_shape, out_features=512, bias=True)  # add linearity
        nn.init.xavier_uniform_(self.encoder_L1.weight)  # init weights according to [9]
        self.encoder_R1 = nn.LeakyReLU(negative_slope=0.4, inplace=True)  # add non-linearity according to [10]

        # specify layer 2 - in 512, out 256
        self.encoder_L2 = nn.Linear(512, 256, bias=True)
        nn.init.xavier_uniform_(self.encoder_L2.weight)
        self.encoder_R2 = nn.LeakyReLU(negative_slope=0.4, inplace=True)

        # specify layer 3 - in 256, out 128
        self.encoder_L3 = nn.Linear(256, 128, bias=True)
        nn.init.xavier_uniform_(self.encoder_L3.weight)
        self.encoder_R3 = nn.LeakyReLU(negative_slope=0.4, inplace=True)

        # specify layer 4 - in 128, out 64
        self.encoder_L4 = nn.Linear(128, 64, bias=True)
        nn.init.xavier_uniform_(self.encoder_L4.weight)
        self.encoder_R4 = nn.LeakyReLU(negative_slope=0.4, inplace=True)

        # specify layer 5 - in 64, out 32
        self.encoder_L5 = nn.Linear(64, 32, bias=True)
        nn.init.xavier_uniform_(self.encoder_L5.weight)
        self.encoder_R5 = nn.LeakyReLU(negative_slope=0.4, inplace=True)

        # specify layer 6 - in 32, out 16
        self.encoder_L6 = nn.Linear(32, 16, bias=True)
        nn.init.xavier_uniform_(self.encoder_L6.weight)
        self.encoder_R6 = nn.LeakyReLU(negative_slope=0.4, inplace=True)

        # specify layer 7 - in 16, out 8
        self.encoder_L7 = nn.Linear(16, 8, bias=True)
        nn.init.xavier_uniform_(self.encoder_L7.weight)
        self.encoder_R7 = nn.LeakyReLU(negative_slope=0.4, inplace=True)

        # specify layer 8 - in 8, out 4
        self.encoder_L8 = nn.Linear(8, 4, bias=True)
        nn.init.xavier_uniform_(self.encoder_L8.weight)
        self.encoder_R8 = nn.LeakyReLU(negative_slope=0.4, inplace=True)

        # specify layer 9 - in 4, out 3
        self.encoder_L9 = nn.Linear(4, 3, bias=True)
        nn.init.xavier_uniform_(self.encoder_L9.weight)
        self.encoder_R9 = nn.LeakyReLU(negative_slope=0.4, inplace=True)

        # init dropout layer with probability p
        self.dropout = nn.Dropout(p=0.0, inplace=True)

    def forward(self, x):
        # define forward pass through the network
        x = self.encoder_R1(self.dropout(self.encoder_L1(x)))
        x = self.encoder_R2(self.dropout(self.encoder_L2(x)))
        x = self.encoder_R3(self.dropout(self.encoder_L3(x)))
        x = self.encoder_R4(self.dropout(self.encoder_L4(x)))
        x = self.encoder_R5(self.dropout(self.encoder_L5(x)))
        x = self.encoder_R6(self.dropout(self.encoder_L6(x)))
        x = self.encoder_R7(self.dropout(self.encoder_L7(x)))
        x = self.encoder_R8(self.dropout(self.encoder_L8(x)))
        x = self.encoder_R9(self.encoder_L9(x))  # don't apply dropout to the AE bottleneck

        return x


# implementation of the decoder network
class decoder(nn.Module):

    def __init__(self):
        super(decoder, self).__init__()
        input_shape = get_shape_of_input()

        # specify layer 1 - in 3, out 4
        self.decoder_L1 = nn.Linear(in_features=3, out_features=4, bias=True)  # add linearity
        nn.init.xavier_uniform_(self.decoder_L1.weight)  # init weights according to [9]
        self.decoder_R1 = nn.LeakyReLU(negative_slope=0.4, inplace=True)  # add non-linearity according to [10]

        # specify layer 2 - in 4, out 8
        self.decoder_L2 = nn.Linear(4, 8, bias=True)
        nn.init.xavier_uniform_(self.decoder_L2.weight)
        self.decoder_R2 = nn.LeakyReLU(negative_slope=0.4, inplace=True)

        # specify layer 3 - in 8, out 16
        self.decoder_L3 = nn.Linear(8, 16, bias=True)
        nn.init.xavier_uniform_(self.decoder_L3.weight)
        self.decoder_R3 = nn.LeakyReLU(negative_slope=0.4, inplace=True)

        # specify layer 4 - in 16, out 32
        self.decoder_L4 = nn.Linear(16, 32, bias=True)
        nn.init.xavier_uniform_(self.decoder_L4.weight)
        self.decoder_R4 = nn.LeakyReLU(negative_slope=0.4, inplace=True)

        # specify layer 5 - in 32, out 64
        self.decoder_L5 = nn.Linear(32, 64, bias=True)
        nn.init.xavier_uniform_(self.decoder_L5.weight)
        self.decoder_R5 = nn.LeakyReLU(negative_slope=0.4, inplace=True)

        # specify layer 6 - in 64, out 128
        self.decoder_L6 = nn.Linear(64, 128, bias=True)
        nn.init.xavier_uniform_(self.decoder_L6.weight)
        self.decoder_R6 = nn.LeakyReLU(negative_slope=0.4, inplace=True)

        # specify layer 7 - in 128, out 256
        self.decoder_L7 = nn.Linear(128, 256, bias=True)
        nn.init.xavier_uniform_(self.decoder_L7.weight)
        self.decoder_R7 = nn.LeakyReLU(negative_slope=0.4, inplace=True)

        # specify layer 8 - in 256, out 512
        self.decoder_L8 = nn.Linear(256, 512, bias=True)
        nn.init.xavier_uniform_(self.decoder_L8.weight)
        self.decoder_R8 = nn.LeakyReLU(negative_slope=0.4, inplace=True)

        # specify layer 9 - in 512, out 618
        self.decoder_L9 = nn.Linear(in_features=512, out_features=input_shape, bias=True)
        nn.init.xavier_uniform_(self.decoder_L9.weight)
        self.decoder_R9 = nn.LeakyReLU(negative_slope=0.4, inplace=True)

        # init dropout layer with probability p
        self.dropout = nn.Dropout(p=0.0, inplace=True)

    def forward(self, x):
        # define forward pass through the network
        x = self.decoder_R1(self.dropout(self.decoder_L1(x)))
        x = self.decoder_R2(self.dropout(self.decoder_L2(x)))
        x = self.decoder_R3(self.dropout(self.decoder_L3(x)))
        x = self.decoder_R4(self.dropout(self.decoder_L4(x)))
        x = self.decoder_R5(self.dropout(self.decoder_L5(x)))
        x = self.decoder_R6(self.dropout(self.decoder_L6(x)))
        x = self.decoder_R7(self.dropout(self.decoder_L7(x)))
        x = self.decoder_R8(self.dropout(self.decoder_L8(x)))
        x = self.decoder_R9(self.decoder_L9(x))  # don't apply dropout to the AE output

        return x


mini_batch_size = 128
num_epochs = 5


def assessment_of_individual_transactions():
    # init training network classes / architectures
    encoder_eval = encoder()
    decoder_eval = decoder()

    # restore pretrained model checkpoint
    encoder_model_name = "ep_20_encoder_model.pth"
    decoder_model_name = "ep_20_decoder_model.pth"
    # load trained models
    encoder_eval.load_state_dict(torch.load(os.path.join("models", encoder_model_name)))
    decoder_eval.load_state_dict(torch.load(os.path.join("models", decoder_model_name)))
    ori_dataset = data_preprocess()
    # Converting Pre-Processed data to pytorch tensor
    ori_subset_transformed = merging_of_cat_n_numeric()
    torch_dataset = torch.from_numpy(ori_subset_transformed.values).float()
    loss_function = nn.BCEWithLogitsLoss(reduction='mean')
    # Convert to pytorch tensor- none cuda enabled
    dataloader = DataLoader(torch_dataset, batch_size=mini_batch_size, shuffle=True, num_workers=0)

    data = autograd.Variable(torch_dataset)

    # Set networks in evaluaiton mode
    encoder_eval.eval()
    decoder_eval.eval()

    # Reconstruct encoded transactional data
    reconstruction = decoder_eval(encoder_eval(data))

    reconstruction_loss_transaction = np.zeros(reconstruction.size()[0])
    # iterate overall detailed reconstructions
    for i in range(0, reconstruction.size()[0]):
        # Determine reconstruciton loss- individual transactions
        reconstruction_loss_transaction[i] = loss_function(reconstruction[i], data[i]).item()
    output = ori_dataset[(reconstruction_loss_transaction >= 0.05) & (reconstruction_loss_transaction < 0.1)]
    return output


#######Uploading CSV#########

@app.post('/v2/anomalies_detection/upload_csv/')
async def upload(uploaded_file: UploadFile = File(...), uploaded_encoder_model: Optional[UploadFile] = File(None),
                 uploaded_decoder_model: Optional[UploadFile] = File(None),
                 uploaded_decoder_model_name: Optional[str] = Form(None),
                 uploaded_encoder_model_name: Optional[str] = Form(None)):
    # Save CSV to Local Dir
    dt = str(datetime.datetime.now())
    dt = "_".join(dt.split()).replace(":", "-")
    dt = dt[:-16]
    csv_name = 'input_file_' + dt + '.csv'
    csv_path = 'csv_dir/'
    file_path = os.path.join(csv_path, csv_name)
    model_path = 'models/'
    if uploaded_encoder_model_name and uploaded_decoder_model:
        encoder_model_path = os.path.join(model_path, uploaded_encoder_model_name)
        decoder_model_path = os.path.join(model_path, uploaded_decoder_model_name)
        with open(encoder_model_path, mode='wb+') as f:
            f.write(uploaded_encoder_model.file.read())
        with open(decoder_model_path, mode='wb+') as f:
            f.write(uploaded_decoder_model.file.read())

    with open(file_path, mode='wb+') as f:
        f.write(uploaded_file.file.read())


    return {'message': 'Input File Successfully Uplaoded'}


#######Getting Col Names#########
@app.post('/v2/anomalies_detection/get_column_names_csv/')
async def get_column_name():
    res = column_names()
    categorical_columns = list()
    numerical_columns = list()
    res_dicts = list()
    count = 1
    for i in res.keys():
        if res.get(i) == 'object':
            categorical_columns.append(i)
        else:
            numerical_columns.append(i)
    for i in res.items():
        temp_dict = dict()
        temp_dict["sr_no"] = count
        temp_dict["column_name"] = i[0]
        temp_dict["column_data_type"] = i[1]
        res_dicts.append(temp_dict)
        count += 1
    return {"response": res_dicts, "categorical_columns": categorical_columns, "numerical_columns": numerical_columns}


@app.post('/v2/anomalies_detection/get_categorical_columns/')
async def get_categorical_column_name():
    list_of_cols = get_categorical_cols()
    # print(list_of_cols)
    return {"categorical_columns": list_of_cols}


@app.post('/v2/anomalies_detection/get_numerical_columns/')
async def get_numerical_column_name():
    list_of_cols = get_numerical_cols()
    # print(list_of_cols)
    return {"numerical_columns": list_of_cols}


@app.post('/v2/anomalies_detection/one_hot_encoding')
async def get_one_hot_encoding():
    one_hot_encoded_df = one_hot_encoding()
    return {'Message': 'One Hot Encoding Successful'}


@app.post('/v2/anomalies_detection/numeric_col_normalization/')
async def get_normalized_numeric_col():
    normalized_col_values = numeric_data_normalization()
    # json_value = normalized_col_values.to_json()
    return {'Message': 'Normalization Successful'}


@app.post('/v2/anomalies_detection/shape_of_input/')
async def get_input_shape():
    value = get_shape_of_input()
    return {'input shape': value}


@app.post('/v2/anomalies_detection/mergin_cat_n_num/')
async def get_merged_df():
    normalized_col_values = merging_of_cat_n_numeric()
    # json_value = normalized_col_values.to_json()
    return {'Message': 'Merging Successful'}


@app.post('/v2/anomalies_detection/get_anomalies')
async def get_anomalies():
    final_result = assessment_of_individual_transactions()
    # print(final_result)
    # print(type(final_result))
    final_result.to_csv('output/final_anomalies.csv', index=False)
    # Create excel writer object
    writer = pd.ExcelWriter('output/final_anomalies.xlsx')
    # Write dataframe to Excel
    final_result.to_excel(writer)
    writer.save()
    return {'message': 'Analysis Completed'}


#
# @app.post('/v1/get_anomalies')
# async def get_anomalies(data_categoric: Union[List[str], None] = Query(default=None),
#                         data_numeric: Union[List[str], None] = Query(default=None)):
# @app.post('/v1/get_anomalies')
# async def get_anomalies(
#         payload: dict = Body(...)
# ):
#     data_categoric = payload.get('data_categoric')
#     data_numeric = payload.get('data_numeric')
#     final_result = assessment_of_individual_transactions(data_categoric, data_numeric)
#     print(final_result)
#     print(type(final_result))
#     final_result.to_csv('output/final_anomalies.csv', index=False)
#     # Create excel writer object
#     writer = pd.ExcelWriter('output/final_anomalies.xlsx')
#     # Write dataframe to Excel
#     final_result.to_excel(writer)
#     writer.save()
#     return {'message': 'Analysis Completed'}

@app.post('/v1/file_download_anomalies')
async def anomalies_file_download(
        payload: dict = Body(...),
        db: Session = Depends(get_db)
):
    csv_name = 'final_anomalies.csv'
    csv_path = 'output/'
    file_path = os.path.join(csv_path, csv_name)
    return FileResponse(path=file_path, media_type="application/octet-stream", filename=csv_name)


if __name__ == '__main__':
    uvicorn.run('main:app', server_header=False)
