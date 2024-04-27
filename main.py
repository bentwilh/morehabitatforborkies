import os
from pathlib import Path
from flask import Flask, request, send_file, jsonify
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import json
from PIL import Image
import numpy as np
import math
from predictor import ImagePredictor
from cacheAccess import CacheAccess
from dotenv import load_dotenv
from datetime import datetime
from dateutil.relativedelta import relativedelta
import base64
import logging

# Configure logging
#logging.basicConfig(filename='image_analysis.log', level=logging.INFO, 
#                    format='%(asctime)s:%(levelname)s:%(message)s')



load_dotenv()

app = Flask(__name__)

def get_oauth_session():
    client = BackendApplicationClient(client_id=os.environ.get("CLIENT_ID"))
    oauth = OAuth2Session(client=client)
    return oauth


def get_token(oauth):
    return oauth.fetch_token(
        token_url='https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token',
        client_secret=os.environ.get("CLIENT_SECRET"), include_client_id=True)

#Intermediate Step
def lat_lon_to_tile_index(lat, lon, tile_size_km=10):
        km_per_degree_lat = 111  # Approximate conversion factor for latitude to km
        min_latitude = -90       # Minimum latitude
        min_longitude = -180     # Minimum longitude
        
        # Calculate the degree conversion for longitude at the given latitude
        km_per_degree_lon = km_per_degree_lat * math.cos(math.radians(lat))
        
        # Calculate tile indices
        lat_index = int((lat - min_latitude) * km_per_degree_lat / tile_size_km)
        lon_index = int((lon - min_longitude) * km_per_degree_lon / tile_size_km)
        
        return lat_index, lon_index

def validate_data(data):
    keys_to_check = ['lat', 'lon', 'start_year', 'start_month', 'end_year', 'end_month']
    if not all(key in data for key in keys_to_check):
        print("Some Key missing")
        return False
    try:
        lat = float(data['lat'])
        lon = float(data['lon'])

        start_year = int(data['start_year'])
        start_month = int(data['start_month'])
        end_year = int(data['end_year'])
        end_month = int(data['end_month'])

        start_date = datetime(start_year, start_month, 1)
        end_date = datetime(end_year, end_month, 28)
        if start_date>=end_date:
            print("Invalid Time 1")
            return False

        min_date = datetime(2015, 1, 1)
        max_date = datetime(2025, 12, 31)
        if not (min_date <= start_date <= max_date and min_date <= end_date <= max_date):
            print("Invalid Time 2")
            return False
        return True
    except ValueError as e:
        print("Parsing failed")
        return False

def generate_file_paths(lat_index, long_index, start_year, start_month, end_year, end_month):
    start_date = datetime(start_year, start_month, 1)
    end_date = datetime(end_year, end_month, 1)
    
    current_date = start_date
    file_paths = []
    
    while current_date <= end_date:
        file_name = f"cache/{lat_index}_{long_index}/{current_date.strftime('%Y_%m')}.jpg"
        file_paths.append(file_name)
        
        current_date += relativedelta(months=1)
    
    return file_paths

def generate_json_from_complete_paths(file_paths):
    files_data = {}
    
    for file_path in file_paths:
        with open(file_path, 'rb') as file:
            file_content = file.read()
            encoded_content = base64.b64encode(file_content).decode('utf-8')
            files_data[file_path] = encoded_content
    
    return jsonify(files_data)

@app.route('/get-image', methods=['POST'])
def get_image():
    cache = CacheAccess()
    data = request.get_json()
    if not validate_data(data):
        return jsonify({"error": "Something is wrong, I can feel it"}), 400
    lat = float(data['lat'])
    lon = float(data['lon'])
    start_year = int(data['start_year'])
    start_month = int(data['start_month'])
    end_year = int(data['end_year'])
    end_month = int(data['end_month'])
    start_date = datetime(start_year, start_month, 1)
    end_date = datetime(end_year, end_month, 28)
    lat_index, long_index = lat_lon_to_tile_index(lat, lon)
    desired_paths = generate_file_paths(lat_index, long_index, start_year, start_month, end_year, end_month)
    cached_paths = cache.get(lat_index, long_index, start_year, start_month, end_year, end_month)
    if cached_paths and all(des in cached_paths for des in desired_paths):
        return generate_json_from_complete_paths(cached_paths)
    
    toGenerate = [des for des in desired_paths if not des in cached_paths]

    size = 0.01

    bbox = [lon - size, lat - size, lon + size, lat + size]
    for pathToGen in toGenerate:

        yearToGen, monthToGen = pathToGen.split('/')[2].split('_')
        monthToGen = monthToGen.split(".")[0]
        date_str_start = f"{yearToGen}-{int(monthToGen):02d}-01T00:00:00Z"
        date_str_end = f"{yearToGen}-{int(monthToGen):02d}-28T00:00:00Z"
        request_payload = {
            "input": {
                "bounds": {
                    "properties": {
                        "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
                    },
                    "bbox": bbox
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": date_str_start,
                                "to": date_str_end
                            }
                        }
                    }
                ]
            },
            "output": {
                "width": 1024,
                "height": 1024,
                "format": "TIFF"
            }
        }

        evalscript = """
        //VERSION=3
        function setup() {
        return {
            input: ["B02", "B03", "B04", "CLP"],
            output: {
            bands: 4,
            sampleType: "AUTO",
            format: "TIFF"
            }
        }
        }

        function evaluatePixel(sample) {
        return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02];
        }
        """

        oauth = get_oauth_session()
        token = get_token(oauth)
        response = oauth.post('https://services.sentinel-hub.com/api/v1/process',
                            files={'request': (None, json.dumps(request_payload), 'application/json'),
                                    'evalscript': (None, evalscript, 'application/javascript')})
        if response.ok:
            filename = 'output_image.tiff'
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            
            image = Image.open(filename)

            image_array = np.asarray(image)
            if np.mean(image_array[3])>100:
                continue            
            
            image = Image.open(filename).convert('RGBA')
            
            predictor = ImagePredictor('./unet_rgb.weights.h5')
            mask = predictor.predict_mask(filename)
            #logging.info(f"Image details - Mode: {image.mode}, Size: {image.size}")

            # Use the predictor to generate a mask
            predictor = ImagePredictor('./unet_rgb.weights.h5')
            mask = predictor.predict_mask(filename)

            # Convert mask to a numpy array for analysis (assuming it's not already one)
            if not isinstance(mask, np.ndarray):
                mask = np.array(mask)

            # Log mask details
            #logging.info(f"Mask shape: {mask.shape}")
            #logging.info(f"Mask dtype: {mask.dtype}")
            #logging.info(f"Mask min value: {np.min(mask)}")
            #logging.info(f"Mask max value: {np.max(mask)}")
            #logging.info("Mask sample values: " + str(mask.flatten()[:10]))  # Example: log first 10 values

            # Analysis of mask data
            unique_values, counts = np.unique(mask, return_counts=True)
            #logging.info(f"Unique mask values: {dict(zip(unique_values, counts))}")

            # Resize mask to match the image size
            mask_image = Image.fromarray(mask)
            mask_image = mask_image.resize(image.size, Image.NEAREST)  # Resize the mask to match the image

            # Normalize and create RGBA mask
            normalized_mask = np.array(mask_image) / 255.0
            gradient_mask = np.zeros((image.height, image.width, 4), dtype=np.uint8)
            gradient_mask[..., 1] = 255  # Red channel
            gradient_mask[..., 3] = (normalized_mask * 255).astype(np.uint8) 
            gradient_mask_image = Image.fromarray(gradient_mask, 'RGBA')

            # Composite the images
            overlayed_image = Image.alpha_composite(image, gradient_mask_image)
            image = image.convert('RGB')#REMOVE
            image.save(f"{yearToGen}_{monthToGen}.jpg", 'JPEG', quality=90)#REMOVE

            overlayed_image = overlayed_image.convert('RGB')
            index_dir = Path(f"./cache/{lat_index}_{long_index}")
            index_dir.mkdir(parents=True, exist_ok=True)
            jpeg_image_path = index_dir / Path(f'{yearToGen}_{monthToGen}.jpg')
            overlayed_image.save(jpeg_image_path, 'JPEG', quality=90)  
        else:
            return jsonify({"error": "Failed to fetch image: " + str(response.status_code)}), 500
    return generate_json_from_complete_paths(cached_paths_refresh)



@app.route("/")
def hello_world():
    return "Hello World"


if __name__ == '__main__':
    app.run(debug=True)