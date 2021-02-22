FROM firmwaredroid-base

WORKDIR /var/www/
COPY ./ /var/www/

CMD [ "gunicorn", "-w", "17", "--bind", "0.0.0.0:5000", "--worker-tmp-dir", "/dev/shm", "--chdir", "/var/www/", "--timeout", "300", "--worker-class", "gevent", "--threads", "12", "--log-level", "debug", "app:app"]