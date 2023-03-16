import React, { useState } from 'react';
import Header from '../common/header';
import { BsFillArrowRightSquareFill } from "react-icons/bs";
import Footer from '../common/footer';
import { upload_anomaly_csv_api, read_anomaly_csv_api, get_anomalies_api, anomalies_file_download_api } from '../constants/endpoints';
import axios from 'axios';
import { MultiSelect } from "react-multi-select-component";
import 'font-awesome/css/font-awesome.min.css';


export default function DetectAnomalies() {
    const [csvFile, setCsvFile] = useState(null)
    const [isUploadShow, setIsUploadShow] = React.useState(false)
    const [isFileUploaded, setIsFileUploaded] = React.useState(false)
    const [columnsData, setColumnsData] = React.useState({})
    const [categorialColumns, setCategorialColumns] = useState([]);
    const [numericalColumns, setNumericalColumns] = useState([]);
    const [fetchCategoricalColumns, setFetchCategoricalColumns] = useState([]);
    const [fetchNumericalColumns, setFetchNumericalColumns] = useState([]);
    const [isProcessShow, setIsProcessShow] = React.useState(false)
    const [loading, setloading] = React.useState(false)
    const [loadingProcess, setLoadingProcess] = React.useState(false)

    console.log(columnsData)
    const handleFile = (e) => {
        if (e.target.name == "file") {
            setCsvFile(e.target.files[0])
            setIsUploadShow(true)
        }
    }

    const handleUploadCsv = () => {
        let payload = { "uploaded_file": csvFile }
        setloading(true)
        setIsUploadShow(false)
        axios.post(
            upload_anomaly_csv_api,
            payload,
            {
                headers: {
                    "Content-type": "multipart/form-data",
                },
            }
        ).then(res=>{
            let data = {}
            axios.post(
                get_anomalies_api,
                data
            ).then(res=>{
                let payload = {}
            axios.post(
                anomalies_file_download_api,
                payload

            ).then(res => {
                setloading(false)
                setIsUploadShow(true)

                FileDownload(res.data, "anomalies_ouptut.csv")
                window.location.pathname = "/detect-anomalies"
            }).catch(err => {
                setloading(false)
                setIsUploadShow(true)

            })
            console.log(res)
            })
        })
        // ).then(res => {
        //     console.log(res)
        //     var today = new Date();
        //     var dd = String(today.getDate()).padStart(2, '0');
        //     var mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
        //     var yyyy = today.getFullYear();

        //     today = yyyy + '-' + mm + '-' + dd;
        //     let datepayload = { "date": today }
        //     axios.post(
        //         read_anomaly_csv_api,
        //         datepayload
        //     ).then(res => {
        //         console.log(res.data)
        //         let construtList = []
        //         let construtList2 = []
        //         res.data.categorical_columns.map(item => {
        //             let construtDic = {}
        //             construtDic["label"] = item
        //             construtDic["value"] = item
        //             construtList.push(construtDic)
        //             return construtList
        //         })
        //         res.data.numerical_columns.map(item => {
        //             let construtDic = {}
        //             construtDic["label"] = item
        //             construtDic["value"] = item
        //             construtList2.push(construtDic)
        //             return construtList2
        //         })
        //         setColumnsData(res.data)
        //         setFetchCategoricalColumns(construtList)
        //         setFetchNumericalColumns(construtList2)
        //     }).then(
        //         setTimeout(() => {
        //             setIsFileUploaded(true)
        //             setloading(false)
        //             setIsUploadShow(true)


        //         }, 500)
        //     )

        // }).catch(err=>{
        //     setIsUploadShow(true)
        // })
    }
    const FileDownload = require('js-file-download');

    const handleProcess = () => {
        setLoadingProcess(true)
        setIsProcessShow(false)
        let data_categoric = categorialColumns.map(item => item.value)
        let data_numeric = numericalColumns.map(item => item.value)
        let payload = { "data_categoric": data_categoric, "data_numeric": data_numeric }
        axios.post(
            get_anomalies_api,
            payload
        ).then(res => {
            let payload = {}
            axios.post(
                anomalies_file_download_api,
                payload

            ).then(res => {
                setLoadingProcess(false)
                setIsProcessShow(true)

                FileDownload(res.data, "anomalies_ouptut.csv")
            }).catch(err => {
                setLoadingProcess(false)
                setIsProcessShow(true)

            })
            console.log(res)
        }).catch(err => {
            setLoadingProcess(false)
            setIsProcessShow(true)

        })
    }
    const handleCheck = (e) => {
        console.log(e)
        if (categorialColumns.length > 0 && numericalColumns.length > 0) {
            setIsProcessShow(true)
        }
        else {
            setIsProcessShow(false)
        }
    }
    return (
        <div>
            <Header />
            <div className="layout" id="main-container">
                <div>
                    <label className="functionality-title">Detect anomalies</label>
                </div>
                <div className="alert alert-info alert-dismissible mt-3">
                    <button type="button" className="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">×</span></button>
                    <p>
                        <i className="fa fa-info-circle fa-fw">
                        </i>
                        Select a .csv file and can detect anomalies
                    </p>

                </div>
 
                <div className='flex width-100'>
                    <div className='width-70'>
                        
                        <input type="file" name="file" id="rules-upload" placeholder="Upload a file" onChange={(e) => handleFile(e)} />
                        {/* <input className='col-sm-4' type="file" name="encoder_model" id="encoder_model" placeholder="Upload a file" onChange={(e) => handleFile(e)} />
                        <input className='col-sm-4' type="file" name="decoder_model" id="decoder_model" placeholder="Upload a file" onChange={(e) => handleFile(e)} />
                         */}
                        <div className='buttons-section mt-3'>
                            <button type="button" className="btn btn-info mr-3" disabled={!isUploadShow} onClick={handleUploadCsv}>
                                {/* Process */}
                                {loading && (
                                    <i
                                        className="fa fa-refresh fa-spin"
                                        style={{ marginRight: "5px" }}
                                    />
                                )}
                                {loading && <span>Loading</span>}
                                {!loading && <span>Process</span>}
                            </button>

                        </div>
                    </div>

                </div>
                <br></br>
                {/* {isFileUploaded && (
                    <div className='flex width-100'>
                        <div className='result-table width-100'>
                            <table className="width-30 pull-right">
                                <thead>
                                    <tr>
                                        <th>Sr.No</th>
                                        <th>Column Name</th>
                                        <th>Data Type</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {columnsData.response && columnsData.response.length > 0 && columnsData.response.map((item) => (
                                        <tr key={item.sr_no}>
                                            <td>{item.sr_no}</td>
                                            <td>{item.column_name}</td>
                                            <td>{item.column_data_type}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            <div className="width-30">
                                <label className='alert-info' style={{ padding: "1rem 1rem" }}>Choose Categorical Columns to be considered<strong></strong></label>
                                <div className="input-group new_field_fields" onChange={(e) => handleCheck(e)}>
                                    <MultiSelect
                                        options={fetchCategoricalColumns}
                                        value={categorialColumns}
                                        onChange={setCategorialColumns}
                                        labelledBy="Select"
                                    />
                                    <br />
                                    <label className='alert-info' style={{ padding: "1rem 1rem" }}>Choose Numerical Columns to be considered<strong></strong></label>
                                    <div className="input-group new_field_fields" onChange={(e) => handleCheck(e)}>
                                        <MultiSelect
                                            options={fetchNumericalColumns}
                                            value={numericalColumns}
                                            onChange={setNumericalColumns}
                                            labelledBy="Select"
                                        />
                                        <div className='buttons-section mt-3 pull-right'>
                                            <button type="button" className="btn btn-info mr-3" disabled={!isProcessShow} onClick={handleProcess}>
                                                {loadingProcess && (
                                                    <i
                                                        className="fa fa-refresh fa-spin"
                                                        style={{ marginRight: "5px" }}
                                                    />
                                                )}
                                                {loadingProcess && <span>Loading... file will download after success</span>}
                                                {!loadingProcess && <span>Process</span>}
                                            </button>

                                        </div>
                                    </div>
                                </div>
                            </div>

                        </div>

                    </div>
                )} */}
            </div>
            <Footer />
        </div>
    );
}