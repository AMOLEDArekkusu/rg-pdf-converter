import os
import io
import zipfile
from flask import Flask, request, send_file, jsonify, render_template

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

@app.before_request
def restrict_to_lark_app():
    """Restricts access to Lark/Feishu clients only."""
    # Allow health checks interactions
    if request.path == '/health':
        return None

    # Check User-Agent
    ua = request.headers.get('User-Agent', '')
    if 'Lark' not in ua and 'Feishu' not in ua:
        return """
        <div style="font-family: sans-serif; text-align: center; margin-top: 50px;">
            <h1>Access Restricted</h1>
            <p>This tool is only accessible internally within the Lark / Feishu Suite.</p>
            <p style="color: gray;">Please open this app from your Workspace.</p>
        </div>
        """, 403

@app.route('/', methods=['GET'])
def index():
    """Renders the frontend UI."""
    return render_template('index.html')

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
        # Read file into memory
        pdf_stream = file.read()
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        
        # Get Options
        output_format = request.form.get('format', 'png').lower()
        use_zip = request.form.get('use_zip', 'true') == 'true'
        dpi = int(request.form.get('dpi', 200))
        
        # Base filename without extension
        base_filename = os.path.splitext(file.filename)[0]

        files_to_return = [] # List of (filename, bytes, mimetype)

        # Process Pages
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            if output_format == 'svg':
                content = page.get_svg_image()
                # SVG returns string, convert to bytes
                content = content.encode('utf-8')
                ext = 'svg'
                mime = 'image/svg+xml'
            else:
                # Raster formats (PNG, JPEG)
                zoom = dpi / 72
                matrix = fitz.Matrix(zoom, zoom)
                
                # Check for JPEG specific handling (needs no alpha)
                alpha = True
                if output_format in ['jpg', 'jpeg']:
                    alpha = False
                    ext = 'jpg'
                    mime = 'image/jpeg'
                else:
                    ext = 'png'
                    mime = 'image/png'

                pix = page.get_pixmap(matrix=matrix, alpha=alpha)
                content = pix.tobytes(ext)

            # Define per-page filename
            # If single page, just use base name. If multi, add page number.
            if len(doc) == 1:
                page_filename = f"{base_filename}.{ext}"
            else:
                page_filename = f"{base_filename}_page_{page_num + 1:03d}.{ext}"
            
            files_to_return.append({
                'name': page_filename,
                'data': content,
                'mime': mime
            })

        doc.close()

        # Decision: Zip or Single File
        # Force zip if multiple files, otherwise respect user choice
        should_zip = use_zip or len(files_to_return) > 1

        if should_zip:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for item in files_to_return:
                    zip_file.writestr(item['name'], item['data'])
            
            zip_buffer.seek(0)
            return send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name=f"{base_filename}_images.zip"
            )
        else:
            # Return single file
            single_file = files_to_return[0]
            return send_file(
                io.BytesIO(single_file['data']),
                mimetype=single_file['mime'],
                as_attachment=True,
                download_name=single_file['name']
            )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # In a real production environment (like AWS/Heroku), 
    # you would use a WSGI server like Gunicorn instead of app.run()
    app.run(debug=True, port=5000)
