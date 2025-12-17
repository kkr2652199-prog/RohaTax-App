"""
AI 블로그 스튜디오 보안 프록시 API
- 무료 놀이터: 토큰 차감 로직 절대 금지
- 보안: API 키는 서버 환경변수에서만 관리
- Rate Limit: 유저당 하루 20회 제한 (메모리 기반)
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, request, session

logger = logging.getLogger(__name__)

# Blueprint 생성
studio_api_bp = Blueprint("studio_api", __name__, url_prefix="/api/studio")

# Rate Limit 관리 (메모리 기반)
# 구조: {user_id: {'count': int, 'reset_at': datetime}}
_rate_limit_store: Dict[int, Dict[str, Any]] = {}
RATE_LIMIT_PER_DAY = 20

# 추가 요금 폭탄 방지용 사용량 추적 (IP / 사용자 ID 기반)
# 구조: { 'user_or_ip': { 'date': 'YYYY-MM-DD', 'count': int, 'last_request': datetime | None } }
USAGE_TRACKER: Dict[str, Dict[str, Any]] = {}


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
        if now >= user_limit["reset_at"]:
            _rate_limit_store[user_id] = {
                "count": 0,
                "reset_at": now + timedelta(days=1),
            }
            return True, None

        # 제한 초과 확인
        if user_limit["count"] >= RATE_LIMIT_PER_DAY:
            reset_time = user_limit["reset_at"].strftime("%Y-%m-%d %H:%M:%S")
            return (
                False,
                f"하루 사용량 제한({RATE_LIMIT_PER_DAY}회)에 도달했습니다. 다음 리셋 시간: {reset_time}",
            )

        # 카운트 증가
        user_limit["count"] += 1
    else:
        # 첫 사용자: 초기화
        _rate_limit_store[user_id] = {"count": 1, "reset_at": now + timedelta(days=1)}

    return True, None


def _get_api_key() -> str:
    """서버 환경변수에서 API 키 가져오기"""
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "서버 환경변수에 GOOGLE_API_KEY 또는 GEMINI_API_KEY가 설정되지 않았습니다."
        )
    # 디버깅용: 앞 5자리와 길이만 출력 (전체 키는 절대 로그에 남기지 않음)
    try:
        print(f"🔑 [Debug] Loaded API Key: {api_key[:5]}... (Length: {len(api_key)})")
    except Exception:
        # print 실패 시에도 서비스 로직에는 영향 주지 않음
        logger.debug("API Key debug print failed", exc_info=True)
    return api_key


@studio_api_bp.route("/generate", methods=["POST"])
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
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"success": False, "error": "로그인이 필요합니다."}), 401

        # 2. 추가 안전장치: IP / 사용자 ID 기반 사용량 제한 (1일 5회, 30초 쿨타임)
        now = datetime.now()
        today_str = now.date().isoformat()

        # 사용자 식별자: 로그인 시 user_id, 비로그인/예외 시 IP 기반
        identifier: str
        try:
            identifier = f"user_{int(user_id)}"
        except Exception:
            client_ip = request.remote_addr or "unknown"
            identifier = f"ip_{client_ip}"

        user_usage = USAGE_TRACKER.get(identifier)

        # 날짜가 바뀌었으면 카운트 리셋
        if not user_usage or user_usage.get("date") != today_str:
            user_usage = {
                "date": today_str,
                "count": 0,
                "last_request": None,
            }
            USAGE_TRACKER[identifier] = user_usage

        # 속도 제한: 마지막 요청 후 30초 이내면 차단 (날씨 요청은 제외)
        if not is_weather_request:
            last_request: Optional[datetime] = user_usage.get("last_request")
            if last_request is not None:
                elapsed = (now - last_request).total_seconds()
                if elapsed < 30:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": "잠시 후 다시 시도해주세요. (요청 간 최소 30초 간격이 필요합니다)",
                            }
                        ),
                        429,
                    )

        # 일일 5회 제한 (날씨 요청은 제외)
        # 날씨 요청이 아닌 경우에만 제한 적용
        if not is_weather_request and user_usage.get("count", 0) >= 5:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "일일 무료 사용량(5회)을 초과했습니다. 내일 다시 이용해주세요.",
                    }
                ),
                429,
            )

        # 3. 기존 Rate Limit 체크 (유저당 20회 / day, 메모리 기반)
        is_allowed, error_msg = _check_rate_limit(user_id)
        if not is_allowed:
            return jsonify({"success": False, "error": error_msg}), 429

        # 4. 요청 데이터 파싱 (먼저 파싱하여 날씨 요청 여부 확인)
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "요청 데이터가 없습니다."}), 400

        action = data.get("action")
        params = data.get("params", {})
        
        # 날씨 요청 여부 확인 (Rate Limit 적용 전에)
        is_weather_request = (
            action == "fetchWeather" or 
            (action == "generate" and params.get("config", {}).get("tools") and 
             any("googleSearch" in str(tool) for tool in params.get("config", {}).get("tools", [])) and 
             "날씨" in params.get("prompt", ""))
        )

        if not action:
            return (
                jsonify({"success": False, "error": "action 파라미터가 필요합니다."}),
                400,
            )

        # 5. API 키 가져오기
        api_key = _get_api_key()

        # 6. Google Generative AI 호출
        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
        except ImportError:
            logger.error(
                "google.generativeai 라이브러리가 설치되지 않았습니다. pip install google-generativeai 필요"
            )
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "서버 설정 오류: AI 라이브러리가 설치되지 않았습니다.",
                    }
                ),
                500,
            )

        # 7. Action에 따른 처리
        if action == "generate":
            # 날씨 요청인지 블로그 생성 요청인지 구분
            prompt = params.get("prompt", "")
            config = params.get("config", {})
            # 날씨 요청: tools에 googleSearch가 있고, prompt에 "날씨"가 포함된 경우
            if config.get("tools") and any("googleSearch" in str(tool) for tool in config.get("tools", [])) and "날씨" in prompt:
                result = _handle_fetch_weather(genai, params)
            else:
                result = _handle_generate(genai, params)
        elif action == "regenerate":
            result = _handle_regenerate(genai, params)
        elif action == "generateImage":
            result = _handle_generate_image(genai, params)
        elif action == "generateTopics":
            result = _handle_generate_topics(genai, params)
        elif action == "suggestInteractiveElement":
            result = _handle_suggest_interactive_element(genai, params)
        elif action == "fetchWeather":
            # 날씨 전용 action 추가
            result = _handle_fetch_weather(genai, params)
        else:
            return (
                jsonify({"success": False, "error": f"지원하지 않는 action: {action}"}),
                400,
            )

        # 사용량 카운트 증가 및 마지막 요청 시간 갱신 (날씨 요청은 제외)
        if not is_weather_request:
            user_usage["count"] = user_usage.get("count", 0) + 1
            user_usage["last_request"] = now

        return jsonify({"success": True, "data": result})

    except ValueError as e:
        logger.error(f"API 키 오류: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception as e:
        logger.error(f"블로그 생성 중 오류 발생: {str(e)}", exc_info=True)
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"블로그 생성 중 오류가 발생했습니다: {str(e)}",
                }
            ),
            500,
        )


def _convert_typescript_schema_to_python(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    TypeScript Type 스키마를 Python 딕셔너리로 변환
    프론트엔드에서 이미 JSON으로 직렬화되어 전달됨
    """
    if not isinstance(schema, dict):
        return schema

    converted = {}

    # type 변환 (이미 문자열로 변환되어 옴)
    if "type" in schema:
        ts_type = schema["type"]
        if isinstance(ts_type, str):
            # 이미 문자열로 변환됨 ('object', 'string', 'array' 등)
            converted["type"] = ts_type
        else:
            # 혹시 모를 경우를 대비
            converted["type"] = str(ts_type)

    # properties 재귀 변환
    if "properties" in schema:
        converted["properties"] = {
            k: _convert_typescript_schema_to_python(v)
            for k, v in schema["properties"].items()
        }

    # items 재귀 변환 (배열의 경우)
    if "items" in schema:
        converted["items"] = _convert_typescript_schema_to_python(schema["items"])

    # 기타 필드 복사
    for key in ["description", "required"]:
        if key in schema:
            converted[key] = schema[key]

    return converted


def _handle_generate(genai, params: Dict[str, Any]) -> Dict[str, Any]:
    """블로그 포스트 생성 처리"""
    prompt = params.get("prompt")
    response_schema_raw = params.get("responseSchema")

    if not prompt:
        raise ValueError("prompt 파라미터가 필요합니다.")

    # TypeScript 스키마를 Python 딕셔너리로 변환
    response_schema = (
        _convert_typescript_schema_to_python(response_schema_raw)
        if response_schema_raw
        else None
    )

    # GenerationConfig 딕셔너리 생성 (google.generativeai는 딕셔너리도 받음)
    generation_config_dict = {"response_mime_type": "application/json"}
    if response_schema:
        generation_config_dict["response_schema"] = response_schema

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash", generation_config=generation_config_dict
    )

    response = model.generate_content(prompt)
    json_string = response.text
    parsed_json = json.loads(json_string)

    return parsed_json


def _handle_regenerate(genai, params: Dict[str, Any]) -> Dict[str, Any]:
    """블로그 포스트 재생성 처리"""
    prompt = params.get("prompt")
    response_schema_raw = params.get("responseSchema")

    if not prompt:
        raise ValueError("prompt 파라미터가 필요합니다.")

    # TypeScript 스키마를 Python 딕셔너리로 변환
    response_schema = (
        _convert_typescript_schema_to_python(response_schema_raw)
        if response_schema_raw
        else None
    )

    # GenerationConfig 딕셔너리 생성
    generation_config_dict = {"response_mime_type": "application/json"}
    if response_schema:
        generation_config_dict["response_schema"] = response_schema

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash", generation_config=generation_config_dict
    )

    response = model.generate_content(prompt)
    json_string = response.text
    parsed_json = json.loads(json_string)

    return parsed_json


def _handle_generate_image(genai, params: Dict[str, Any]) -> Dict[str, Any]:
    """이미지 생성 처리"""
    prompt = params.get("prompt")
    aspect_ratio = params.get("aspectRatio", "16:9")

    if not prompt:
        raise ValueError("prompt 파라미터가 필요합니다.")

    # ⚠️ 중요: Google Gemini API는 이미지 생성을 지원하지 않습니다.
    # 이미지 생성은 Google Imagen API (별도 서비스) 또는 다른 이미지 생성 서비스를 사용해야 합니다.
    # 
    # 현재 구현 상태:
    # - Google Gemini API는 텍스트 생성에만 특화되어 있음
    # - 이미지 생성은 별도의 API 키와 서비스가 필요함
    # 
    # 해결 방안:
    # 1. Google Imagen API 통합 (유료 서비스)
    # 2. 다른 이미지 생성 서비스 통합 (DALL-E, Stable Diffusion 등)
    # 3. 프론트엔드에서 직접 이미지 생성 API 호출
    
    logger.warning(
        f"이미지 생성 요청 수신: prompt='{prompt[:50]}...', aspectRatio={aspect_ratio}. "
        "하지만 Google Gemini API는 이미지 생성을 지원하지 않습니다. "
        "Google Imagen API 또는 다른 이미지 생성 서비스 통합이 필요합니다."
    )
    
    # 사용자에게 명확한 에러 메시지 반환
    raise NotImplementedError(
        "이미지 생성 기능은 현재 지원되지 않습니다. "
        "Google Gemini API는 텍스트 생성에만 특화되어 있으며, "
        "이미지 생성은 Google Imagen API 또는 다른 이미지 생성 서비스가 필요합니다. "
        "이 기능은 추후 구현 예정입니다."
    )


def _handle_generate_topics(genai, params: Dict[str, Any]) -> Dict[str, Any]:
    """주제 생성 처리"""
    prompt = params.get("prompt")
    use_search = params.get("useSearch", False)
    response_schema_raw = params.get("responseSchema")

    if not prompt:
        raise ValueError("prompt 파라미터가 필요합니다.")

    config_dict = {}
    if use_search:
        # Google Search 도구 사용
        import google.generativeai as genai_module

        config_dict["tools"] = [genai_module.protos.Tool(google_search={})]
    else:
        config_dict["response_mime_type"] = "application/json"
        if response_schema_raw:
            response_schema = _convert_typescript_schema_to_python(response_schema_raw)
            config_dict["response_schema"] = response_schema

    config_dict["temperature"] = 1.0

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash", generation_config=config_dict
    )

    import hashlib

    random_seed = int(hashlib.md5(prompt.encode()).hexdigest(), 16) % 10000
    enhanced_prompt = f"{prompt}\n\n(This is a new request. Please generate a completely new and different set of suggestions. Random seed: {random_seed})"
    response = model.generate_content(enhanced_prompt)

    if use_search:
        # 검색 결과는 JSON이 아닐 수 있음
        # ✅ 에러 방지: response.text가 None이거나 빈 문자열일 수 있음
        if not response.text:
            raise ValueError("AI 응답이 비어있습니다. 다시 시도해주세요.")
        
        text = response.text
        lines = text.split("\n")
        lines = [line.strip() for line in lines if line.strip()]
        # 서두 문장 제거
        if lines and (lines[0].endswith("입니다.") or lines[0].endswith("입니다:")):
            lines.pop(0)
        import re

        topics = [
            re.sub(r"^(\d+\.|-|\*)\s*", "", line).strip()
            for line in lines
            if line.strip()
        ]
        
        # ✅ 최소 1개 이상의 주제가 있어야 함
        if not topics:
            raise ValueError("주제 추천 결과가 비어있습니다. 다시 시도해주세요.")
        
        return {"topics": topics}
    else:
        # ✅ 에러 방지: response.text가 None이거나 빈 문자열일 수 있음
        if not response.text:
            raise ValueError("AI 응답이 비어있습니다. 다시 시도해주세요.")
        
        json_string = response.text
        try:
            parsed_json = json.loads(json_string)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {json_string[:200]}...")
            raise ValueError(f"AI 응답 파싱 오류: {str(e)}")
        
        return parsed_json


def _handle_fetch_weather(genai, params: Dict[str, Any]) -> Dict[str, Any]:
    """날씨 정보 조회 처리 (Rate Limit 제외)"""
    prompt = params.get("prompt")
    config = params.get("config", {})
    
    if not prompt:
        raise ValueError("prompt 파라미터가 필요합니다.")
    
    # Google Search 도구 사용
    import google.generativeai as genai_module
    
    generation_config_dict = {
        "tools": [genai_module.protos.Tool(google_search={})]
    }
    
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=generation_config_dict
    )
    
    response = model.generate_content(prompt)
    
    # ✅ 에러 방지: response.text가 None이거나 빈 문자열일 수 있음
    if not response.text:
        raise ValueError("AI 응답이 비어있습니다. 다시 시도해주세요.")
    
    # JSON 추출 (프론트엔드의 extractJsonFromText 로직과 유사)
    text = response.text
    import re
    
    # JSON 코드 블록 찾기
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        json_string = json_match.group(1)
    else:
        # 코드 블록 없이 JSON만 있는 경우
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            json_string = json_match.group(0)
        else:
            raise ValueError("AI 응답에서 JSON을 찾을 수 없습니다.")
    
    try:
        parsed_json = json.loads(json_string)
        return {"text": json.dumps(parsed_json, ensure_ascii=False)}
    except json.JSONDecodeError as e:
        logger.error(f"날씨 JSON 파싱 오류: {json_string[:200]}...")
        raise ValueError(f"날씨 정보 파싱 오류: {str(e)}")


def _handle_suggest_interactive_element(
    genai, params: Dict[str, Any]
) -> Dict[str, Any]:
    """인터랙티브 요소 제안 처리"""
    topic = params.get("topic")

    if not topic:
        raise ValueError("topic 파라미터가 필요합니다.")

    prompt = f"""
        You are a creative web developer and UI/UX designer.
        For the blog post topic "{topic}", suggest a single, simple, and engaging interactive element idea that can be implemented using only HTML, CSS, and vanilla JavaScript.
        The idea should be concise and described in a single sentence in Korean.
        For example: "간단한 투자 수익률을 계산해주는 계산기" or "나에게 맞는 커피 원두를 추천해주는 퀴즈".
        Just return the idea itself, without any introductory phrases.
    """

    generation_config = {"temperature": 0.8}

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash", generation_config=generation_config
    )

    response = model.generate_content(prompt)
    return {"suggestion": response.text.strip()}
