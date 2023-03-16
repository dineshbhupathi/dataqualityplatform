import React, { useEffect, useState } from "react";
import axios from "axios";

import Footer from "../common/footer";
import Header from "../common/header";
import LoadingSpinner from "../common/loadingSpinner";
import { BsFillCloudDownloadFill,BsUpload,BsList,BsPencilSquare,BsFillTrashFill } from "react-icons/bs";
import { projects_api,get_project_files_api ,upload_project_file_api} from '../constants/endpoints'
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

export default function ProjectDetailsPage() {
    const [projectData, setProjectData] = useState([])
    const [projectFilesData,setProjectFilesData] = useState([])
    const [showDialogForm, setShowDialogForm] = useState(false)
    const [open, setOpen] = useState(true)
    const [payload, setPayload] = useState({})
    const theme = useTheme();
    
    const fullScreen = useMediaQuery(theme.breakpoints.down('md'));

    const getProjectData = () => {
        fetch(projects_api).then((res) => res.json()).then((res) => {
            setProjectData(res)
        })
    }

    const getProjectFilesData = () => {
        fetch(get_project_files_api).then((res) => res.json()).then((res) => {
            setProjectFilesData(res)
        })
    }
    useEffect(() => {
        getProjectData()
        getProjectFilesData()
    }, [])
    const handleClose =()=>{
        setShowDialogForm(false)
    }
    const dialogClick = () =>{
        setShowDialogForm(true)
    }
    const handleFileChange = (e) =>{
        setPayload({"file_name":e.target.files[0].name,"project":2,"uploaded_file":e.target.files[0]})

    }
    const handleSubmit = () =>{
        console.log(payload)
        axios.post(
            upload_project_file_api,
            payload,
            {
                headers: {
                    "Content-type": "multipart/form-data",
                },
            }
        ).then(res=>{
            console.log(res)
            setShowDialogForm(false)
        }).catch(err=>{
            console.log(err)
        })
    }
    return (
        <div>
            <Header />
            <div className="layout" id="main-container">
                <div className="flex space-between">
                    <div><h3><BsList /> Projects Details</h3></div>
                    <div><button className="btn btn-success" onClick={dialogClick}>Upload a file &nbsp; <BsUpload /></button></div>
                </div>
                <div className="mt-9">
                    <table className="dataset-process-table width-100">
                        <thead>
                            <tr>
                                <th>
                                    Project Name
                                </th>
                                <th>
                                    Description
                                </th>
                                <th>
                                    Last Updates
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {
                                projectData && projectData.length>0 && projectData.map((item) => (
                                    <tr key={item.id}>
                                        <td className="width-40">{item.project_name}</td>
                                        <td className="width-30">{item.description}</td>
                                        <td className="width-20">{item.updated_at}</td>
                                        {/* <td className="width-10"><button className="button-bor"><a className="btn btn-warning">Re-Train Dataset &nbsp;<BsPencilSquare /></a></button></td>
                                        <td className="width-10"><button className="btn btn-info"><a className="download-btn">Download</a>&nbsp;<BsFillCloudDownloadFill /></button></td>
                                        <td className="width-5"><button type="button" className="btn btn-danger delete-btn"><a className="download-btn"><BsFillTrashFill /></a></button></td> */}

                                    </tr>
                                ))
                            }
                        </tbody>
                    </table>
                            {
                                showDialogForm && (
                                    <div>                                
                                    <Dialog fullScreen={fullScreen} open={open} onClose={handleClose}>                                        
                                      <DialogContent>
                                          <h4>
                                          Upload File
                                          </h4>                                        
                                        <input
                                          type="file"
                                          onChange={handleFileChange}
                                        />
                                      </DialogContent>
                                      <DialogActions>
                                        {/* <button className="btn btn-info" onClick={handleClose}>Cancel</button> */}
                                        <button className="btn btn-info" onClick={handleSubmit}>Submit</button>
                                      </DialogActions>
                                    </Dialog>
                                  </div>
                                )
                            }
                            {
                                projectFilesData.length>0 && (
                
                                    <div className="mt-9">
                                                            <div><h3><BsList /> Files</h3></div>


                                    <table className="dataset-process-table width-100">
                        <thead>
                            <tr>
                                <th>
                                    File Name
                                </th>
                        
                                <th>
                                    Last Updates
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {
                                projectFilesData && projectFilesData.length>0 && projectFilesData.map((item) => (
                                    <tr key={item.id}>
                                        <td className="width-40">{item.file_name}</td>
                                        <td className="width-30">{item.updated_at}</td>                            
                                        <td className="width-10"><button className="button-bor"><a className="btn btn-warning">Re-Train Dataset &nbsp;<BsPencilSquare /></a></button></td>
                                        <td className="width-10"><button className="btn btn-info"><a className="download-btn">Download</a>&nbsp;<BsFillCloudDownloadFill /></button></td>
                                        <td className="width-5"><button type="button" className="btn btn-danger delete-btn"><a className="download-btn"><BsFillTrashFill /></a></button></td>

                                    </tr>
                                ))
                            }
                        </tbody>
                    </table></div>
                                ) 
                            }
                </div>

            </div>
            <Footer />
        </div>
    )
}