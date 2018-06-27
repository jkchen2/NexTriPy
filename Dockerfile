FROM python:3.6.5-alpine

COPY server.py /server.py
RUN pip install --upgrade \
    flask \
    https://github.com/jkchen2/NexTriPy/tarball/master

ENTRYPOINT ["python", "server.py"]
