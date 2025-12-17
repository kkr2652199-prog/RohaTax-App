"""
동적 컬럼 매핑 모듈

지능앱 핵심 기술: 동적 컬럼 매핑
스코어링 기반으로 최적의 공급가액/부가세 컬럼을 선택하는 기능을 제공합니다.
"""

import pandas as pd
import numpy as np
import re
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)
# 제트엔진 모드: 로그 레벨 최적화 (WARNING 이상만 출력)
logger.setLevel(logging.WARNING)

class ColumnMapper:
    """동적 컬럼 매핑기"""
    
    def __init__(self):
        self.logger = logger

    def dynamic_column_mapping(self, df: pd.DataFrame, column_names: List[str]) -> Tuple[Optional[int], Optional[int]]:
        """
        지능앱 핵심 기술: 동적 컬럼 매핑
        스코어링 기반으로 최적의 공급가액/부가세 컬럼 선택
        """
        try:
            # 부가세 컬럼 먼저 찾기
            vat_col = self._find_vat_column(df, column_names)
            
            # 공급가액 컬럼 찾기 (VAT와의 관계 고려)
            supply_col = self._find_supply_amount_column(df, column_names, vat_col)
            
            # VAT 헤더를 못 찾았지만 공급가액 컬럼이 있으면 인접 추론 시도(좌/우 1열)
            if vat_col is None and supply_col is not None:
                inferred_vat = self._infer_vat_near_supply(df, column_names, supply_col)
                if inferred_vat is not None:
                    self.logger.info(f"참고 규칙 적용: 공급가액 인접 열에서 부가세 추론 성공 (컬럼 {inferred_vat})")
                    self.logger.info("AUX_RULE_USED: VAT_NEAR_SUPPLY=true")
                    vat_col = inferred_vat

            return supply_col, vat_col
            
        except Exception as e:
            self.logger.error(f"지능앱 동적 컬럼 매핑 오류: {str(e)}")
            return None, None

    def _infer_vat_near_supply(self, df: pd.DataFrame, column_names: List[str], supply_col: int) -> Optional[int]:
        """
        참고 규칙: 공급가액 컬럼 좌/우 1열 내에서 부가세 후보를 추론
        - 헤더 키워드(부가세/VAT/세액) 또는 금액 관계(약 10%)를 기준으로 판단
        """
        try:
            candidates = []
            num_cols = len(column_names)
            neighbor_indices = []
            if supply_col - 1 >= 0:
                neighbor_indices.append(supply_col - 1)
            if supply_col + 1 < num_cols:
                neighbor_indices.append(supply_col + 1)

            supply_series = self._parse_numeric_series(df.iloc[:, supply_col])
            if (supply_series > 0).sum() == 0:
                return None

            vat_keywords = ['부가세', '세액', 'vat', '세금', '세']
            for idx in neighbor_indices:
                header = str(column_names[idx]).lower().strip()
                series = self._parse_numeric_series(df.iloc[:, idx])
                if (series > 0).sum() == 0:
                    continue

                # 헤더 키워드 점수
                kw_score = 1 if any(k in header for k in vat_keywords) else 0

                # 10% 관계 오차(중앙값) 기반 점수
                diff = (series - supply_series * 0.1).abs()
                median_err = float(np.median(diff.replace(np.nan, 0)))
                rel_score = -median_err  # 작을수록 우수

                total = kw_score * 2 + rel_score
                candidates.append((total, -median_err, kw_score, idx))

            if not candidates:
                return None

            # 최고 점수 선택: total, 그 다음 오차가 작은 것
            candidates.sort(reverse=True)
            best = candidates[0]
            return best[3]
        except Exception as e:
            self.logger.error(f"VAT 인접 추론 오류: {str(e)}")
            return None
    
    def _find_vat_column(self, df: pd.DataFrame, column_names: List[str]) -> Optional[int]:
        """부가세 컬럼 찾기 (부가세 앞칸 규칙 적용)
        - '부가세 합계/총합계/누계' 등 집계성 헤더는 힌트로만 사용하고 후보에서 제외
        """
        try:
            # 비교는 소문자로 통일
            vat_keywords = ['부가세', '세액', 'vat', '세금', '세']
            aggregate_tokens = ["부가세 합계".lower()]
            forbidden_family_headers = ['콜수수료 부가세'.lower()]
            
            for col_idx, col_name in enumerate(column_names):
                col_name_lower = col_name.lower()
                
                for keyword in vat_keywords:
                    if keyword in col_name_lower:
                        # 가족 금지 헤더(예: 콜수수료 부가세)
                        if any(fh in col_name_lower for fh in forbidden_family_headers):
                            self.logger.info(f"FORBIDDEN_SKIP: FAMILY_VAT_HEADER skip='{col_name}' (col {col_idx})")
                            continue
                        # 집계성 헤더는 힌트로만 사용하고 스킵
                        if any(tok in col_name_lower for tok in aggregate_tokens):
                            self.logger.info(f"HINT_ONLY: VAT_AGG_HEADER_DETECTED skip='{col_name}' (col {col_idx})")
                            continue
                        # 추가 검증: 해당 컬럼에 숫자 데이터가 있는지 확인
                        numeric_count = self._count_numeric_values(df.iloc[:, col_idx])
                        if numeric_count > 0:
                            self.logger.info(f"지능앱 부가세 컬럼 발견: {col_name} (컬럼 {col_idx}, 숫자 데이터 {numeric_count}개)")
                            
                            # 부가세 앞칸 규칙 적용: 부가세 앞칸이 총합계인지 확인
                            total_col = self._validate_total_column_before_vat(df, col_idx)
                            if total_col is not None:
                                self.logger.info(f"부가세 앞칸 규칙 적용: 부가세 컬럼 {col_idx} 앞칸 {total_col}이 총합계로 확인됨")
                            
                            return col_idx

            # 헤더 매칭 실패 시: 헤더 아래 셀 텍스트 스캔으로 VAT 열 추론
            inferred_vat_by_cells = self._find_vat_by_cell_text(df)
            if inferred_vat_by_cells is not None:
                self.logger.info(f"보강 탐색: 셀 텍스트 스캔으로 부가세 후보 열 감지 (컬럼 {inferred_vat_by_cells})")
                total_col = self._validate_total_column_before_vat(df, inferred_vat_by_cells)
                if total_col is not None:
                    self.logger.info(f"보강 탐색 검증 성공: 컬럼 {inferred_vat_by_cells}는 유효한 부가세 열로 판단 (앞칸 총합계 {total_col})")
                return inferred_vat_by_cells
            
            self.logger.warning("지능앱 부가세 컬럼을 찾을 수 없습니다")
            return None
            
        except Exception as e:
            self.logger.error(f"지능앱 부가세 컬럼 찾기 오류: {str(e)}")
            return None
    
    def _validate_total_column_before_vat(self, df: pd.DataFrame, vat_col: int) -> Optional[int]:
        """부가세 앞칸이 총합계인지 확인 (10:1 비율 검증)"""
        try:
            if vat_col <= 0:
                return None
            
            # 부가세 앞칸 확인
            total_col = vat_col - 1
            if total_col < 0:
                return None
            
            # 10:1 비율 확인 (부가세 10% 규칙)
            valid_rows = 0
            total_rows = 0
            
            for row_idx in range(len(df)):
                try:
                    total_value = df.iloc[row_idx, total_col]
                    vat_value = df.iloc[row_idx, vat_col]
                    
                    # 숫자 데이터인지 확인
                    if pd.isna(total_value) or pd.isna(vat_value):
                        continue
                    
                    total_value = float(total_value)
                    vat_value = float(vat_value)
                    
                    if total_value <= 0 or vat_value <= 0:
                        continue
                    
                    total_rows += 1
                    
                    # 10:1 비율 확인 (9.5:1 ~ 10.5:1 범위 허용)
                    ratio = total_value / vat_value
                    if 9.5 <= ratio <= 10.5:
                        valid_rows += 1
                        
                except (ValueError, TypeError):
                    continue
            
            # 70% 이상의 행이 10:1 비율을 만족하면 유효한 총합계 컬럼으로 인정
            if total_rows > 0 and (valid_rows / total_rows) >= 0.7:
                self.logger.info(f"부가세 앞칸 규칙 검증 성공: 컬럼 {total_col}이 총합계로 확인됨 (유효 비율: {valid_rows}/{total_rows})")
                return total_col
            
            return None
            
        except Exception as e:
            self.logger.error(f"부가세 앞칸 규칙 검증 오류: {str(e)}")
            return None
    
    def _find_supply_amount_column(self, df: pd.DataFrame, column_names: List[str], vat_col: Optional[int]) -> Optional[int]:
        """공급가액 컬럼 찾기 (지능앱 핵심 기술: 스코어링 기반 + 부가세 앞칸 규칙)"""
        try:
            # 부가세 앞칸 규칙 우선 적용
            if vat_col is not None:
                total_col = self._validate_total_column_before_vat(df, vat_col)
                if total_col is not None:
                    self.logger.info(f"부가세 앞칸 규칙으로 공급가액 컬럼 확정: {total_col}")
                    return total_col
            
            supply_strong_headers = {
                "공급가액", "공급가액합계", "공급가액 합계", "공급가액합", "과세표준", "과표",
                "총공급가액", "합계(공급가액)", "총액(공급가액)"
            }
            forbidden_supply_headers = ['콜수수료 공급가', '콜수수료 공급액']
            
            # 공급가액 컬럼에서 제외할 헤더 (금지어 포함)
            exclude_headers = {
                "사업자", "등록번호", "사업자번호", "사업자등록번호", "주민번호", "라이더실명",
                "도착지", "상세", "주소", "이름", "이메일",
                "수수료", "공급수수료"
            }
            
            best_candidate = {
                "idx": None,
                "total_score": -1e9,
                "median_err": float("inf"),
                "adj_vat": False,
                "header": "",
                "reason": ""
            }
            
            # 부가세 컬럼이 있으면 VAT와의 관계 분석
            vat_series = None
            if vat_col is not None:
                vat_series = self._parse_numeric_series(df.iloc[:, vat_col])
            
            # 모든 컬럼을 후보로 평가
            for col_idx in range(len(column_names)):
                if col_idx == vat_col:
                    continue
                    
                header_text = str(column_names[col_idx]).strip()
                candidate_series = self._parse_numeric_series(df.iloc[:, col_idx])
                
                # 사업자번호 등 제외 조건
                if any(exclude_h in header_text for exclude_h in exclude_headers):
                    continue
                # 가족 금지 공급가 헤더 제외
                header_lower = header_text.lower()
                if any(fs in header_lower for fs in forbidden_supply_headers):
                    self.logger.info(f"FORBIDDEN_SKIP: FAMILY_SUPPLY_HEADER skip='{header_text}' (col {col_idx})")
                    continue
                
                # 유효성 검사: 숫자 데이터가 충분한지 확인
                valid_count = int((candidate_series > 0).sum())
                if valid_count < max(3, int(0.05 * len(candidate_series))):
                    reason = "유효값 부족"
                    total_score = -1e6
                    median_err = float("inf")
                    adj_vat = False
                else:
                    # 지능앱 기술: VAT와의 관계 분석 (10% 관계)
                    if vat_series is not None and len(vat_series) > 0:
                        diff = (vat_series - candidate_series * 0.1).abs()
                        median_err = float(diff.median(skipna=True)) if hasattr(diff, 'median') else diff.median()
                        rel_score = -median_err  # 작을수록 점수 큼
                    else:
                        rel_score = 0
                        median_err = 0
                    
                    # 헤더 점수 (지능앱 기술) - 강화된 키워드 매칭
                    header_score = 0
                    if any(h in header_text for h in supply_strong_headers):
                        header_score += 3  # 강화된 점수
                    if "합계" in header_text:
                        header_score += 1
                    if "총" in header_text:
                        header_score += 1
                    
                    # VAT 인접성 점수
                    adj_vat = (vat_col is not None and col_idx + 1 == vat_col)
                    adj_score = 1 if adj_vat else 0
                    
                    total_score = rel_score + header_score + adj_score
                    reason = ""
                
                # 최고 점수 후보 갱신
                if total_score > best_candidate["total_score"]:
                    best_candidate = {
                        "idx": col_idx,
                        "total_score": total_score,
                        "median_err": median_err,
                        "adj_vat": adj_vat,
                        "header": header_text,
                        "reason": reason
                    }
            
            if best_candidate["idx"] is not None:
                self.logger.info(f"지능앱 공급가액 컬럼 선택: '{best_candidate['header']}' (컬럼 {best_candidate['idx']}, 점수: {best_candidate['total_score']:.2f})")
                if best_candidate["adj_vat"]:
                    self.logger.info("지능앱 VAT 인접성 확인: 공급가액 컬럼이 부가세 컬럼 바로 앞에 위치")
                return best_candidate["idx"]
            else:
                self.logger.warning("지능앱 공급가액 컬럼을 찾을 수 없습니다")
                return None
                
        except Exception as e:
            self.logger.error(f"지능앱 공급가액 컬럼 찾기 오류: {str(e)}")
            return None

    def _find_vat_by_cell_text(self, df: pd.DataFrame) -> Optional[int]:
        """
        헤더 아래 실제 셀 텍스트를 가로/세로로 스캔하여 VAT 열을 추론한다.
        - 범위: 헤더 바로 아래(start_row)부터 유효 데이터 끝까지
        - 키워드: 부가세/세액/VAT/세금/세 (대소문자 무시, 부분 일치)
        - 반환: 후보 VAT 열 인덱스 또는 None
        """
        try:
            if df is None or df.empty:
                return None

            vat_keywords = ["부가세", "세액", "vat", "세금", "세"]
            aggregate_tokens = ["부가세 합계".lower()]
            forbidden_family_headers = ["콜수수료 부가세".lower()]

            # 상단 헤더 영역을 대략 1~5행으로 가정(헤더 검출 고도화 여지는 있음)
            start_row = min(5, max(0, int(len(df) * 0.02)))

            candidates: List[Tuple[float, int]] = []
            num_cols = df.shape[1]

            for col_idx in range(num_cols):
                # 집계/금지 헤더는 셀 스캔 단계에서도 엄마 후보에서 제외
                header_lower = str(getattr(df.columns, '__iter__', lambda: [])().__next__() if False else str(df.columns[col_idx])).lower().strip()
                if any(tok in header_lower for tok in aggregate_tokens) or any(fh in header_lower for fh in forbidden_family_headers):
                    # 힌트만 남기고 후보 제외
                    if any(tok in header_lower for tok in aggregate_tokens):
                        logger.info(f"HINT_ONLY: VAT_AGG_HEADER_DETECTED skip_by_cells='{df.columns[col_idx]}' (col {col_idx})")
                    else:
                        logger.info(f"FORBIDDEN_SKIP: FAMILY_VAT_HEADER skip_by_cells='{df.columns[col_idx]}' (col {col_idx})")
                    continue
                col_series = df.iloc[start_row:, col_idx]
                text_series = col_series.astype(str).str.lower().str.replace('\u00a0', ' ', regex=False).str.strip()

                # 키워드 히트(부분 일치)
                kw_hit = any(text_series.str.contains(kw, na=False) for kw in vat_keywords)

                # 숫자 존재(부가세는 금액형일 가능성)
                numeric_count = self._count_numeric_values(df.iloc[:, col_idx])

                score = 0
                if kw_hit:
                    score += 2
                if numeric_count >= 3:
                    score += 1

                if score > 0:
                    candidates.append((float(score), col_idx))

            if not candidates:
                return None

            candidates.sort(key=lambda x: (-x[0], x[1]))
            return candidates[0][1]

        except Exception as e:
            self.logger.error(f"VAT 셀 텍스트 스캔 오류: {str(e)}")
            return None
    
    def _count_numeric_values(self, series: pd.Series) -> int:
        """시리즈에서 숫자 값의 개수 계산"""
        try:
            numeric_series = pd.to_numeric(series, errors='coerce')
            return int(numeric_series.notna().sum())
        except Exception:
            return 0
    
    def _parse_numeric_series(self, series: pd.Series) -> pd.Series:
        """
        지능앱 기술: 숫자 파싱 보강
        천단위 구분자/통화 문자 제거 및 기본 단위 스케일 감지
        """
        try:
            import re
            
            # 문자열 정제
            s = series.astype(str).str.replace(',', '', regex=False)
            
            # 유럽식 천단위 점(.) 제거
            def _strip_thousand_dots(x: str) -> str:
                if '.' not in x:
                    return x
                if x.count('.') >= 2 or re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", x):
                    return x.replace('.', '')
                return x
            
            s = s.apply(_strip_thousand_dots)
            s = s.str.replace('\u00a0', ' ', regex=False)  # non-breaking space
            s = s.str.replace('원', '', regex=False)
            s = s.str.replace('￦', '', regex=False)  # fullwidth Won sign
            s = s.str.replace('\u20a9', '', regex=False)  # normal Won sign ₩
            s = s.str.replace('KRW', '', case=False, regex=False)
            
            # 회계표기 음수 (1,234) → -1234 처리
            s = s.str.replace(r"^\((.+)\)$", r"-\1", regex=True)
            
            # 숫자/소수점/음수만 남기기
            s = s.apply(lambda x: re.sub(r"[^0-9\.-]", '', x))
            
            num = pd.to_numeric(s, errors='coerce').fillna(0)

            # 안전 스케일링: 기본 원 단위, 헤더 단서가 있을 때만 적용
            header_text = (str(getattr(series, "name", "")) or "").lower()
            scale = 1
            if "천원" in header_text:
                scale = 1000
            elif "만원" in header_text:
                scale = 10000

            return num * scale
            
        except Exception as e:
            self.logger.error(f"지능앱 숫자 파싱 오류: {str(e)}")
            return pd.Series(0, index=series.index, dtype=float)



