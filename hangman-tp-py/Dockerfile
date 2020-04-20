FROM python:3.5-slim-buster

ADD requirements.txt /

RUN pip install --no-cache-dir -r /requirements.txt

COPY code/ /code/

CMD ["python3.5", "/code/main.py", "--validator", "tcp://validator:4004"]