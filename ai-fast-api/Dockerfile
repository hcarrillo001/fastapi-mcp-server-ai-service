#start from python base
FROM python:3.12

#change working dic
WORKDIR /code

# Install Node.js and npm
RUN apt-get update && apt-get install -y nodejs npm

RUN export SSL_CERT_FILE=$(python -m certifi)

#add requirements
COPY ./requirements.txt /code/requirements.txt

#install python libraries
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt



#append project and data directories to PYTHONPATH
#ENV PYTHONPATH "${PYTHONPATH}:/code/app"

#add python code
COPY ./app/ /code/app/

#specify default command
CMD ["fastapi", "run", "app/main.py", "--port", "80"]
