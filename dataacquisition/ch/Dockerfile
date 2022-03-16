FROM python:3.10-slim

WORKDIR /src

COPY ./getData.py  ./requirements.txt ./
COPY ./ch ./

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "/src/wikipedia_script_ch.py"]