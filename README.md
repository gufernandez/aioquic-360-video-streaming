# 360º Video Streaming over QUIC
## Repository setup

### 1. Start working through `$ git clone`
Clone the repo with:
   - With https: `$ git clone https://github.com/gufernandez/aioquic-360-video-streaming`
   - Or ssh: `$ git clone ssh:git@github.com/gufernandez/aioquic-360-video-streaming`

## Environment setup
### 1. Install Python 3 in your favorite distribution (I'm currently using Python 3.6.9)
### 2. Use Python virtual environment for a better package management
  - Install python3-venv
  - Create a virtual environment on the project root: `$ python3 -m venv venv`
  - Activate it: `$ source venv/bin/activate`
### 3. Install the project dependencies
  - Update pip if necessary: `$ pip install --upgrade pip`
  - Install the requirements: `$ pip install -r requirements.txt`
### 4. You're ready to work!

## Running the application
### 1. Running the Server
The command to run the server is:

`$ python3 server.py [-h] -c PATH/TO/CERTIFICATE [--host HOST] [--port PORT] -k PATH/TO/PRIVATE_KEY [-q QUEUE]`

Example:

`$ python3 server.py -c '../cert/ssl_cert.pem' -k '../cert/ssl_key.pem -q 'SP'`

### 2. Running the Client
The command to run the client is:

`$ python3 client.py [-h] [-c PATH/TO/CA_CERTS] -i USER_INPUT_FILE url`

Example:

`$ python3 client.py -c '../cert/pycacert.pem' -i '../data/user_input.csv' "wss://127.0.0.1:4433"`
