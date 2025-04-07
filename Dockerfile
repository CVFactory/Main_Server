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

# 환경 변수 설정 - 프로덕션 환경
ENV DEBUG="False"
ENV RENDER="true"
ENV RENDER_EXTERNAL_HOSTNAME="cvfactory.dev"
ENV DATABASE_URL="sqlite:///db.sqlite3"
ENV DJANGO_SECRET_KEY="production-secret-key-change-this"
ENV ALLOWED_HOSTS="cvfactory.dev,www.cvfactory.dev"
ENV CSRF_TRUSTED_ORIGINS="https://cvfactory.dev,https://www.cvfactory.dev"
ENV CORS_ALLOWED_ORIGINS="https://cvfactory.dev,https://www.cvfactory.dev"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 포트 노출
EXPOSE 8000

# 프로덕션 서버 실행 스크립트
RUN echo '#!/bin/bash\n\
python manage.py collectstatic --no-input\n\
python manage.py migrate\n\
waitress-serve --port=8000 cvfactory.wsgi:application\n\
' > /app/entrypoint.sh \
&& chmod +x /app/entrypoint.sh

# 애플리케이션 실행
CMD ["bash", "/app/entrypoint.sh"] 