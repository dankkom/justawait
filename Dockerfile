FROM python:3-slim
COPY . ./
RUN pip install -r requirements.txt
EXPOSE 5000
CMD gunicorn --bind :5000 justawait:app
