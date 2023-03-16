const BASE_URL = "http://127.0.0.1:8000/"
export const project_api = BASE_URL+"v1/upload_csv"
export const compare_data_set_api = BASE_URL+"v1/compare_dataset_project/"
export const projects_api = BASE_URL+"v1/projects/"
export const file_download = BASE_URL+"v1/file_download/"
export const read_csv_api = BASE_URL+"v1/read_csv/"
export const projet_data_check_api = BASE_URL+"v1/project_data/"
export const active_learning_link_api = BASE_URL+"v1/active_learning_link/"
export const active_learning_api = BASE_URL+"v1/active-learning"
export const active_training_api = BASE_URL+"v1/active-training"
export const active_training_link_api = BASE_URL+"v1/active_training_link"
export const delete_project_api = BASE_URL+"v1/delete_project/"
export const trained_data_api = BASE_URL+"v1/trained_data/"
export const upload_project_file_api = BASE_URL+"v1/upload_file/"
export const get_project_files_api = BASE_URL+"v1/project_files"


// data analytics endpints
export const data_analytics_projects_api = BASE_URL+'v1/data_analytics_projects'
export const data_analytics_report_api = BASE_URL+'v1/data_analytics_report'
export const data_analytics_upload_api = BASE_URL+'v1/data_reporting'
export const data_analytics_matching_files = BASE_URL+'v1/upload_csv_Datamatching'
export const data_analytics_matching_file_download = BASE_URL+'v1/file_download_matching'
export const data_matching_columns_api = BASE_URL+'v1/get_data_matching_columns'


// data missing values
export const data_missing_values_upload_api = BASE_URL+'v1/upload_csv_MissingValues/'
export const data_missing_values_download_api = BASE_URL+'v1/file_download_MissingValues'

// rules engine

export const upload_rules_engine_api = BASE_URL+'v2/upload_rules_csv'
export const rules_filtered_api = BASE_URL+'v2/filtered_data'
export const get_columns_api = BASE_URL+'v2/column_name_n_datatype'



// anomaly detection
export const upload_anomaly_csv_api = BASE_URL+'v2/anomalies_detection/upload_csv/'
export const read_anomaly_csv_api = BASE_URL+'v1/read_anomaly_csv_file/'
export const get_anomalies_api = BASE_URL+'v2/anomalies_detection/get_anomalies'
export const anomalies_file_download_api = BASE_URL+'v1/file_download_anomalies/'
