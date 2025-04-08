#!/bin/bash

# GitHub Actions 환경 테스트 스크립트
echo "=== GitHub Actions 환경 테스트 스크립트 ==="

# 현재 작업 디렉토리 출력
echo "현재 작업 디렉토리: $(pwd)"

# 환경 파일 존재 확인
if [ -f "env_configs/.env.production" ]; then
  echo "✅ env_configs/.env.production 파일이 존재합니다."
else
  echo "❌ env_configs/.env.production 파일이 존재하지 않습니다."
  mkdir -p env_configs
  echo "디렉토리 생성됨: env_configs"
  
  # 환경 파일 생성
  cat > env_configs/.env.production << 'EOF'
# Django 기본 설정
# 프로덕션 환경 설정
DEBUG=False

# Django SECRET_KEY
DJANGO_SECRET_KEY=ci-test-key-value

# 쉼표로 구분된 호스트 목록
ALLOWED_HOSTS=cvfactory.dev,www.cvfactory.dev,cvfactory.onrender.com

# API 키 설정 (API 엔드포인트 인증에 사용)
API_KEY=ci-test-api-key

# Groq API 설정
GROQ_API_KEY=ci-test-groq-key

# CSRF 설정
CSRF_USE_SESSIONS=False
CSRF_COOKIE_HTTPONLY=False
CSRF_COOKIE_SECURE=True
CSRF_COOKIE_SAMESITE=Lax
CSRF_TRUSTED_ORIGINS=https://cvfactory.dev,https://www.cvfactory.dev,https://cvfactory.onrender.com

# CORS 설정
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://cvfactory.dev,https://www.cvfactory.dev,https://cvfactory.onrender.com

# 보안 설정
ENABLE_CSRF_MIDDLEWARE=True

# 프로덕션 환경임을 표시
ENVIRONMENT=production
EOF
  echo "✅ env_configs/.env.production 파일이 생성되었습니다."
fi

# 환경 설정 파일 복사 및 추가 설정
cp env_configs/.env.production .env
echo "DEBUG=True" >> .env
echo "ALLOWED_HOSTS=localhost,127.0.0.1,testserver" >> .env
echo "DJANGO_SECRET_KEY=test-secret-key-for-ci" >> .env

echo "✅ .env 파일 생성 및 구성 완료"
echo "파일 내용 미리보기:"
grep -v "SECRET\|PASSWORD\|KEY" .env || echo "미리보기 실패"

echo "=== 테스트 완료 ==="
