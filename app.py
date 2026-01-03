import os
import io
import zipfile
from flask import Flask, request, send_file, jsonify

# -----------------------------------------------------------------------------
# PREREQUISITES for Web/Lark:
# You need a web framework (Flask) and the PDF library.
# Run: pip install flask pymupdf
# -----------------------------------------------------------------------------

try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError("PyMuPDF is missing. Run: pip install pymupdf")

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Simple endpoint to check if server is running."""
    return jsonify({"status": "active", "service": "PDF to Image Converter"})

@app.route('/convert', methods=['POST'])
def convert_pdf():
    """
    Endpoint for Lark App to upload a PDF.
    Returns a ZIP file containing all images.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "File must be a PDF"}), 400

    try:
        # Read file into memory (no need to save to disk for web apps)
        pdf_stream = file.read()
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        
        # Prepare a ZIP file in memory to return multiple images
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Get DPI from request or default to 200
            dpi = int(request.form.get('dpi', 200))
            zoom = dpi / 72
            matrix = fitz.Matrix(zoom, zoom)
            
            # Loop through pages
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=matrix)
                
                # Convert to PNG binary data
                img_data = pix.tobytes("png")
                
                # Add to zip
                filename = f"page_{page_num + 1:03d}.png"
                zip_file.writestr(filename, img_data)

        doc.close()
        
        # Finalize ZIP
        zip_buffer.seek(0)
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{os.path.splitext(file.filename)[0]}_images.zip"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # In a real production environment (like AWS/Heroku), 
    # you would use a WSGI server like Gunicorn instead of app.run()
    app.run(debug=True, port=5000)
