Setup and Running Instructions:
Create the Project Directory:

mkdir -p /home/goombah/Desktop/Documents/code/OrderBuddy/backend/app
mkdir -p /home/goombah/Desktop/Documents/code/OrderBuddy/backend/trained_nlu_model
mkdir -p /home/goombah/Desktop/Documents/code/OrderBuddy/asr_service/app
mkdir -p /home/goombah/Desktop/Documents/code/OrderBuddy/asr_service/models
mkdir -p /home/goombah/Desktop/Documents/code/OrderBuddy/nlu_service/app
mkdir -p /home/goombah/Desktop/Documents/code/OrderBuddy/nlu_service/training_data
mkdir -p /home/goombah/Desktop/Documents/code/OrderBuddy/frontend
mkdir -p /home/goombah/Desktop/Documents/code/OrderBuddy/data # For SQLite DB persistence
mkdir -p /home/goombah/Desktop/Documents/code/OrderBuddy/menu_data

Copy the Files:
Copy the content of each code block above into its respective file within the OrderBuddy directory structure.

Install Docker and Docker Compose:
If you haven't already, install Docker and Docker Compose on your Linux Mint server.

Install Docker Engine: Follow the official Docker documentation for Ubuntu (Mint is based on Ubuntu).

sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

Add your user to the docker group (to run Docker commands without sudo):

sudo usermod -aG docker $USER
newgrp docker # Apply group changes immediately (or log out/in)

Verify Docker installation: docker run hello-world

Train the NLU Model:
Navigate to the nlu_service directory and run the training script. This will generate the trained_nlu_model directory inside backend/.

cd /home/goombah/Desktop/Documents/code/OrderBuddy/nlu_service/
python train_nlu.py

Important: This step creates the trained_nlu_model directory. Ensure it's created successfully.

Build and Run the Docker Containers:
Navigate to the root OrderBuddy directory (where docker-compose.yml is located).

cd /home/goombah/Desktop/Documents/code/OrderBuddy/
docker-compose build
docker-compose up -d

The docker-compose build command will take some time, especially for the asr_service as it downloads the Whisper model.

docker-compose up -d will start all services in the background.

Access the Web App:

Find your Linux server's IP address (e.g., run ip a in your terminal and look for the IP under your active network interface, usually eth0 or wlp...).

On your Android tablet, open a web browser and navigate to http://YOUR_SERVER_IP:8001 (replace YOUR_SERVER_IP with the actual IP address of your Linux Mint server).

To Stop the Services:
Navigate to the OrderBuddy directory and run:

docker-compose down

This comprehensive setup should get your OrderBuddy system up and running! Remember to adjust the BACKEND_URL in frontend/script.js to match your server's IP address.