FROM python:3.13-slim

RUN apt-get update && \
    apt-get -y install gcc build-essential && \
    apt-get clean autoclean --yes && \
    apt-get autoremove --yes && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/

WORKDIR /usr/src/benchmarks

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY regression_test.py ./

CMD ["python", "regression_test.py"]
