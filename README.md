# RG PDF to Image Converter

A professional, high-performance web tool to convert PDF documents into images (PNG, JPEG, SVG). Built with **Python (Flask)** and **PyMuPDF**, this application is designed for seamless integration with **Lark Suite** (Feishu), featuring Bot notifications, native mobile UI, and intelligent file handling.

## 🚀 Features

### Core Functionality
*   **Multiple Formats**: Convert PDFs to **PNG** (Best Quality), **JPEG** (Smallest Size), or **SVG** (Vector).
*   **Adjustable Quality**: Select DPI settings from Screen (72 DPI) to Print (300 DPI).
*   **Smart Downloading**:
    *   **Save As**: Uses the modern File System Access API to let users choose the download location (Supported Browsers).
    *   **Auto-Zip**: Automatically archives multi-page conversions.
*   **Intelligent Naming**: Output files replicate the original filename (e.g., `Report.pdf` -> `Report.zip`).

### Lark Suite Integration
*   **Bot Notifications**: Automatically messages the user on Lark when a conversion is complete.
*   **Native Mobile Experience**:
    *   **Responsive UI**: Shifts from a "Desktop Card" layout to a "Full-Screen App" layout on mobile.
    *   **Sticky Controls**: "Convert" button stays within thumb reach on phones.
*   **Security & Access**:
    *   **AppLink Redirect**: If accessed from a standard browser (Chrome/Edge), automatically redirects the user to open the specific **Lark AppLink**.
    *   **Identity**: Integrated OAuth2 login to identify the user for notifications.

## 🛠️ Usage

### Web Interface
1.  Open the app within **Lark/Feishu**.
2.  **Upload** your PDF.
3.  Select **Format** and **Quality**.
4.  Tap **Convert**.
5.  *Result*: The file is downloaded, and the Bot sends you a confirmation message!

## 💻 Local Development

### Prerequisites
*   Python 3.11+
*   Environment Variables (see below)

### Installation
1.  **Clone & Install**:
    ```bash
    git clone <your-repo-url>
    cd rg-pdf-converter
    pip install -r requirements.txt
    ```

2.  **Run**:
    ```bash
    python app.py
    ```

## ☁️ Deployment Configuration

To enable all features (Bot, Login, Notifications), you must configure the following **Environment Variables** in your deployment platform (Azure App Service, Docker, etc.):

| Variable | Description | Example |
| :--- | :--- | :--- |
| `LARK_APP_ID` | Your Lark App ID | `cli_a9dc...` |
| `LARK_APP_SECRET` | Your Lark App Secret | `HhKem...` |
| `LARK_REDIRECT_URI` | Callback URL for Login | `https://<your-app>.azurewebsites.net/callback` |
| `FLASK_SECRET_KEY` | Session Security Key | `(random string)` |

### Lark Console Setup
1.  **Permissions**: Add `im:message:send_as_bot` and `contact:user.id:readonly`.
2.  **Event Subscriptions**: Set Request URL to `https://<your-app>.azurewebsites.net/lark/events`.
3.  **Redirect URLs**: Add your callback URL.
4.  **Publish**: Create and release a version.

## 🐳 Docker
```bash
docker build -t pdf-converter .
docker run -p 5000:5000 --env-file .env pdf-converter
```