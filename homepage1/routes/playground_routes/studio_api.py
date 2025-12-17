"""
AI 블로그 스튜디오 보안 프록시 API
- 무료 놀이터: 토큰 차감 로직 절대 금지
- 보안: API 키는 서버 환경변수에서만 관리
- Rate Limit: 유저당 하루 20회 제한 (메모리 기반)
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Blueprint 생성
studio_api_bp = Blueprint(
    'studio_api',
    __name__,
    url_prefix='/api/studio'
)

# Rate Limit 관리 (메모리 기반)
# 구조: {user_id: {'count': int, 'reset_at': datetime}}
_rate_limit_store: Dict[int, Dict[str, Any]] = {}
RATE_LIMIT_PER_DAY = 20


def _check_rate_limit(user_id: int) -> tuple[bool, Optional[str]]:
    """
    Rate Limit 체크
    Returns: (is_allowed, error_message)
    """
    now = datetime.now()
    
    # 기존 기록이 있는지 확인
    if user_id in _rate_limit_store:
        user_limit = _rate_limit_store[user_id]
        
        # 리셋 시간이 지났으면 초기화
        if now >= user_limit['reset_at']:
            _rate_limit_store[user_id] = {
                'count': 0,
                'reset_at': now + timedelta(days=1)
            }
            return True, None
        
        # 제한 초과 확인
        if user_limit['count'] >= RATE_LIMIT_PER_DAY:
            reset_time = user_limit['reset_at'].strftime('%Y-%m-%d %H:%M:%S')
            return False, f"하루 사용량 제한({RATE_LIMIT_PER_DAY}회)에 도달했습니다. 다음 리셋 시간: {reset_time}"
        
        # 카운트 증가
        user_limit['count'] += 1
    else:
        # 첫 사용자: 초기화
        _rate_limit_store[user_id] = {
            'count': 1,
            'reset_at': now + timedelta(days=1)
        }
    
    return True, None


def _get_api_key() -> str:
    """서버 환경변수에서 API 키 가져오기"""
    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("서버 환경변수에 GOOGLE_API_KEY 또는 GEMINI_API_KEY가 설정되지 않았습니다.")
    return api_key


@studio_api_bp.route('/generate', methods=['POST'])
def generate():
    """
    블로그 포스트 생성 API (보안 프록시)
    
    Request Body:
    {
        "action": "generate" | "regenerate" | "generateImage" | "generateTopics" | "suggestInteractiveElement",
        "params": {...}  # action에 따른 파라미터
    }
    
    Returns:
    {
        "success": bool,
        "data": {...} | null,
        "error": str | null
    }
    """
    try:
        # 1. 로그인 체크
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': '로그인이 필요합니다.'
            }), 401
        
        # 2. Rate Limit 체크
        is_allowed, error_msg = _check_rate_limit(user_id)
        if not is_allowed:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 429
        
        # 3. 요청 데이터 파싱
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '요청 데이터가 없습니다.'
            }), 400
        
        action = data.get('action')
        params = data.get('params', {})
        
        if not action:
            return jsonify({
                'success': False,
                'error': 'action 파라미터가 필요합니다.'
            }), 400
        
        # 4. API 키 가져오기
        api_key = _get_api_key()
        
        # 5. Google Generative AI 호출
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
        except ImportError:
            logger.error("google.generativeai 라이브러리가 설치되지 않았습니다. pip install google-generativeai 필요")
            return jsonify({
                'success': False,
                'error': '서버 설정 오류: AI 라이브러리가 설치되지 않았습니다.'
            }), 500
        
        # 6. Action에 따른 처리
        if action == 'generate':
            result = _handle_generate(genai, params)
        elif action == 'regenerate':
            result = _handle_regenerate(genai, params)
        elif action == 'generateImage':
            result = _handle_generate_image(genai, params)
        elif action == 'generateTopics':
            result = _handle_generate_topics(genai, params)
        elif action == 'suggestInteractiveElement':
            result = _handle_suggest_interactive_element(genai, params)
        else:
            return jsonify({
                'success': False,
                'error': f'지원하지 않는 action: {action}'
            }), 400
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except ValueError as e:
        logger.error(f"API 키 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"블로그 생성 중 오류 발생: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'블로그 생성 중 오류가 발생했습니다: {str(e)}'
        }), 500


def _convert_typescript_schema_to_python(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    TypeScript Type 스키마를 Python 딕셔너리로 변환
    프론트엔드에서 이미 JSON으로 직렬화되어 전달됨
    """
    if not isinstance(schema, dict):
        return schema
    
    converted = {}
    
    # type 변환 (이미 문자열로 변환되어 옴)
    if 'type' in schema:
        ts_type = schema['type']
        if isinstance(ts_type, str):
            # 이미 문자열로 변환됨 ('object', 'string', 'array' 등)
            converted['type'] = ts_type
        else:
            # 혹시 모를 경우를 대비
            converted['type'] = str(ts_type)
    
    # properties 재귀 변환
    if 'properties' in schema:
        converted['properties'] = {
            k: _convert_typescript_schema_to_python(v)
            for k, v in schema['properties'].items()
        }
    
    # items 재귀 변환 (배열의 경우)
    if 'items' in schema:
        converted['items'] = _convert_typescript_schema_to_python(schema['items'])
    
    # 기타 필드 복사
    for key in ['description', 'required']:
        if key in schema:
            converted[key] = schema[key]
    
    return converted


def _handle_generate(genai, params: Dict[str, Any]) -> Dict[str, Any]:
    """블로그 포스트 생성 처리"""
    prompt = params.get('prompt')
    response_schema_raw = params.get('responseSchema')
    
    if not prompt:
        raise ValueError("prompt 파라미터가 필요합니다.")
    
    # TypeScript 스키마를 Python 딕셔너리로 변환
    response_schema = _convert_typescript_schema_to_python(response_schema_raw) if response_schema_raw else None
    
    # GenerationConfig 딕셔너리 생성 (google.generativeai는 딕셔너리도 받음)
    generation_config_dict = {
        "response_mime_type": "application/json"
    }
    if response_schema:
        generation_config_dict["response_schema"] = response_schema
    
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=generation_config_dict
    )
    
    response = model.generate_content(prompt)
    json_string = response.text
    parsed_json = json.loads(json_string)
    
    return parsed_json


def _handle_regenerate(genai, params: Dict[str, Any]) -> Dict[str, Any]:
    """블로그 포스트 재생성 처리"""
    prompt = params.get('prompt')
    response_schema_raw = params.get('responseSchema')
    
    if not prompt:
        raise ValueError("prompt 파라미터가 필요합니다.")
    
    # TypeScript 스키마를 Python 딕셔너리로 변환
    response_schema = _convert_typescript_schema_to_python(response_schema_raw) if response_schema_raw else None
    
    # GenerationConfig 딕셔너리 생성
    generation_config_dict = {
        "response_mime_type": "application/json"
    }
    if response_schema:
        generation_config_dict["response_schema"] = response_schema
    
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=generation_config_dict
    )
    
    response = model.generate_content(prompt)
    json_string = response.text
    parsed_json = json.loads(json_string)
    
    return parsed_json


def _handle_generate_image(genai, params: Dict[str, Any]) -> Dict[str, Any]:
    """이미지 생성 처리"""
    prompt = params.get('prompt')
    aspect_ratio = params.get('aspectRatio', '16:9')
    
    if not prompt:
        raise ValueError("prompt 파라미터가 필요합니다.")
    
    # Imagen API 사용 (Google Generative AI의 이미지 생성)
    # 참고: 실제 구현은 Google의 Imagen API 문서를 참조해야 함
    # 여기서는 예시로 구조만 제공
    try:
        # 실제 구현 시 Google의 이미지 생성 API 호출
        # 현재는 구조만 제공
        raise NotImplementedError("이미지 생성 기능은 추후 구현 예정입니다.")
    except Exception as e:
        logger.error(f"이미지 생성 오류: {str(e)}")
        raise


def _handle_generate_topics(genai, params: Dict[str, Any]) -> Dict[str, Any]:
    """주제 생성 처리"""
    prompt = params.get('prompt')
    use_search = params.get('useSearch', False)
    response_schema_raw = params.get('responseSchema')
    
    if not prompt:
        raise ValueError("prompt 파라미터가 필요합니다.")
    
    config_dict = {}
    if use_search:
        # Google Search 도구 사용
        import google.generativeai as genai_module
        config_dict['tools'] = [genai_module.protos.Tool(google_search={})]
    else:
        config_dict['response_mime_type'] = "application/json"
        if response_schema_raw:
            response_schema = _convert_typescript_schema_to_python(response_schema_raw)
            config_dict['response_schema'] = response_schema
    
    config_dict['temperature'] = 1.0
    
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=config_dict
    )
    
    import hashlib
    random_seed = int(hashlib.md5(prompt.encode()).hexdigest(), 16) % 10000
    enhanced_prompt = f"{prompt}\n\n(This is a new request. Please generate a completely new and different set of suggestions. Random seed: {random_seed})"
    response = model.generate_content(enhanced_prompt)
    
    if use_search:
        # 검색 결과는 JSON이 아닐 수 있음
        text = response.text
        lines = text.split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        # 서두 문장 제거
        if lines and (lines[0].endswith('입니다.') or lines[0].endswith('입니다:')):
            lines.pop(0)
        import re
        topics = [re.sub(r'^(\d+\.|-|\*)\s*', '', line).strip() for line in lines if line.strip()]
        return {'topics': topics}
    else:
        json_string = response.text
        parsed_json = json.loads(json_string)
        return parsed_json


def _handle_suggest_interactive_element(genai, params: Dict[str, Any]) -> Dict[str, Any]:
    """인터랙티브 요소 제안 처리"""
    topic = params.get('topic')
    
    if not topic:
        raise ValueError("topic 파라미터가 필요합니다.")
    
    prompt = f'''
        You are a creative web developer and UI/UX designer.
        For the blog post topic "{topic}", suggest a single, simple, and engaging interactive element idea that can be implemented using only HTML, CSS, and vanilla JavaScript.
        The idea should be concise and described in a single sentence in Korean.
        For example: "간단한 투자 수익률을 계산해주는 계산기" or "나에게 맞는 커피 원두를 추천해주는 퀴즈".
        Just return the idea itself, without any introductory phrases.
    '''
    
    generation_config = {
        "temperature": 0.8
    }
    
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=generation_config
    )
    
    response = model.generate_content(prompt)
    return {'suggestion': response.text.strip()}

