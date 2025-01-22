from flask import Flask, request, jsonify, send_file
from rembg import remove
from PIL import Image
import io
import os

app = Flask(__name__)

class ImageProcessor:
    def __init__(self):
        self.max_size = 1024

    def optimize_image(self, image):
        temp_buffer = io.BytesIO()
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image.save(temp_buffer, format='JPEG', optimize=True, progressive=True)
        temp_buffer.seek(0)
        return Image.open(temp_buffer)

    def compress_and_resize(self, image):
        if max(image.size) > self.max_size:
            ratio = self.max_size / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        return self.optimize_image(image)

    def process_image(self, input_path):
        with open(input_path, 'rb') as input_file:
            input_image = input_file.read()
            output_image = remove(input_image)
        image = Image.open(io.BytesIO(output_image))
        image = self.compress_and_resize(image)
        output_buffer = io.BytesIO()
        image.save(output_buffer, format='JPEG', optimize=True)
        output_buffer.seek(0)
        return output_buffer

processor = ImageProcessor()

@app.route('/')
def home():
    return "Image Processing API is running!"

@app.route('/process-image', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    image_file = request.files['image']
    input_path = f"temp_{image_file.filename}"
    image_file.save(input_path)
    try:
        output_buffer = processor.process_image(input_path)
        os.remove(input_path)
        return send_file(output_buffer, mimetype='image/jpeg', as_attachment=True, download_name='processed_image.jpg')
    except Exception as e:
        if os.path.exists(input_path):
            os.remove(input_path)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
