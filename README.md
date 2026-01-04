# RG PDF to Image Converter

A lightweight, high-performance web tool to convert PDF documents into images (PNG, JPEG, SVG). Built with **Python (Flask)** and **PyMuPDF**, this application is designed for speed and easy deployment to platforms like **Microsoft Azure** or **Lark Suite**.

## 🚀 Features

*   **Multiple Formats**: Convert PDFs to **PNG** (Best Quality), **JPEG** (Smallest Size), or **SVG** (Vector).
*   **Adjustable Quality**: Select common DPI settings ranging from Screen (72 DPI) to Print (300 DPI).
*   **Smart Downloading**:
    *   **Auto-Zip**: Automatically archives multi-page conversions into a single ZIP file.
    *   **Flexible Access**: Single-page documents can be downloaded directly as an image if preferred.
*   **Clean UI**: Simple, responsive web interface for easy uploading.
*   **Ready to Deploy**: Includes `Dockerfile` and `Procfile` for instant deployment to Azure, Heroku, or Docker containers.

## 🛠️ Usage

### Web Interface
1.  Upload a `.pdf` file.
2.  Select your desired **Format** and **Quality**.
3.  Click **Convert & Download**.

### API Endpoint
The application exposes a simple REST endpoint for programmatic use.

**POST** `/convert`

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `file` | File | Required | The PDF file to convert. |
| `format` | String | `png` | Output format: `png`, `jpg`, `svg`. |
| `dpi` | Integer | `200` | Resolution (e.g., 72, 150, 200, 300). |
| `use_zip` | Boolean | `true` | If `true`, output is zipped. If `false` (and single page), output is an image. |

## 💻 Local Development

### Prerequisites
*   Python 3.11+
*   pip

### Installation

1.  **Clone the repository**:
    ```bash
    git clone <your-repo-url>
    cd rg-pdf-converter
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application**:
    ```bash
    python app.py
    ```

4.  **Open in Browser**:
    Visit `http://localhost:5000`

## ☁️ Deployment

### Docker
Build and run the container locally:

```bash
docker build -t pdf-converter .
docker run -p 5000:5000 pdf-converter
```

### Microsoft Azure
This project is configured for **Azure Web Apps**:
1.  **VS Code**: Use the Azure App Service extension to "Deploy to Web App".
2.  **CLI**: Run `az webapp up --runtime "PYTHON:3.11" --sku F1`.

### Lark/Feishu Integration
To use this as a **Lark H5 App**:
1.  Deploy the app to a public HTTPS URL (e.g., Azure).
2.  In the Lark Developer Console, creat a "Custom App".
3.  Add the "Web App" feature and paste your deployment URL.