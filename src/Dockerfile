FROM python:3.10

RUN apt-get update -y
RUN apt-get upgrade -y

WORKDIR /src

COPY ./requirements.txt ./
RUN pip install -r requirements.txt
COPY ./bank bank

CMD [ "python3", "bank/manage.py", "runserver", "0.0.0.0:8000" ]