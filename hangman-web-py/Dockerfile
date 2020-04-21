FROM python:3.5-slim-buster

ADD requirements.txt /

RUN pip install --no-cache-dir -r /requirements.txt

COPY code/ /code/

ENV FLASK_APP=code/main.py

# CMD ["flask", "run", "--host=0.0.0.0"]
CMD ["tail", "-f", "/dev/null"]