FROM python:3.5-slim-buster

ADD requirements.txt /

RUN pip install --no-cache-dir -r /requirements.txt

COPY code/ /code/

RUN chmod +x code/hmcli.py

CMD ["tail", "-f", "/dev/null"]