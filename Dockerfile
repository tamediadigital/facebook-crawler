FROM python:3.8

WORKDIR /facebook-crawler

COPY /requirements.txt .

RUN apt update && apt -y install libnss3 libasound2 libatspi2.0-0 libdrm2 libgbm1 libgtk-3-0 libxkbcommon-x11-0 libx11-xcb1 libdbus-glib-1-dev &&\
    pip3 install -r requirements.txt &&\
    python -m playwright install firefox

COPY . .

CMD ["python", "main.py"]
