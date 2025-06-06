FROM python:3.11-slim

WORKDIR /extract_app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p data logs

COPY . .

RUN echo 'alias extract_app="python /extract_app/main.py"' >> /root/.bashrc

CMD ["tail", "-f", "/dev/null"]