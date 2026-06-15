# app/deepface_service/face_recognition.py
#
# Handles face enrollment and face verification using DeepFace (Facenet model).
#
# UPDATED: Face images are now stored in MongoDB as base64 strings
# (in employee's "face_images" array field), instead of being saved
# as files on the local filesystem. This makes the system production-safe
# since filesystem storage is not persistent on most cloud hosts.

import base64
import numpy as np
import cv2
from deepface import DeepFace
from app.database.connection import get_db
import os
import tempfile

_model_loaded = False

def preload_model():
    global _model_loaded
    if not _model_loaded:
        try:
            DeepFace.build_model("Facenet")
            _model_loaded = True
            print("✅ Facenet model loaded successfully")
        except Exception as e:
            print(f"⚠️ Model preload warning: {e}")


def _base64_to_temp_file(image_base64: str) -> str:
    """
    Helper: decodes a base64 image string and writes it to a temporary
    .jpg file on disk. Returns the temp file path.
    Caller is responsible for deleting the file after use.
    """
    image_data = base64.b64decode(image_base64.split(',')[-1])
    np_array = np.frombuffer(image_data, np.uint8)
    frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        cv2.imwrite(tmp.name, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        return tmp.name


async def verify_face_from_base64(image_base64: str):
    try:
        image_data = base64.b64decode(image_base64.split(',')[-1])
        np_array = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if frame is None:
            return None, "Invalid image"

        # Resize for faster processing
        max_size = 480
        h, w = frame.shape[:2]
        if w > max_size or h > max_size:
            scale = max_size / max(w, h)
            frame = cv2.resize(frame, (int(w * scale), int(h * scale)))

        # Detect face first
        faces = DeepFace.extract_faces(
            img_path=frame,
            detector_backend='opencv',
            enforce_detection=False
        )

        if len(faces) == 0:
            return None, "No face detected. Please face the camera directly."

        if len(faces) > 1:
            return None, "Multiple faces detected. Please ensure only one face is visible."

        # Fetch enrolled employees (face_images now contains base64 strings)
        db = get_db()
        employees = await db.employees.find(
            {"is_deleted": False, "status": "active", "face_images": {"$ne": []}}
        ).to_list(1000)

        if not employees:
            return None, "No employees enrolled in system"

        # Write the captured frame to a temp file (for DeepFace.verify input)
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            cv2.imwrite(tmp.name, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            tmp_path = tmp.name

        best_match = None
        best_distance = 0.5
        temp_files_to_cleanup = []

        try:
            for employee in employees:
                face_images = employee.get("face_images", [])
                # Only check first 3 stored images — faster
                for face_image_b64 in face_images[:3]:
                    enrolled_temp_path = None
                    try:
                        # Decode the stored base64 image into a temp file
                        enrolled_temp_path = _base64_to_temp_file(face_image_b64)
                        temp_files_to_cleanup.append(enrolled_temp_path)

                        result = DeepFace.verify(
                            img1_path=tmp_path,
                            img2_path=enrolled_temp_path,
                            model_name="Facenet",
                            detector_backend='opencv',
                            enforce_detection=False,
                            align=False
                        )
                        if result["verified"] and result["distance"] < best_distance:
                            best_distance = result["distance"]
                            best_match = employee
                            break  # Match found, move to next employee
                    except Exception:
                        continue

                if best_match:
                    break  # Match found, stop checking other employees
        finally:
            # Cleanup all temp files created for enrolled images
            for path in temp_files_to_cleanup:
                if os.path.exists(path):
                    os.unlink(path)
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        if best_match:
            return best_match, None
        return None, "Face not recognized. Please try again."

    except Exception as e:
        return None, str(e)


async def save_face_images(employee_id: str, images_base64: list):
    """
    Resizes and re-encodes each enrollment image, then stores them
    directly as base64 strings in the employee's MongoDB document
    (field: face_images). No files are written to disk.
    """
    db = get_db()
    saved_images_base64 = []

    for image_base64 in images_base64:
        try:
            image_data = base64.b64decode(image_base64.split(',')[-1])
            np_array = np.frombuffer(image_data, np.uint8)
            frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
            if frame is not None:
                frame = cv2.resize(frame, (160, 160))
                # Re-encode to JPEG bytes, then to base64 string for DB storage
                success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                if success:
                    encoded_str = base64.b64encode(buffer).decode('utf-8')
                    # Store with data URI prefix so it can be reused directly by frontend if needed
                    saved_images_base64.append(f"data:image/jpeg;base64,{encoded_str}")
        except Exception:
            continue

    await db.employees.update_one(
        {"employee_id": employee_id},
        {"$set": {"face_images": saved_images_base64}}
    )
    return saved_images_base64