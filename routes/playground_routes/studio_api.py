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


def _get_api_key(user_id: int) -> str:
    """
    사용자별 API 키 가져오기 (BYOK 모델)
    1. 사용자 데이터베이스에서 google_api_key 조회
    2. 없으면 서버 환경변수에서 fallback
    """
    import sqlite3
    from core.db import get_conn
    
    # user_id 유효성 검사
    if not user_id:
        logger.warning("_get_api_key: user_id가 None이거나 0입니다.")
        # user_id가 없어도 환경변수에서 가져올 수 있으므로 계속 진행
    
    # 1. 사용자별 API 키 조회 (BYOK 모델)
    if user_id:
        try:
            logger.info(f"[_get_api_key] 사용자 API 키 조회 시작 (user_id={user_id})")
            with get_conn() as conn:
                # sqlite3.Row 사용 (더 안정적)
                conn.row_factory = sqlite3.Row
                user = conn.execute(
                    "SELECT google_api_key FROM users WHERE id = ? AND COALESCE(is_deleted, 0) = 0",
                    (user_id,)
                ).fetchone()
                
                if user:
                    api_key = user['google_api_key'] if user['google_api_key'] else None
                    if api_key:
                        api_key = api_key.strip()
                        # API 키 유효성 검사 (AIzaSy로 시작하거나 최소 20자 이상)
                        if api_key and (api_key.startswith('AIzaSy') or len(api_key) >= 20):
                            logger.info(f"[_get_api_key] 사용자 API 키 발견 (user_id={user_id}, 길이={len(api_key)})")
                            return api_key
                        else:
                            logger.warning(f"[_get_api_key] 사용자 API 키 형식이 올바르지 않음 (user_id={user_id}, 길이={len(api_key) if api_key else 0})")
                    else:
                        logger.info(f"[_get_api_key] 사용자 API 키가 NULL (user_id={user_id})")
                else:
                    logger.warning(f"[_get_api_key] 사용자를 찾을 수 없음 (user_id={user_id})")
        except Exception as e:
            logger.error(f"[_get_api_key] 사용자 API 키 조회 중 예외 발생 (user_id={user_id}): {e}", exc_info=True)
    
    # 2. Fallback: 서버 환경변수에서 가져오기
    logger.info("[_get_api_key] 서버 환경변수에서 API 키 조회 시도")
    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        error_msg = "API 키가 설정되지 않았습니다. 마이페이지에서 Google API Key를 등록하거나, 서버 관리자에게 문의하세요."
        logger.error(f"[_get_api_key] {error_msg} (user_id={user_id})")
        raise ValueError(error_msg)
    
    logger.info(f"[_get_api_key] 서버 환경변수에서 API 키 사용 (길이={len(api_key)})")
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
        
        # 4. API 키 가져오기 (사용자별 키 우선)
        api_key = _get_api_key(user_id)
        
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
        elif action == 'proxyAI':
            result = _handle_proxy_ai(genai, params)
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
        error_msg = str(e)
        logger.error(f"[generate] API 키 오류 (user_id={user_id}): {error_msg}")
        return jsonify({
            'success': False,
            'error': error_msg,
            'error_code': 'API_KEY_NOT_FOUND',
            'user_id': user_id
        }), 400
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[generate] 블로그 생성 중 오류 발생 (user_id={user_id}): {error_msg}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'블로그 생성 중 오류가 발생했습니다: {error_msg}',
            'user_id': user_id
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
    
    # GenerationConfig 딕셔너리 생성
    generation_config_dict = {
        "response_mime_type": "application/json"
    }
    if response_schema:
        generation_config_dict["response_schema"] = response_schema
    
    # 모델 시도 순서 (최신 모델부터)
    models_to_try = ["gemini-2.0-flash-exp", "gemini-1.5-flash"]
    last_error = None
    
    for model_name in models_to_try:
        try:
            logger.info(f"📝 [_handle_generate] 모델 시도 중: {model_name}")
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config_dict
            )
            response = model.generate_content(prompt)
            json_string = response.text
            parsed_json = json.loads(json_string)
            return parsed_json
        except Exception as e:
            last_error = str(e)
            logger.warning(f"⚠️ [_handle_generate] {model_name} 실패: {last_error}")
            continue
            
    raise ValueError(f"모든 AI 모델 호출 실패. 마지막 에러: {last_error}")


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
    
    models_to_try = ["gemini-2.0-flash-exp", "gemini-1.5-flash"]
    last_error = None
    
    for model_name in models_to_try:
        try:
            logger.info(f"🔄 [_handle_regenerate] 모델 시도 중: {model_name}")
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config_dict
            )
            response = model.generate_content(prompt)
            json_string = response.text
            parsed_json = json.loads(json_string)
            return parsed_json
        except Exception as e:
            last_error = str(e)
            logger.warning(f"⚠️ [_handle_regenerate] {model_name} 실패: {last_error}")
            continue
            
    raise ValueError(f"모든 AI 모델 호출 실패. 마지막 에러: {last_error}")


def _handle_generate_image(genai, params: Dict[str, Any]) -> Dict[str, Any]:
    """이미지 생성 처리 (Imagen 모델 사용)"""
    prompt = params.get('prompt')
    aspect_ratio = params.get('aspectRatio', '16:9')
    
    if not prompt:
        raise ValueError("prompt 파라미터가 필요합니다.")
    
    try:
        logger.info(f"📸 [_handle_generate_image] 이미지 생성 시작: prompt='{prompt[:50]}...', ratio={aspect_ratio}")
        
        # Imagen 모델 인스턴스 생성
        # 참고: 모델명은 버전에 따라 다를 수 있음 (imagen-3.0-generate-001, imagen-3.0-fast-generate-001 등)
        model = genai.GenerativeModel('imagen-3.0-generate-001')
        
        # 이미지 생성 호출
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio=aspect_ratio,
            output_mime_type='image/jpeg'
        )
        
        if response.generated_images:
            image_bytes = response.generated_images[0].image.image_bytes
            import base64
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            
            logger.info("✅ [_handle_generate_image] 이미지 생성 성공")
            return {
                'imageBytes': f"data:image/jpeg;base64,{image_b64}"
            }
        else:
            logger.error("[_handle_generate_image] 생성된 이미지가 없습니다.")
            raise ValueError("이미지를 생성할 수 없습니다. (응답이 비어있음)")
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ [_handle_generate_image] 이미지 생성 중 오류 발생: {error_msg}")
        
        # 모델을 찾을 수 없는 경우 등 특정 에러에 대한 폴백이나 상세 안내
        if "not found" in error_msg.lower():
            raise ValueError("이미지 생성 모델을 찾을 수 없습니다. 서버 설정을 확인해주세요.")
        
        raise ValueError(f"이미지 생성 실패: {error_msg}")


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
    
    models_to_try = ["gemini-2.0-flash-exp", "gemini-1.5-flash"]
    last_error = None
    
    import hashlib
    random_seed = int(hashlib.md5(prompt.encode()).hexdigest(), 16) % 10000
    enhanced_prompt = f"{prompt}\n\n(This is a new request. Please generate a completely new and different set of suggestions. Random seed: {random_seed})"

    for model_name in models_to_try:
        try:
            logger.info(f"💡 [_handle_generate_topics] 모델 시도 중: {model_name}")
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=config_dict
            )
            response = model.generate_content(enhanced_prompt)
            
            if use_search:
                text = response.text
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                if lines and (lines[0].endswith('입니다.') or lines[0].endswith('입니다:')):
                    lines.pop(0)
                import re
                topics = [re.sub(r'^(\d+\.|-|\*)\s*', '', line).strip() for line in lines if line.strip()]
                return {'topics': topics}
            else:
                return json.loads(response.text)
        except Exception as e:
            last_error = str(e)
            logger.warning(f"⚠️ [_handle_generate_topics] {model_name} 실패: {last_error}")
            continue
            
    raise ValueError(f"주제 생성 실패. 마지막 에러: {last_error}")


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
    
    config_dict = {
        "temperature": 0.8
    }
    
    models_to_try = ["gemini-2.0-flash-exp", "gemini-1.5-flash"]
    last_error = None
    
    for model_name in models_to_try:
        try:
            logger.info(f"💡 [_handle_suggest_interactive_element] 모델 시도 중: {model_name}")
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=config_dict
            )
            response = model.generate_content(prompt)
            return {'suggestion': response.text.strip()}
        except Exception as e:
            last_error = str(e)
            logger.warning(f"⚠️ [_handle_suggest_interactive_element] {model_name} 실패: {last_error}")
            continue
            
    raise ValueError(f"요소 제안 실패. 마지막 에러: {last_error}")


def _handle_proxy_ai(genai, params: Dict[str, Any]) -> Dict[str, Any]:
    """범용 AI 프록시 처리 (keywordService 등에서 사용)"""
    prompt = params.get('prompt')
    model_name = params.get('model', 'gemini-1.5-flash')
    config_raw = params.get('config', {})
    
    if not prompt:
        raise ValueError("prompt 파라미터가 필요합니다.")
    
    # 설정 변환
    config = {}
    if config_raw.get('tools'):
        import google.generativeai as genai_module
        config['tools'] = [genai_module.protos.Tool(google_search={})]
        
    if config_raw.get('responseMimeType'):
        config['response_mime_type'] = config_raw['responseMimeType']
        
    if config_raw.get('responseSchema'):
        config['response_schema'] = _convert_typescript_schema_to_python(config_raw['responseSchema'])
        
    if config_raw.get('temperature'):
        config['temperature'] = config_raw['temperature']

    # 모델 시도 순서
    models_to_try = [model_name, "gemini-2.0-flash-exp", "gemini-1.5-flash"]
    last_error = None
    
    for m in models_to_try:
        try:
            logger.info(f"🌐 [_handle_proxy_ai] 모델 시도 중: {m}")
            model = genai.GenerativeModel(
                model_name=m,
                generation_config=config if not config_raw.get('tools') else None,
                tools=config.get('tools')
            )
            # generation_config는 generate_content의 인자로도 전달 가능
            response = model.generate_content(prompt, generation_config=config if not config_raw.get('tools') else config)
            return {'text': response.text}
        except Exception as e:
            last_error = str(e)
            logger.warning(f"⚠️ [_handle_proxy_ai] {m} 실패: {last_error}")
            continue
            
    raise ValueError(f"AI 호출 실패. 마지막 에러: {last_error}")

