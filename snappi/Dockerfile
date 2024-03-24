FROM python:3.10

RUN mkdir /snappi

WORKDIR /snappi

COPY requirements.txt .

RUN pip install -r requirements.txt

CMD ["tail","-f","/dev/null"]