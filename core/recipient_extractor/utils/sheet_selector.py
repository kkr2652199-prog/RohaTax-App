"""
시트 선택 로직 모듈

main_extractor.py의 시트 선택 관련 로직을 독립 모듈로 분리
"""

import pandas as pd
from typing import Dict, List, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)


def select_optimal_sheet_by_family_rule(parsed_data: Dict[str, Any], logger_instance: logging.Logger = None) -> Optional[Dict[str, Any]]:
    """
    🎯 지능앱 시트 우선순위 선택 로직 (단순화)
    
    가족 규칙에 따라 최적의 시트를 선택:
    1. 각 시트에서 독립된 단일 셀 값으로 가족(아빠값, 엄마값) 구성
    2. 전체 시트 중 최대 아빠값을 가진 시트를 1순위로 선택
    3. 아빠값이 동일한 경우 시트 순서(작은 번호) 우선
    
    Args:
        parsed_data: 파싱된 데이터 (모든 시트 정보 포함)
        logger_instance: 로거 인스턴스 (선택사항)
            
    Returns:
        선택된 시트 정보 또는 None
    """
    log = logger_instance or logger
    
    try:
        # 모든 시트 정보 가져오기
        all_sheets = parsed_data.get('all_sheets', {})
        if not all_sheets:
            log.warning("시트 우선순위 선택: 모든 시트 정보가 없습니다")
            return None
        
        log.info(f"🎯 시트 우선순위 선택 시작: {len(all_sheets)}개 시트 검토")
        
        sheet_candidates = []
        
        # 각 시트별로 가족 검증 및 아빠값 추출
        for sheet_name, sheet_info in all_sheets.items():
            try:
                log.info(f"🔍 시트 '{sheet_name}' 검토 중...")
                
                # 시트에서 가족 정보 추출 (단순화된 로직)
                family_info = extract_family_from_sheet_simple(sheet_info, log)
                
                if family_info and family_info.get('dad_value', 0) > 0:
                    sheet_candidates.append({
                        'sheet_name': sheet_name,
                        'dad_value': family_info['dad_value'],
                        'mom_value': family_info.get('mom_value', 0),
                        'family_info': family_info
                    })
                    
                    log.info(f"✅ 시트 '{sheet_name}' 가족 발견: 아빠값={family_info['dad_value']:,.0f}원, 엄마값={family_info.get('mom_value', 0):,.0f}원")
                else:
                    log.info(f"❌ 시트 '{sheet_name}' 가족 없음")
                    
            except Exception as e:
                log.warning(f"시트 '{sheet_name}' 검토 중 오류: {str(e)}")
                continue
        
        if not sheet_candidates:
            log.warning("🎯 시트 우선순위 선택: 가족을 찾은 시트가 없습니다")
            return None
        
        # 최대 아빠값을 가진 시트 선택 (결정적 정렬)
        sheet_candidates.sort(key=lambda x: (x['dad_value'], x.get('sheet_name', '')), reverse=True)
        best_sheet = sheet_candidates[0]
        
        log.info(f"🎯 최적 시트 선택: '{best_sheet['sheet_name']}' (아빠값: {best_sheet['dad_value']:,.0f}원, 엄마값: {best_sheet['mom_value']:,.0f}원)")
        
        # DataFrame 생성하여 반환
        try:
            # 선택된 시트의 데이터로 DataFrame 생성
            selected_sheet_name = best_sheet['sheet_name']
            sheet_info = all_sheets[selected_sheet_name]
            
            # 헤더와 데이터 추출
            headers = sheet_info.get('headers', [])
            data = sheet_info.get('data', [])
            
            # DataFrame 체크: data가 DataFrame인 경우 처리
            if isinstance(data, pd.DataFrame):
                data = data.values.tolist()
            
            if headers and len(headers) > 0 and (isinstance(data, list) and len(data) > 0):
                # 첫 번째 행을 헤더로 사용
                header_row = headers[0] if headers else []
                # DataFrame 생성
                df = pd.DataFrame(data, columns=header_row)
                
                # 반환 딕셔너리에 dataframe 추가
                best_sheet['dataframe'] = df
                log.info(f"🎯 DataFrame 생성 완료: '{selected_sheet_name}' ({len(df)}행, {len(df.columns)}열)")
            else:
                log.warning(f"시트 '{selected_sheet_name}' 데이터가 없어 DataFrame 생성 실패")
                return None
                
        except Exception as e:
            log.error(f"DataFrame 생성 오류: {str(e)}")
            return None
        
        return best_sheet
        
    except Exception as e:
        log.error(f"시트 우선순위 선택 오류: {str(e)}")
        return None


def extract_family_from_sheet_simple(sheet_info: Dict[str, Any], logger_instance: logging.Logger = None) -> Optional[Dict[str, Any]]:
    """
    시트에서 가족 정보 추출 (단순화된 로직)
    
    Args:
        sheet_info: 시트 정보 (file_parser에서 수집한 데이터)
        logger_instance: 로거 인스턴스 (선택사항)
            
    Returns:
        가족 정보 또는 None
    """
    log = logger_instance or logger
    
    try:
        # 시트 데이터에서 헤더와 데이터 추출
        headers = sheet_info.get('headers', [])
        data = sheet_info.get('data', [])
        
        # DataFrame 체크: data가 DataFrame인 경우 처리
        if isinstance(data, pd.DataFrame):
            data = data.values.tolist()
        
        if not headers or (isinstance(data, list) and len(data) == 0):
            return None
        
        # 첫 번째 행을 헤더로 사용
        header_row = headers[0] if headers else []
        
        # 아빠값(공급가액)과 엄마값(부가세) 컬럼 찾기
        dad_col = None
        mom_col = None
        
        for i, header in enumerate(header_row):
            header_lower = str(header).lower().strip()
            
            # 아빠값 컬럼 찾기 (공급가액 관련)
            if any(keyword in header_lower for keyword in ['공급가액', '총금액', '합계', '배달요금', '총배달']):
                if '부가세' not in header_lower:  # 부가세가 포함된 컬럼은 제외
                    dad_col = i
                    log.debug(f"아빠값 컬럼 발견: {header} (컬럼 {i})")
            
            # 엄마값 컬럼 찾기 (부가세 관련)
            elif any(keyword in header_lower for keyword in ['부가세', '세액', 'vat']):
                if '합계' not in header_lower:  # 합계는 제외
                    mom_col = i
                    log.debug(f"엄마값 컬럼 발견: {header} (컬럼 {i})")
        
        if dad_col is None or mom_col is None:
            log.debug(f"가족 구성 실패: 아빠값 컬럼={dad_col}, 엄마값 컬럼={mom_col}")
            return None
        
        # 각 행에서 최대 아빠값 찾기
        max_dad_value = 0
        max_mom_value = 0
        
        for row_data in data:
            if len(row_data) > max(dad_col, mom_col):
                try:
                    dad_value = extract_numeric_value(row_data[dad_col])
                    mom_value = extract_numeric_value(row_data[mom_col])
                    
                    # 가족 검증: 둘 다 양수여야 함
                    if dad_value > 0 and mom_value > 0:
                        if dad_value > max_dad_value:
                            max_dad_value = dad_value
                            max_mom_value = mom_value
                            
                            # 10% 관계 검증
                            ratio = mom_value / dad_value if dad_value > 0 else 0
                            if 0.095 <= ratio <= 0.105:  # 9.5% ~ 10.5% 범위
                                log.debug(f"완벽한 가족 발견: 아빠={dad_value}, 엄마={mom_value}, 비율={ratio:.3f}")
                            
                except Exception as e:
                    log.debug(f"행 처리 오류: {e}")
                    continue
        
        if max_dad_value > 0:
            return {
                'dad_value': max_dad_value,
                'mom_value': max_mom_value,
                'dad_col': dad_col,
                'mom_col': mom_col
            }
        
        return None
        
    except Exception as e:
        log.error(f"가족 정보 추출 오류: {e}")
        return None


def extract_numeric_value(cell_value) -> float:
    """셀 값에서 숫자 추출"""
    try:
        if pd.isna(cell_value):
            return 0.0
        
        # 문자열인 경우 숫자만 추출
        if isinstance(cell_value, str):
            # 천단위 구분자 제거
            cleaned = cell_value.replace(',', '').replace('원', '').replace('￦', '').replace('₩', '')
            # 괄호로 둘러싸인 음수 처리
            if cleaned.startswith('(') and cleaned.endswith(')'):
                cleaned = '-' + cleaned[1:-1]
            # 숫자만 추출
            numbers = re.findall(r'-?\d+\.?\d*', cleaned)
            if numbers:
                return float(numbers[0])
            return 0.0
        
        # 숫자 타입인 경우
        return float(cell_value)
        
    except Exception:
        return 0.0

