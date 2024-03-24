FROM python:3.10

WORKDIR /app

COPY ./requirements.txt .

RUN pip install -r requirements.txt
# RUN playwright install chromium

COPY ./load_model.py .

RUN python3 load_model.py

COPY ./src /app/src

ENV WORKING_MODE="low-mem"

CMD [ "uvicorn","src.api.endpoints.main:app","--host","0.0.0.0","--port","8000" ]