FROM localhost:5000/continuumio/miniconda3

WORKDIR /app

RUN apt-get update

RUN apt-get install sqlite3

RUN git clone https://github.com/AliSajid/fbise.git

RUN pip install -r fbise/requirements.txt

CMD ["python", "/app/fbise/downloader.py"]