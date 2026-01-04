import os
import io
import zipfile
import requests
import json
from flask import Flask, request, send_file, jsonify, render_template, session, redirect, url_for

# -----------------------------------------------------------------------------
# PREREQUISITES:
# pip install flask pymupdf requests
# Set env vars: LARK_APP_ID, LARK_APP_SECRET
# -----------------------------------------------------------------------------

try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError("PyMuPDF is missing. Run: pip install pymupdf")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-in-prod")

# Lark Configuration
LARK_APP_ID = os.environ.get("LARK_APP_ID", "cli_a9dc3e836cf8de1a")
LARK_APP_SECRET = os.environ.get("LARK_APP_SECRET", "HhKemh5woyoZBJCjUrqXwbRRvogvrV81")
# Note: For production, this should be your actual domain callback
# e.g., https://your-app.azurewebsites.net/callback
LARK_REDIRECT_URI = os.environ.get("LARK_REDIRECT_URI", "http://localhost:5000/callback")

@app.before_request
def restrict_to_lark_app():
    """Restricts access to Lark/Feishu clients only."""
    # Allow health checks interactions and Lark Verification/Callback
    if request.path in ['/health', '/lark/events', '/callback']:
        return None

    # Check User-Agent
    ua = request.headers.get('User-Agent', '')
    if 'Lark' not in ua and 'Feishu' not in ua:
        # Optional: Allow local dev testing if needed
        # return None 
        return """
        <div style="font-family: sans-serif; text-align: center; margin-top: 50px;">
            <h1>Access Restricted</h1>
            <p>This tool is only accessible internally within the Lark / Feishu Suite.</p>
            <p style="color: gray;">Please open this app from your Workspace.</p>
        </div>
        """, 403

def get_tenant_access_token():
    """Gets the internal tenant access token for Bot operations."""
    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    payload = {
        "app_id": LARK_APP_ID,
        "app_secret": LARK_APP_SECRET
    }
    try:
        resp = requests.post(url, headers=headers, json=payload)
        data = resp.json()
        if data.get("code") == 0:
            return data.get("tenant_access_token")
        else:
            print(f"Error getting token: {data}")
            return None
    except Exception as e:
        print(f"Exception getting token: {e}")
        return None

def send_lark_notification(user_open_id, filename):
    """Sends a conversion complete message to the user via Bot."""
    token = get_tenant_access_token()
    if not token:
        return

    url = "https://open.larksuite.com/open-apis/im/v1/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    # Message Content (Post type)
    content = {
        "zh_cn": {
            "title": "Conversion Complete",
            "content": [
                [
                    {"tag": "text", "text": f"Your file "},
                    {"tag": "text", "text": filename, "style": ["bold"]},
                    {"tag": "text", "text": " has been successfully converted and downloaded."}
                ]
            ]
        }
    }

    payload = {
        "receive_id": user_open_id,
        "msg_type": "post",
        "content": json.dumps(content)
    }
    
    # We use open_id as the receive_id_type
    params = {"receive_id_type": "open_id"}

    try:
        requests.post(url, headers=headers, params=params, json=payload)
    except Exception as e:
        print(f"Failed to send notification: {e}")


@app.route('/login')
def login():
    """Redirects to Lark OAuth."""
    # Docs: https://open.larksuite.com/document/common-capabilities/sso/web-application-sso/login-process
    auth_url = (
        f"https://open.larksuite.com/open-apis/authen/v1/authorize?"
        f"app_id={LARK_APP_ID}&"
        f"redirect_uri={LARK_REDIRECT_URI}&"
        f"scope=contact:user.id:readonly&"
        f"state=RANDOM_STATE"
    )
    return redirect(auth_url)

@app.route('/callback')
def callback():
    """Handles OAuth callback."""
    code = request.args.get('code')
    if not code:
        return "No code provided", 400

    # Exchange code for user_access_token to get open_id
    url = "https://open.larksuite.com/open-apis/authen/v1/oidc/access_token"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    
    # Get app_access_token (needed for OIDC in some flows, but commonly app_access_token)
    # Actually simpler endpoint for internal apps: 
    # authen/v1/oidc/access_token needs app_access_token.
    # Let's use the simpler v3 token endpoint or just internal logic.
    
    # Getting app_token first
    app_token = get_tenant_access_token() # Roughly same for internal
    if not app_token:
        return "Failed to get app token", 500

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "app_access_token": app_token
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload)
        data = resp.json()
        if data.get("code") == 0:
            # Success
            session['user_open_id'] = data.get('data', {}).get('open_id')
            session['user_name'] = data.get('data', {}).get('name', 'User')  # Might not be in OIDC standard
            return redirect(url_for('index'))
        else:
            return f"Login failed: {data.get('msg')}", 400
    except Exception as e:
        return f"Login error: {str(e)}", 500

@app.route('/lark/events', methods=['POST'])
def lark_events():
    """Handles Lark Event Subscriptions (Verification Challenge)."""
    try:
        data = request.get_json()
        if not data:
            return "No data", 400
        
        # Handle URL Verification Challenge
        if data.get("type") == "url_verification":
            return jsonify({"challenge": data.get("challenge")})
            
        # Handle other events suitable for future expansion
        # e.g. receiving messages
        
        return jsonify({"msg": "ok"})
    except Exception as e:
        print(f"Event error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/', methods=['GET'])
def index():
    """Renders the frontend UI."""
    user = session.get('user_open_id')
    return render_template('index.html', user=user)

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

        # Notify functionality
        if 'user_open_id' in session:
            # We assume notification is fire-and-forget
            # In production, use a background task (e.g. celery) to avoid delaying response
            send_lark_notification(session['user_open_id'], file.filename)


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
