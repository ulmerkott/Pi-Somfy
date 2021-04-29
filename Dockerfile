FROM balenalib/raspberry-pi-debian-python:latest

WORKDIR /app
COPY ./ ./

RUN [ "cross-build-start" ]

# ephem needs gcc (in build-essential package)
RUN install_packages gcc libc-dev pigpio
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get remove gcc libc-dev && apt autoremove

RUN [ "cross-build-end" ]

CMD [ "python", "./operateShutters.py", "-auto", "-mqtt" ]