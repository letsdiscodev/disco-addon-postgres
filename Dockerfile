FROM python:3.12.3
WORKDIR /code
RUN pip install uv
ADD requirements.txt /code/requirements.txt
RUN pip install -r requirements.txt
ADD . /code
