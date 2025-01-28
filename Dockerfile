FROM python:3.13.1
WORKDIR /code
RUN pip install uv
ADD requirements.txt /code/requirements.txt
RUN pip install -r requirements.txt
ADD . /code
RUN pip install -e .