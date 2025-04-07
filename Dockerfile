FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 시스템 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    unzip \
    curl \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install 'whitenoise[brotli]' waitress django-extensions werkzeug pyOpenSSL

# 애플리케이션 코드 복사
COPY . .

# 로그 및 정적 파일 디렉토리 생성
RUN mkdir -p /app/logs /app/static /app/frontend /app/staticfiles /app/ssl

# SSL 인증서 생성
RUN openssl req -x509 -newkey rsa:4096 -nodes -out /app/ssl/cert.pem -keyout /app/ssl/key.pem -days 365 -subj '/CN=localhost'

# 환경 변수 설정 - Render 환경 시뮬레이션
ENV DEBUG="True"
ENV RENDER="true"
ENV RENDER_EXTERNAL_HOSTNAME="localhost"
ENV DATABASE_URL="sqlite:///db.sqlite3"
ENV DJANGO_SECRET_KEY="local-test-key-for-render-simulation"
ENV ALLOWED_HOSTS="localhost,127.0.0.1"
ENV CSRF_TRUSTED_ORIGINS="http://localhost:8000,http://127.0.0.1:8000"
ENV CORS_ALLOWED_ORIGINS="http://localhost:8000,http://127.0.0.1:8000"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 포트 노출
EXPOSE 8000

# Render 배포 시뮬레이션 스크립트
RUN echo '#!/bin/bash\n\
python manage.py collectstatic --no-input\n\
python manage.py migrate\n\
python manage.py runserver 0.0.0.0:8000\n\
' > /app/entrypoint.sh \
&& chmod +x /app/entrypoint.sh

# 애플리케이션 실행
CMD ["bash", "/app/entrypoint.sh"] 