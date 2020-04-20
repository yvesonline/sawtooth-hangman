FROM python:3.5-slim-buster

ADD requirements.txt /

RUN pip install --no-cache-dir -r /requirements.txt

COPY code/ /code/

CMD ["tail", "-f", "/dev/null"]