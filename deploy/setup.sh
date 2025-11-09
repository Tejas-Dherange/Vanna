#!/bin/bash

# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install Python and required system packages
sudo apt-get install -y python3.11 python3.11-venv python3-pip nginx

# Create project directory
mkdir -p ~/vanna_v2

# Create and activate virtual environment
python3 -m venv ~/vanna_v2/venv
source ~/vanna_v2/venv/bin/activate

# Install required packages
pip install --upgrade pip
pip install 'vanna[fastapi,gemini] @ git+https://github.com/vanna-ai/vanna.git@v2'
pip install psycopg2-binary python-dotenv uvicorn gunicorn requests

# Setup systemd service
sudo cp /home/ubuntu/vanna_v2/deploy/vanna.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vanna
sudo systemctl start vanna

# Setup Nginx
sudo tee /etc/nginx/sites-available/vanna << EOF
server {
    listen 80;
    server_name your_domain_or_ip;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

# Enable nginx site
sudo ln -s /etc/nginx/sites-available/vanna /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx