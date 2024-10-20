<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Bug Bounty Framework</title>
</head>
<body>

<h1 align="center">🔍 Bug Bounty Framework</h1>
<p align="center">
    A comprehensive bug bounty framework for domain reconnaissance and vulnerability assessment, built using Python and FastAPI.
</p>

<div align="center">
    <img src="https://img.shields.io/badge/License-MIT-green.svg">
    <img src="https://img.shields.io/badge/Status-Development-blue.svg">
    <img src="https://img.shields.io/badge/Python-3.10+-brightgreen.svg">
</div>

<h2>🚀 Features</h2>
<ul>
    <li>Real-time WebSocket connection for interactive recon and live logs</li>
    <li>Domain enumeration using <code>subfinder</code></li>
    <li>Validation of subdomains using <code>curl</code>, with detailed status code handling and redirect support</li>
    <li>Comprehensive URL discovery using <code>Katana</code> with parameter filtering and cleanup</li>
    <li>XSS vulnerability scanning using <code>Dalfox</code> on discovered URLs</li>
    <li>Downloadable results including subdomains, alive subdomains, Katana output, and XSS scan results</li>
</ul>

<h2>📋 Table of Contents</h2>
<ol>
    <li><a href="#requirements">Requirements</a></li>
    <li><a href="#installation">Installation</a></li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#author">Author</a></li>
</ol>

<h2 id="requirements">🛠 Requirements</h2>
<ul>
    <li>Python 3.10+</li>
    <li><code>fastapi</code> - Web framework for building the API</li>
    <li><code>subfinder</code> - Subdomain enumeration tool</li>
    <li><code>curl</code> - HTTP client for validating subdomains</li>
    <li><code>katana</code> - URL enumeration tool</li>
    <li><code>dalfox</code> - XSS vulnerability scanner</li>
    <li><code>uvicorn</code> - ASGI server to run FastAPI</li>
</ul>

<h2 id="installation">📦 Installation</h2>
<pre>
git clone https://github.com/yourusername/bug-bounty-framework.git
cd bug-bounty-framework
pip install -r requirements.txt
</pre>

<h2 id="usage">📝 Usage</h2>
<p>To run the server:</p>
<pre>
python run.py
</pre>
<p>Navigate to <a href="http://localhost:8000">http://localhost:8000</a> and enter the target domain to start the recon process. The real-time logs will be displayed on the webpage, and the results can be downloaded directly.</p>

<h3>Endpoints</h3>
<ul>
    <li><code>GET /</code>: Serves the main HTML interface for starting recon.</li>
    <li><code>GET /download/{filename}</code>: Endpoint to download generated files (e.g., subdomains, alive subdomains).</li>
    <li><code>WebSocket /ws</code>: Real-time communication for handling domain input and streaming logs.</li>
</ul>

<h3>Real-time Log Streaming</h3>
<p>The WebSocket connection allows you to monitor the progress of the recon process, including:</p>
<ul>
    <li>Subdomain discovery using <code>subfinder</code></li>
    <li>Validation of alive subdomains using <code>curl</code></li>
    <li>URL discovery with <code>Katana</code> and cleanup of duplicate URLs</li>
    <li>XSS vulnerability detection using <code>Dalfox</code></li>
</ul>

<h3>File Downloads</h3>
<p>Upon completion of each stage, download links are made available for:</p>
<ul>
    <li>Discovered subdomains</li>
    <li>Validated alive subdomains</li>
    <li>Filtered Katana output</li>
    <li>XSS scan results</li>
</ul>

<h2 id="contributing">🤝 Contributing</h2>
<p>Contributions are welcome! Please follow these steps:</p>
<ol>
    <li>Fork the repository</li>
    <li>Create a new branch (<code>git checkout -b feature/YourFeature</code>)</li>
    <li>Commit your changes (<code>git commit -m 'Add new feature'</code>)</li>
    <li>Push to the branch (<code>git push origin feature/YourFeature</code>)</li>
    <li>Open a pull request</li>
</ol>

<h2 id="license">📄 License</h2>
<p>This project is licensed under the MIT License. See the <a href="LICENSE">LICENSE</a> file for details.</p>

<h2 id="author">👤 Author</h2>
<p>Marcos Ryan Foley Sanchez - <a href="[https://www.linkedin.com/in/yourprofile](https://www.linkedin.com/in/marcosfoley/)">LinkedIn</a></p>

<div align="center">
    <p>Made with ❤️ by Marcos Ryan Foley Sanchez</p>
</div>

</body>
</html>
