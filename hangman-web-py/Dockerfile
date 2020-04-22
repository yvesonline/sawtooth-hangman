FROM python:3.5-slim-buster

ADD requirements.txt /

RUN pip install --no-cache-dir -r /requirements.txt

COPY code/ /code/

ENV FLASK_APP=code/main.py

CMD ["python3", "code/main.py"]