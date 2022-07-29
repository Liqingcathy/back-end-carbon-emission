FROM python:3
ADD . /capstone-backend
WORKDIR /capstone-backend
RUN pip install -r requirements.txt