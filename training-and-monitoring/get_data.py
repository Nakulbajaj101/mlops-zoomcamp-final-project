from prefect_training_monitoring.utility_functions import download_data

files = ["202201-capitalbikeshare-tripdata.zip",
         "202202-capitalbikeshare-tripdata.zip",
         "202203-capitalbikeshare-tripdata.zip",
         "202204-capitalbikeshare-tripdata.zip",
         "202205-capitalbikeshare-tripdata.zip",
         "202206-capitalbikeshare-tripdata.zip",
         "202207-capitalbikeshare-tripdata.zip"]

destination_dir = "../datasets"
print(f"Download files:")
for file in files:
    download_data(destination_dir=destination_dir, filename=file)
