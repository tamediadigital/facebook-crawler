FROM ubuntu:22.04

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get -y install python3-pip libnss3 libasound2 libatspi2.0-0 libdrm2 libgbm1 libgtk-3-0 libxkbcommon-x11-0  \
    libx11-xcb1 libdbus-glib-1-dev dumb-init

WORKDIR /facebook-crawler
COPY requirements.txt .

ENV PLAYWRIGHT_BROWSERS_PATH=/facebook-crawler/browsers

RUN pip install -r requirements.txt
RUN python3 -m playwright install firefox

COPY . .

RUN addgroup --gid 223344 facebook
RUN useradd -m --uid 223344 --gid 223344 facebook
RUN chown -R facebook:facebook /facebook-crawler


USER facebook

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["/facebook-crawler/run_spiders.sh"]
