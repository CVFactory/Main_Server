import os
from dotenv import load_dotenv
import groq
import re
import logging
import json
from datetime import datetime
import traceback
import inspect
import sys
from django.conf import settings

# 로거 설정
logger = logging.getLogger("api")

# groq_service 전용 로거 설정
groq_logger = logging.getLogger("groq_service")

# 개발 환경에서만 디버그 메시지 출력
if settings.DEBUG:
    # 파일 핸들러 설정
    log_dir = os.path.join("logs")
    os.makedirs(log_dir, exist_ok=True)  # 로그 디렉토리 확인
    
    groq_handler = logging.FileHandler(os.path.join(log_dir, "groq_service_debug.log"), encoding='utf-8')
    groq_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s [%(name)s] - %(message)s'))
    groq_logger.addHandler(groq_handler)
    
    groq_logger.debug("=== Groq 서비스 디버그 모드로 시작 ===")
    groq_logger.debug(f"로그 레벨: {logging.getLevelName(groq_logger.level)}")

# .env 파일 로드
load_dotenv()

# Groq API 키 설정
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    error_msg = "Groq API Key가 설정되지 않았습니다."
    groq_logger.error(error_msg)
    raise ValueError(error_msg)

# 패키지 버전 정보 로깅
groq_logger.info(f"Python 버전: {sys.version}")
groq_logger.info(f"Groq 모듈 버전: {getattr(groq, '__version__', '버전 정보 없음')}")
groq_logger.info(f"Groq 모듈 경로: {getattr(groq, '__file__', '파일 경로 정보 없음')}")

# Groq 클라이언트 초기화 파라미터 검사
try:
    groq_logger.info("Groq Client 초기화 파라미터 검사 시작")
    client_init_params = inspect.signature(groq.Client.__init__).parameters
    groq_logger.info(f"Groq.Client.__init__ 파라미터 목록: {list(client_init_params.keys())}")
    
    # 상속 관계 확인
    groq_logger.info("Groq Client 클래스 계층 구조 검사")
    mro = groq.Client.__mro__
    groq_logger.info(f"상속 계층: {[cls.__name__ for cls in mro]}")
    
    # 모든 상위 클래스의 __init__ 파라미터 검사
    for cls in mro:
        if cls == object:
            continue
        try:
            init_sig = inspect.signature(cls.__init__)
            groq_logger.info(f"{cls.__name__}.__init__ 파라미터: {list(init_sig.parameters.keys())}")
        except (ValueError, TypeError) as e:
            groq_logger.info(f"{cls.__name__}.__init__ 시그니처 검사 실패: {e}")
except Exception as e:
    groq_logger.error(f"Groq Client 파라미터 검사 중 예외 발생: {e}")
    groq_logger.debug(traceback.format_exc())

# Groq 클라이언트 초기화
try:
    # 버전 호환성 문제 해결을 위한 방어적 코드
    try:
        groq_logger.info("Groq Client 초기화 시도 - 표준 방식")
        # 소스 코드 검사
        if hasattr(groq.Client, '__init__') and callable(groq.Client.__init__):
            source_code = inspect.getsource(groq.Client.__init__)
            groq_logger.debug(f"Groq.Client.__init__ 소스코드 일부: {source_code[:200]}...")
        
        # 최신 버전 호환 방식으로 초기화 시도
        client = groq.Client(api_key=api_key)
        groq_logger.info("Groq 클라이언트 초기화 성공 (표준 방식)")
    except TypeError as type_error:
        groq_logger.error(f"TypeError 발생: {type_error}")
        error_msg = str(type_error)
        
        if "unexpected keyword argument 'proxies'" in error_msg:
            # proxies 인자 문제 확인
            groq_logger.warning(f"Groq 모듈 버전 호환성 문제 감지: {error_msg}")
            
            # 스택 트레이스에서 문제 발생 지점 확인
            tb = traceback.extract_tb(sys.exc_info()[2])
            groq_logger.debug(f"오류 발생 스택 트레이스: {tb}")
            
            # 모듈 내부에서 proxies 사용 여부 검사
            groq_logger.info("groq 모듈 내부 코드 검사")
            base_modules = ['_client', '_base_client']
            for module_name in base_modules:
                try:
                    module = getattr(groq, module_name, None)
                    if module:
                        groq_logger.info(f"{module_name} 모듈 확인됨")
                        classes = [name for name, obj in inspect.getmembers(module, inspect.isclass)]
                        groq_logger.info(f"{module_name} 클래스 목록: {classes}")
                except Exception as e:
                    groq_logger.error(f"{module_name} 검사 중 오류: {e}")
            
            # 대체 방식 시도 (proxies 제외)
            from typing import Dict, Any
            
            # 클라이언트 생성자의 인자 목록 확인
            sig = inspect.signature(groq.Client.__init__)
            valid_params = {
                name: param 
                for name, param in sig.parameters.items() 
                if name not in ['self', 'proxies']
            }
            
            # 유효한 파라미터만 전달
            client_kwargs: Dict[str, Any] = {"api_key": api_key}
            filtered_kwargs = {k: v for k, v in client_kwargs.items() if k in valid_params}
            
            groq_logger.info(f"필터링된 인자로 초기화 시도: {filtered_kwargs}")
            
            # 필터링된 인자로 초기화 재시도
            client = groq.Client(**filtered_kwargs)
            groq_logger.info("Groq 클라이언트 초기화 성공 (대체 방식)")
        else:
            # 다른 TypeError인 경우 다시 발생
            groq_logger.error(f"알 수 없는 TypeError: {error_msg}")
            raise
    groq_logger.info("Groq 서비스가 성공적으로 초기화되었습니다.")

except Exception as e:
    groq_logger.error(f"Groq 클라이언트 초기화 실패: {str(e)}")
    # 로그에 자세한 에러 정보 기록
    groq_logger.debug(f"상세 오류: {traceback.format_exc()}")
    groq_logger.warning("이 오류로 인해 AI 기능이 제한됩니다.")
    # 클라이언트 객체 None으로 설정 - 이 경우 함수들은 fallback 응답 반환
    client = None

def log_function_call(func_name, inputs, outputs=None, additional_info=None):
    """함수 호출 정보를 로깅하는 유틸리티 함수"""
    # 개발 환경에서만 상세 로깅
    if not settings.DEBUG:
        return
        
    log_entry = {
        "function": func_name,
        "timestamp": datetime.now().isoformat(),
        "inputs": inputs,
    }
    
    if outputs:
        log_entry["outputs"] = outputs
        
    if additional_info:
        log_entry["additional_info"] = additional_info
    
    # 안전한 직렬화를 위해 기본 처리
    try:    
        groq_logger.debug(json.dumps(log_entry, ensure_ascii=False, default=str))
    except TypeError as e:
        # 직렬화 불가능한 객체가 있는 경우 str()로 변환
        groq_logger.error(f"로깅 중 직렬화 오류: {e}")
        # 입력을 안전하게 문자열로 변환
        safe_log_entry = {
            "function": str(func_name),
            "timestamp": str(datetime.now().isoformat()),
            "inputs": str(inputs),
        }
        if outputs:
            safe_log_entry["outputs"] = str(outputs)
        if additional_info:
            safe_log_entry["additional_info"] = str(additional_info)
        groq_logger.debug(json.dumps(safe_log_entry, ensure_ascii=False))

def analyze_job_description(job_description):
    """
    1단계-1: 채용공고 분석
    """
    func_name = "analyze_job_description"
    groq_logger.info(f"===== {func_name} 함수 시작 =====")
    groq_logger.debug(f"입력 파라미터: job_description 길이 = {len(job_description)}")
    
    # 입력 로깅
    inputs = {"job_description_length": len(job_description), "job_description_preview": job_description[:100] + "..."}
    log_function_call(func_name, inputs)
    
    prompt = f"""
    다음 채용공고를 분석해주세요:
    
    채용공고:
    {job_description}
    
    다음 사항을 분석해주세요:
    1. 주요 업무 내용
    2. 필수 자격 요건
    3. 우대 사항
    4. 직무 특성
    """
    
    groq_logger.debug(f"생성된 프롬프트 길이: {len(prompt)}")
    
    try:
        groq_logger.info(f"Groq API 호출 시작 - 모델: qwen-qwq-32b")
        response = client.chat.completions.create(
            model="qwen-qwq-32b",
            messages=[
                {"role": "system", "content": "당신은 채용공고 분석 전문가입니다. 주어진 채용공고의 주요 내용을 분석해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1500
        )
        
        groq_logger.debug(f"Groq API 응답 수신 - 토큰 수: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
        
        if response and hasattr(response, 'choices') and len(response.choices) > 0:
            job_analysis = response.choices[0].message.content
            
            # 출력 및 처리 과정 로깅
            additional_info = {
                "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else None,
                "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else None,
                "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else None
            }
            outputs = {"job_analysis_length": len(job_analysis), "job_analysis_preview": job_analysis[:100] + "..."}
            log_function_call(func_name, inputs, outputs, additional_info)
            
            logger.info(f"채용공고 분석 API 호출 성공 - 사용 토큰: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
            groq_logger.info(f"===== {func_name} 함수 종료 =====")
            return job_analysis
        else:
            error_msg = f"채용공고 분석 API 응답 형식 오류: {response}"
            logger.error(error_msg)
            groq_logger.error(error_msg)
            
            # 오류 로깅
            outputs = {"error": error_msg}
            log_function_call(func_name, inputs, outputs)
            
            groq_logger.info(f"===== {func_name} 함수 종료 (오류) =====")
            return "채용공고 분석 중 오류가 발생했습니다."
            
    except Exception as e:
        error_msg = f"채용공고 분석 API 호출 오류: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 스택 트레이스 포함하여 오류 로깅
        outputs = {"error": str(e), "traceback": traceback.format_exc()}
        log_function_call(func_name, inputs, outputs)
        
        groq_logger.error(error_msg)
        groq_logger.debug(traceback.format_exc())
        groq_logger.info(f"===== {func_name} 함수 종료 (예외) =====")
        return "채용공고 분석 중 오류가 발생했습니다."

def analyze_company_info(company_info):
    """
    1단계-2: 회사 정보 분석
    """
    func_name = "analyze_company_info"
    groq_logger.info(f"===== {func_name} 함수 시작 =====")
    groq_logger.debug(f"입력 파라미터: company_info 길이 = {len(company_info)}")
    
    # 입력 로깅
    inputs = {"company_info_length": len(company_info), "company_info_preview": company_info[:100] + "..."}
    log_function_call(func_name, inputs)
    
    logger.info(f"[DEBUG] analyze_company_info 시작 - 입력 길이: {len(company_info)}")
    prompt = f"""
    다음 회사 정보를 분석해주세요:
    
    회사 정보:
    {company_info}
    
    다음 사항을 분석해주세요:
    1. 회사의 주요 사업 영역
    2. 회사 문화와 가치관
    3. 회사의 성장성과 미래 전망
    """
    
    groq_logger.debug(f"생성된 프롬프트 길이: {len(prompt)}")
    
    try:
        groq_logger.info(f"Groq API 호출 시작 - 모델: qwen-qwq-32b")
        response = client.chat.completions.create(
            model="qwen-qwq-32b",
            messages=[
                {"role": "system", "content": "당신은 회사 분석 전문가입니다. 주어진 회사 정보의 주요 내용을 분석해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1500
        )
        
        groq_logger.debug(f"Groq API 응답 수신 - 토큰 수: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
        
        if response and hasattr(response, 'choices') and len(response.choices) > 0:
            company_analysis = response.choices[0].message.content
            
            # 출력 및 처리 과정 로깅
            additional_info = {
                "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else None,
                "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else None,
                "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else None
            }
            outputs = {"company_analysis_length": len(company_analysis), "company_analysis_preview": company_analysis[:100] + "..."}
            log_function_call(func_name, inputs, outputs, additional_info)
            
            logger.info(f"회사 정보 분석 API 호출 성공 - 사용 토큰: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
            groq_logger.info(f"===== {func_name} 함수 종료 =====")
            return company_analysis
        else:
            error_msg = f"회사 정보 분석 API 응답 형식 오류: {response}"
            logger.error(error_msg)
            groq_logger.error(error_msg)
            
            # 오류 로깅
            outputs = {"error": error_msg}
            log_function_call(func_name, inputs, outputs)
            
            groq_logger.info(f"===== {func_name} 함수 종료 (오류) =====")
            return "회사 정보 분석 중 오류가 발생했습니다."
            
    except Exception as e:
        error_msg = f"회사 정보 분석 API 호출 오류: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 스택 트레이스 포함하여 오류 로깅
        outputs = {"error": str(e), "traceback": traceback.format_exc()}
        log_function_call(func_name, inputs, outputs)
        
        groq_logger.error(error_msg)
        groq_logger.debug(traceback.format_exc())
        groq_logger.info(f"===== {func_name} 함수 종료 (예외) =====")
        return "회사 정보 분석 중 오류가 발생했습니다."

def analyze_job_and_company(job_description, company_info):
    """
    1단계: 채용공고와 회사 정보 분석
    """
    func_name = "analyze_job_and_company"
    groq_logger.info(f"===== {func_name} 함수 시작 =====")
    
    # 입력 로깅
    inputs = {
        "job_description_length": len(job_description),
        "company_info_length": len(company_info),
        "job_description_preview": job_description[:100] + "...",
        "company_info_preview": company_info[:100] + "..."
    }
    log_function_call(func_name, inputs)
    
    try:
        # 1단계-1: 채용공고 분석
        groq_logger.debug("1단계-1: 채용공고 분석 시작")
        logger.debug("1단계-1: 채용공고 분석 시작")
        job_analysis = analyze_job_description(job_description)
        logger.debug(f"채용공고 분석: {job_analysis[:100]}...")
        groq_logger.debug(f"채용공고 분석 결과 길이: {len(job_analysis)}")
        
        # 1단계-2: 회사 정보 분석
        groq_logger.debug("1단계-2: 회사 정보 분석 시작")
        logger.debug("1단계-2: 회사 정보 분석 시작")
        company_analysis = analyze_company_info(company_info)
        logger.debug(f"회사 정보 분석: {company_analysis[:100]}...")
        groq_logger.debug(f"회사 정보 분석 결과 길이: {len(company_analysis)}")
        
        # 분석 결과 통합
        analysis = f"""
        [채용공고 분석]
        {job_analysis}
        
        [회사 정보 분석]
        {company_analysis}
        """
        
        # 출력 및 처리 과정 로깅
        outputs = {
            "analysis_length": len(analysis),
            "analysis_preview": analysis[:100] + "..."
        }
        log_function_call(func_name, inputs, outputs)
        
        groq_logger.info(f"===== {func_name} 함수 종료 =====")
        return analysis
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"채용공고/회사 분석 중 오류 발생: {error_msg}", exc_info=True)
        
        # 오류 로깅
        outputs = {"error": error_msg, "traceback": traceback.format_exc()}
        log_function_call(func_name, inputs, outputs)
        
        groq_logger.error(f"채용공고/회사 분석 중 오류 발생: {error_msg}")
        groq_logger.debug(traceback.format_exc())
        groq_logger.info(f"===== {func_name} 함수 종료 (예외) =====")
        return "채용공고/회사 분석 중 오류가 발생했습니다."

def extract_job_keypoints(job_description):
    """
    채용공고에서 핵심 내용만 추출
    """
    func_name = "extract_job_keypoints"
    groq_logger.info(f"===== {func_name} 함수 시작 =====")
    
    # 안전한 입력 준비
    if job_description is None:
        job_description = ""
        
    # 문자열 확인 및 변환
    if not isinstance(job_description, str):
        logger.warning(f"job_description이 문자열이 아닙니다: {type(job_description)}")
        job_description = str(job_description)
    
    # 입력 로깅 - 안전한 슬라이싱
    job_desc_preview = job_description[:100] + "..." if len(job_description) > 100 else job_description
    inputs = {"job_description_length": len(job_description), "job_description_preview": job_desc_preview}
    log_function_call(func_name, inputs)
    
    try:
        logger.debug(f"=== extract_job_keypoints 시작 ===")
        logger.debug(f"입력 job_description 길이: {len(job_description)}")
        groq_logger.debug(f"입력 job_description 길이: {len(job_description)}")
        
        prompt = f"""다음 채용공고에서 핵심 내용만 추출해주세요:

채용공고:
{job_description}

다음 형식으로 추출해주세요:
1. 주요 업무 (3-4줄)
2. 필수 자격요건 (3-4줄)
3. 우대사항 (2-3줄)"""

        logger.debug(f"프롬프트 길이: {len(prompt)}")
        groq_logger.debug(f"생성된 프롬프트 길이: {len(prompt)}")
        
        groq_logger.info(f"Groq API 호출 시작 - 모델: qwen-qwq-32b")
        response = client.chat.completions.create(
            model="qwen-qwq-32b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        groq_logger.debug(f"Groq API 응답 수신 - 토큰 수: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
        
        logger.debug(f"응답 토큰 수: {response.usage.completion_tokens}")
        logger.debug(f"=== extract_job_keypoints 완료 ===")
        
        result = response.choices[0].message.content
        
        # 출력 및 처리 과정 로깅
        additional_info = {
            "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else None,
            "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else None,
            "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else None
        }
        outputs = {"result_length": len(result), "result_preview": result[:100] + "..."}
        log_function_call(func_name, inputs, outputs, additional_info)
        
        groq_logger.info(f"===== {func_name} 함수 종료 =====")
        return result
    except Exception as e:
        error_msg = f"extract_job_keypoints 오류: {str(e)}"
        logger.error(error_msg)
        
        # 오류 로깅
        outputs = {"error": str(e), "traceback": traceback.format_exc()}
        log_function_call(func_name, inputs, outputs)
        
        groq_logger.error(error_msg)
        groq_logger.debug(traceback.format_exc())
        groq_logger.info(f"===== {func_name} 함수 종료 (예외) =====")
        raise

def create_resume_draft(job_keypoints, company_info, user_story):
    """
    2단계: 자기소개서 초안 작성
    """
    func_name = "create_resume_draft"
    groq_logger.info(f"===== {func_name} 함수 시작 =====")
    
    # 입력 타입 검증 및 변환
    if not isinstance(job_keypoints, str):
        job_keypoints = str(job_keypoints)
    
    if not isinstance(company_info, str):
        company_info = str(company_info)
        
    # user_story 처리 개선
    user_story_dict = {}
    if isinstance(user_story, dict):
        user_story_dict = user_story
    elif isinstance(user_story, str):
        logger.warning(f"user_story가 문자열입니다: {type(user_story)}")
        # 문자열을 분석하여 기본 정보 추출 시도
        user_story_dict = {
            '성격의 장단점': user_story,
            '지원 동기': user_story,
            '입사 후 포부': user_story
        }
    else:
        logger.warning(f"user_story가 예상치 못한 타입입니다: {type(user_story)}")
        user_story_dict = {
            '성격의 장단점': str(user_story),
            '지원 동기': str(user_story),
            '입사 후 포부': str(user_story)
        }
    
    # 안전한 슬라이싱을 위한 프리뷰 생성
    job_preview = job_keypoints[:100] + "..." if len(job_keypoints) > 100 else job_keypoints
    company_preview = company_info[:100] + "..." if len(company_info) > 100 else company_info
    
    # 입력 로깅
    inputs = {
        "job_keypoints_length": len(job_keypoints),
        "company_info_length": len(company_info),
        "user_story_keys": list(user_story_dict.keys()),
        "job_keypoints_preview": job_preview,
        "company_info_preview": company_preview
    }
    log_function_call(func_name, inputs)
    
    # 성장과정과 학교생활 제거
    filtered_story = {
        '성격의 장단점': user_story_dict.get('성격의 장단점', ''),
        '지원 동기': user_story_dict.get('지원 동기', ''),
        '입사 후 포부': user_story_dict.get('입사 후 포부', '')
    }
    
    groq_logger.debug(f"필터링된 user_story 키: {list(filtered_story.keys())}")
    
    prompt = f"""
    다음 정보를 바탕으로 자기소개서를 작성해주세요:
    
    [채용공고 핵심 내용]
    {job_keypoints}
    
    [회사 정보]
    {company_info}
    
    [지원자 정보]
    성격의 장단점: {filtered_story['성격의 장단점']}
    지원 동기: {filtered_story['지원 동기']}
    입사 후 포부: {filtered_story['입사 후 포부']}
    
    다음 사항을 포함하여 작성해주세요:
    1. 지원자의 핵심 경쟁력과 지원 동기
    2. 회사와 직무에 대한 이해도
    3. 입사 후 기여 방안
    """
    
    groq_logger.debug(f"생성된 프롬프트 길이: {len(prompt)}")
    
    try:
        groq_logger.info(f"Groq API 호출 시작 - 모델: qwen-qwq-32b")
        response = client.chat.completions.create(
            model="qwen-qwq-32b",
            messages=[
                {"role": "system", "content": "당신은 자기소개서 작성 전문가입니다. 주어진 정보를 바탕으로 설득력 있는 자기소개서를 작성해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        groq_logger.debug(f"Groq API 응답 수신 - 토큰 수: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
        
        if response and hasattr(response, 'choices') and len(response.choices) > 0:
            draft = response.choices[0].message.content
            
            # 출력 및 처리 과정 로깅
            additional_info = {
                "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else None,
                "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else None,
                "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else None
            }
            outputs = {"draft_length": len(draft), "draft_preview": draft[:100] + "..."}
            log_function_call(func_name, inputs, outputs, additional_info)
            
            logger.info(f"자기소개서 초안 작성 API 호출 성공 - 사용 토큰: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
            groq_logger.info(f"===== {func_name} 함수 종료 =====")
            return draft
        else:
            error_msg = f"자기소개서 초안 작성 API 응답 형식 오류: {response}"
            logger.error(error_msg)
            
            # 오류 로깅
            outputs = {"error": error_msg}
            log_function_call(func_name, inputs, outputs)
            
            groq_logger.error(error_msg)
            groq_logger.info(f"===== {func_name} 함수 종료 (오류) =====")
            return "자기소개서 초안 작성 중 오류가 발생했습니다."
            
    except Exception as e:
        error_msg = f"자기소개서 초안 작성 API 호출 오류: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 오류 로깅
        outputs = {"error": str(e), "traceback": traceback.format_exc()}
        log_function_call(func_name, inputs, outputs)
        
        groq_logger.error(error_msg)
        groq_logger.debug(traceback.format_exc())
        groq_logger.info(f"===== {func_name} 함수 종료 (예외) =====")
        return "자기소개서 초안 작성 중 오류가 발생했습니다."

def finalize_resume_metrics(resume_draft):
    """
    3단계-1: 성과와 역량을 구체적 수치로 표현
    """
    func_name = "finalize_resume_metrics"
    groq_logger.info(f"===== {func_name} 함수 시작 =====")
    
    # 입력 로깅
    inputs = {"resume_draft_length": len(resume_draft), "resume_draft_preview": resume_draft[:100] + "..."}
    log_function_call(func_name, inputs)
    
    prompt = f"""
    다음 자기소개서 초안의 성과와 역량을 구체적 수치로 표현해주세요:
    
    초안: {resume_draft}
    
    다음 사항을 개선해주세요:
    1. 모든 성과와 역량은 구체적 수치로 표현 (예: "생산성 30% 향상", "만족도 4.8/5 달성")
    2. 입사 시 예상 기여도를 수치로 제시 (예: "비용 40% 절감", "매출 15% 성장 기여")
    """
    
    groq_logger.debug(f"생성된 프롬프트 길이: {len(prompt)}")
    
    try:
        groq_logger.info(f"Groq API 호출 시작 - 모델: qwen-qwq-32b")
        response = client.chat.completions.create(
            model="qwen-qwq-32b",
            messages=[
                {"role": "system", "content": "당신은 자기소개서 편집 전문가입니다. 주어진 초안의 성과와 역량을 구체적 수치로 표현해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        
        groq_logger.debug(f"Groq API 응답 수신 - 토큰 수: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
        
        if response and hasattr(response, 'choices') and len(response.choices) > 0:
            metrics = response.choices[0].message.content
            
            # 출력 및 처리 과정 로깅
            additional_info = {
                "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else None,
                "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else None,
                "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else None
            }
            outputs = {"metrics_length": len(metrics), "metrics_preview": metrics[:100] + "..."}
            log_function_call(func_name, inputs, outputs, additional_info)
            
            logger.info(f"자기소개서 수치화 API 호출 성공 - 사용 토큰: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
            groq_logger.info(f"===== {func_name} 함수 종료 =====")
            return metrics
        else:
            error_msg = f"수치화 API 응답 형식 오류: {response}"
            logger.error(error_msg)
            
            # 오류 로깅
            outputs = {"error": error_msg}
            log_function_call(func_name, inputs, outputs)
            
            groq_logger.error(error_msg)
            groq_logger.info(f"===== {func_name} 함수 종료 (오류) =====")
            return "자기소개서 수치화 중 오류가 발생했습니다."
            
    except Exception as e:
        error_msg = f"수치화 API 호출 오류: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 오류 로깅
        outputs = {"error": str(e), "traceback": traceback.format_exc()}
        log_function_call(func_name, inputs, outputs)
        
        groq_logger.error(error_msg)
        groq_logger.debug(traceback.format_exc())
        groq_logger.info(f"===== {func_name} 함수 종료 (예외) =====")
        return "자기소개서 수치화 중 오류가 발생했습니다."

def finalize_resume_style(resume_draft):
    """
    3단계-2: 전문성과 열정을 강조하는 문체로 수정
    """
    func_name = "finalize_resume_style"
    groq_logger.info(f"===== {func_name} 함수 시작 =====")
    
    # 입력 로깅
    inputs = {"resume_draft_length": len(resume_draft), "resume_draft_preview": resume_draft[:100] + "..."}
    log_function_call(func_name, inputs)
    
    prompt = f"""
    다음 자기소개서 초안을 전문성과 열정을 강조하는 문체로 수정해주세요:
    
    초안: {resume_draft}
    
    다음 사항을 개선해주세요:
    1. 전문 용어와 업계 용어를 자연스럽게 사용
    2. 열정과 자신감을 표현하는 어조 사용
    3. 간결하고 명확한 문장으로 수정
    """
    
    groq_logger.debug(f"생성된 프롬프트 길이: {len(prompt)}")
    
    try:
        groq_logger.info(f"Groq API 호출 시작 - 모델: qwen-qwq-32b")
        response = client.chat.completions.create(
            model="qwen-qwq-32b",
            messages=[
                {"role": "system", "content": "당신은 자기소개서 편집 전문가입니다. 주어진 초안을 전문성과 열정을 강조하는 문체로 수정해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        
        groq_logger.debug(f"Groq API 응답 수신 - 토큰 수: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
        
        if response and hasattr(response, 'choices') and len(response.choices) > 0:
            styled = response.choices[0].message.content
            
            # 출력 및 처리 과정 로깅
            additional_info = {
                "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else None,
                "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else None,
                "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else None
            }
            outputs = {"styled_length": len(styled), "styled_preview": styled[:100] + "..."}
            log_function_call(func_name, inputs, outputs, additional_info)
            
            logger.info(f"자기소개서 문체 수정 API 호출 성공 - 사용 토큰: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
            groq_logger.info(f"===== {func_name} 함수 종료 =====")
            return styled
        else:
            error_msg = f"문체 수정 API 응답 형식 오류: {response}"
            logger.error(error_msg)
            
            # 오류 로깅
            outputs = {"error": error_msg}
            log_function_call(func_name, inputs, outputs)
            
            groq_logger.error(error_msg)
            groq_logger.info(f"===== {func_name} 함수 종료 (오류) =====")
            return "자기소개서 문체 수정 중 오류가 발생했습니다."
            
    except Exception as e:
        error_msg = f"문체 수정 API 호출 오류: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 오류 로깅
        outputs = {"error": str(e), "traceback": traceback.format_exc()}
        log_function_call(func_name, inputs, outputs)
        
        groq_logger.error(error_msg)
        groq_logger.debug(traceback.format_exc())
        groq_logger.info(f"===== {func_name} 함수 종료 (예외) =====")
        return "자기소개서 문체 수정 중 오류가 발생했습니다."

def finalize_resume_emphasis(resume_draft):
    """
    3단계-3: 직무 관련 핵심 키워드 강조 및 맞춤화
    """
    func_name = "finalize_resume_emphasis"
    groq_logger.info(f"===== {func_name} 함수 시작 =====")
    
    # 입력 로깅
    inputs = {"resume_draft_length": len(resume_draft), "resume_draft_preview": resume_draft[:100] + "..."}
    log_function_call(func_name, inputs)
    
    prompt = f"""
    다음 자기소개서 초안에서 직무 관련 핵심 키워드를 강조하고 맞춤화해주세요:
    
    초안: {resume_draft}
    
    다음 사항을 개선해주세요:
    1. 직무 관련 핵심 키워드 3-5개 강조 (굵은 글씨로 표시하지 말고, 문맥 속에 자연스럽게 강조)
    2. 회사 문화와 가치관과 일치하는 내용으로 맞춤화
    3. 지원 포지션에 꼭 필요한 역량 중심으로 재구성
    """
    
    groq_logger.debug(f"생성된 프롬프트 길이: {len(prompt)}")
    
    try:
        groq_logger.info(f"Groq API 호출 시작 - 모델: qwen-qwq-32b")
        response = client.chat.completions.create(
            model="qwen-qwq-32b",
            messages=[
                {"role": "system", "content": "당신은 자기소개서 편집 전문가입니다. 주어진 초안에서 직무 관련 핵심 키워드를 강조하고 맞춤화해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        
        groq_logger.debug(f"Groq API 응답 수신 - 토큰 수: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
        
        if response and hasattr(response, 'choices') and len(response.choices) > 0:
            emphasized = response.choices[0].message.content
            
            # 출력 및 처리 과정 로깅
            additional_info = {
                "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else None,
                "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else None,
                "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else None
            }
            outputs = {"emphasized_length": len(emphasized), "emphasized_preview": emphasized[:100] + "..."}
            log_function_call(func_name, inputs, outputs, additional_info)
            
            logger.info(f"자기소개서 키워드 강조 API 호출 성공 - 사용 토큰: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
            groq_logger.info(f"===== {func_name} 함수 종료 =====")
            return emphasized
        else:
            error_msg = f"키워드 강조 API 응답 형식 오류: {response}"
            logger.error(error_msg)
            
            # 오류 로깅
            outputs = {"error": error_msg}
            log_function_call(func_name, inputs, outputs)
            
            groq_logger.error(error_msg)
            groq_logger.info(f"===== {func_name} 함수 종료 (오류) =====")
            return "자기소개서 키워드 강조 중 오류가 발생했습니다."
            
    except Exception as e:
        error_msg = f"키워드 강조 API 호출 오류: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 오류 로깅
        outputs = {"error": str(e), "traceback": traceback.format_exc()}
        log_function_call(func_name, inputs, outputs)
        
        groq_logger.error(error_msg)
        groq_logger.debug(traceback.format_exc())
        groq_logger.info(f"===== {func_name} 함수 종료 (예외) =====")
        return "자기소개서 키워드 강조 중 오류가 발생했습니다."

def finalize_resume(resume_draft):
    """
    3단계: 자기소개서 최종 완성
    """
    func_name = "finalize_resume"
    groq_logger.info(f"===== {func_name} 함수 시작 =====")
    
    # 입력 타입 검증
    if not isinstance(resume_draft, str):
        logger.warning(f"resume_draft가 문자열이 아닙니다: {type(resume_draft)}")
        resume_draft = str(resume_draft)
    
    # 안전한 프리뷰 생성
    draft_preview = resume_draft[:100] + "..." if len(resume_draft) > 100 else resume_draft
    
    # 입력 로깅
    inputs = {"resume_draft_length": len(resume_draft), "resume_draft_preview": draft_preview}
    log_function_call(func_name, inputs)
    
    try:
        groq_logger.debug("3단계-1: 성과와 역량을 구체적 수치로 표현 시작")
        # 3단계-1: 성과와 역량을 구체적 수치로 표현
        metrics = finalize_resume_metrics(resume_draft)
        groq_logger.debug(f"수치화 결과 길이: {len(metrics)}")
        
        groq_logger.debug("3단계-2: 전문성과 열정을 강조하는 문체로 수정 시작")
        # 3단계-2: 전문성과 열정을 강조하는 문체로 수정
        styled = finalize_resume_style(metrics)
        groq_logger.debug(f"문체 수정 결과 길이: {len(styled)}")
        
        groq_logger.debug("3단계-3: 직무 관련 핵심 키워드 강조 및 맞춤화 시작")
        # 3단계-3: 직무 관련 핵심 키워드 강조 및 맞춤화
        finalized = finalize_resume_emphasis(styled)
        groq_logger.debug(f"키워드 강조 결과 길이: {len(finalized)}")
        
        # 출력 및 처리 과정 로깅
        outputs = {
            "finalized_length": len(finalized),
            "finalized_preview": finalized[:100] + "..."
        }
        log_function_call(func_name, inputs, outputs)
        
        groq_logger.info(f"===== {func_name} 함수 종료 =====")
        return finalized
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"자기소개서 최종 완성 중 오류 발생: {error_msg}", exc_info=True)
        
        # 오류 로깅
        outputs = {"error": error_msg, "traceback": traceback.format_exc()}
        log_function_call(func_name, inputs, outputs)
        
        groq_logger.error(f"자기소개서 최종 완성 중 오류 발생: {error_msg}")
        groq_logger.debug(traceback.format_exc())
        groq_logger.info(f"===== {func_name} 함수 종료 (예외) =====")
        return "자기소개서 최종 완성 중 오류가 발생했습니다."

def generate_resume(job_description, user_story, company_info):
    """
    자기소개서 생성 - 전체 과정
    """
    func_name = "generate_resume"
    groq_logger.info(f"===== {func_name} 함수 시작 =====")
    
    # 입력 타입 검증
    if not isinstance(job_description, str):
        logger.warning(f"job_description이 문자열이 아닙니다: {type(job_description)}")
        job_description = str(job_description)
        
    if not isinstance(company_info, str):
        logger.warning(f"company_info가 문자열이 아닙니다: {type(company_info)}")
        company_info = str(company_info)
    
    # user_story 처리 개선
    user_story_dict = {}
    if isinstance(user_story, dict):
        user_story_dict = user_story
    elif isinstance(user_story, str):
        logger.warning(f"user_story가 문자열입니다: {type(user_story)}")
        # 문자열을 분석하여 기본 정보 추출 시도
        user_story_dict = {
            '성격의 장단점': user_story,
            '지원 동기': user_story,
            '입사 후 포부': user_story
        }
    else:
        logger.warning(f"user_story가 예상치 못한 타입입니다: {type(user_story)}")
        user_story_dict = {
            '성격의 장단점': str(user_story),
            '지원 동기': str(user_story),
            '입사 후 포부': str(user_story)
        }
    
    # 안전한 프리뷰 생성
    job_preview = job_description[:100] + "..." if len(job_description) > 100 else job_description
    company_preview = company_info[:100] + "..." if len(company_info) > 100 else company_info
    
    # 입력 로깅
    inputs = {
        "job_description_length": len(job_description),
        "company_info_length": len(company_info),
        "user_story_keys": list(user_story_dict.keys()),
        "job_description_preview": job_preview,
        "company_info_preview": company_preview
    }
    log_function_call(func_name, inputs)
    
    try:
        # 1단계: 분석
        groq_logger.info("1단계: 채용공고에서 핵심 내용 추출 시작")
        job_keypoints = extract_job_keypoints(job_description)
        groq_logger.debug(f"채용공고 핵심 내용 길이: {len(job_keypoints)}")
        
        # 2단계: 자기소개서 초안 작성
        groq_logger.info("2단계: 자기소개서 초안 작성 시작")
        resume_draft = create_resume_draft(job_keypoints, company_info, user_story_dict)
        groq_logger.debug(f"자기소개서 초안 길이: {len(resume_draft)}")
        
        # 3단계: 자기소개서 최종 완성
        groq_logger.info("3단계: 자기소개서 최종 완성 시작")
        finalized_resume = finalize_resume(resume_draft)
        groq_logger.debug(f"최종 자기소개서 길이: {len(finalized_resume)}")
        
        # 출력 및 처리 과정 로깅
        outputs = {
            "finalized_resume_length": len(finalized_resume),
            "finalized_resume_preview": finalized_resume[:100] + "..."
        }
        log_function_call(func_name, inputs, outputs)
        
        groq_logger.info(f"===== {func_name} 함수 종료 =====")
        return finalized_resume
    
    except Exception as e:
        error_msg = f"자기소개서 생성 중 오류: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 오류 로깅
        outputs = {"error": error_msg, "traceback": traceback.format_exc()}
        log_function_call(func_name, inputs, outputs)
        
        groq_logger.error(error_msg)
        groq_logger.debug(traceback.format_exc())
        groq_logger.info(f"===== {func_name} 함수 종료 (예외) =====")
        return "자기소개서 생성 중 오류가 발생했습니다."
