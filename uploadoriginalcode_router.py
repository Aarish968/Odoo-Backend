from fastapi import APIRouter, HTTPException, Depends, Form, UploadFile, File
from pwp_core.database import DbSession, get_transaction as get_tran
from peerworker_fe_api.model.service.uploadoriginalcodeservice import get_details, get_file_hash, extract_zip, insert_files_in_db
from peerworker_fe_api.webapi.fe.upload_original_code_schema import FileDetailData, FileDetailsResponse
from pwp_core.logger import getLogger
import os
import tempfile
from pwp_core_webapi.webapi.domain_router import DomainRouter


logger = getLogger()
domain_router = DomainRouter(prefix="/fe/webapp")
router: APIRouter = domain_router.router

# # Endpoint to get file details based on project_id
# @router.post("/get_file_details/", response_model=FileDetailsResponse)
# async def extract_zip_api(
#     project_id: int,
#     db: DbSession = Depends(get_tran),
# ):
#     try:
#         # Fetch existing file details from the database
#         files_details, records, remarks = get_details(db, project_id)

#         return FileDetailsResponse(
#             data=FileDetailData(files=files_details, count=records),
#             status="SUCCESS",
#             remarks=remarks,
#         )
#     except Exception as e:
#         logger.error(f"An error occurred: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))


# Endpoint to upload ZIP, extract files and update/insert in DB
@router.post("/upload-zip/")
async def upload_zip(
    project_id:int = Form(...),  # Accept project_id as a form parameter
    file: UploadFile = File(...),  # Accept the ZIP file to be uploaded
    db: DbSession = Depends(get_tran)  # Dependency for database session
):
    """API to upload and extract a ZIP file, and update/insert records in the DB based on the ZIP contents."""

    try:
        # Ensure that project_id and file are provided
        if not project_id:
            raise HTTPException(status_code=400, detail="Project ID is required")

        if not file:
            raise HTTPException(status_code=400, detail="File is required")

        # Create a temporary directory to store the uploaded ZIP file
        temp_dir = tempfile.mkdtemp()

        # Define the path where the ZIP will be saved
        zip_path = os.path.join(temp_dir, file.filename)

        # Save the uploaded ZIP file to the temporary directory
        with open(zip_path, "wb") as buffer:
            buffer.write(await file.read())

        # Insert or update records in the database based on the contents of the ZIP
        insert_files_in_db(db, project_id, zip_path)

        # Extract file paths from the ZIP file
        file_paths = extract_zip(zip_path)

        return {"message": "ZIP file processed successfully!", "file_paths": file_paths}

    except Exception as e:
        logger.error(f"An error occurred during upload or file update/insertion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
