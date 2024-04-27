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

@app.route('/get-image', methods=['POST'])
def get_image():
    cache = CacheAccess()
    data = request.get_json()
    if not data or 'lat' not in data or 'lon' not in data:
        return jsonify({"error": "Latitude and longitude must be provided"}), 400
    lat = float(data['lat'])
    lon = float(data['lon'])
    lat_index, long_index = lat_lon_to_tile_index(lat, lon)

    cached_path = cache.get(lat_index, long_index, 2022, 1)
    if cached_path:
        return send_file(cached_path, mimetype='image/jpeg')

    size = 0.01

    bbox = [lon - size, lat - size, lon + size, lat + size]
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
                            "from": "2022-01-01T00:00:00Z",
                            "to": "2022-01-31T00:00:00Z"
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
        input: ["B02", "B03", "B04"],
        output: {
          bands: 3,
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

        image = Image.open(filename).convert('RGBA')

        predictor = ImagePredictor('./unet_rgb.weights.h5')
        mask = predictor.predict_mask(filename)

        # Resize mask to match the image size
        mask_image = Image.fromarray(mask)
        mask_image = mask_image.resize(image.size, Image.NEAREST)  # Resize the mask to match the image

        # Normalize and create RGBA mask
        normalized_mask = np.array(mask_image) / 255.0
        gradient_mask = np.zeros((image.height, image.width, 4), dtype=np.uint8)
        gradient_mask[..., 1] = 255  # Red channel
        gradient_mask[..., 3] = (normalized_mask * 255).astype(np.uint8)  # Alpha channel
        gradient_mask_image = Image.fromarray(gradient_mask, 'RGBA')

        # Composite the images
        overlayed_image = Image.alpha_composite(image, gradient_mask_image)
        overlayed_image = overlayed_image.convert('RGB')
        index_dir = Path("./cache") / Path(f"{lat_index}_{long_index}")
        print(index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)
        jpeg_image_path = index_dir / Path('overlayed_image.jpg')
        overlayed_image.save(jpeg_image_path, 'JPEG', quality=90)  # Save as JPEG with high quality

        return send_file(jpeg_image_path, mimetype='image/jpeg')
    else:
        return jsonify({"error": "Failed to fetch image: " + str(response.status_code)}), 500

@app.route("/")
def hello_world():
    return "Hello World"


if __name__ == '__main__':
    app.run(debug=True)