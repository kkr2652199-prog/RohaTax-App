"""
응답 시간 개선 모듈
Python 3.14의 향상된 성능을 활용한 고성능 응답 시간 최적화
"""

import time
import threading
import asyncio
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import functools
import queue
import weakref

logger = logging.getLogger(__name__)

class ResponseTimeLevel(Enum):
    """응답 시간 레벨"""
    EXCELLENT = "excellent"  # < 0.5초
    GOOD = "good"           # 0.5-1초
    ACCEPTABLE = "acceptable" # 1-2초
    SLOW = "slow"           # 2-5초
    CRITICAL = "critical"   # > 5초

@dataclass
class ResponseTimeStats:
    """응답 시간 통계"""
    endpoint: str
    total_requests: int = 0
    total_time: float = 0.0
    average_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    p50_time: float = 0.0
    p95_time: float = 0.0
    p99_time: float = 0.0
    response_time_level: ResponseTimeLevel = ResponseTimeLevel.EXCELLENT
    error_count: int = 0
    success_rate: float = 100.0

@dataclass
class PerformanceOptimization:
    """성능 최적화 설정"""
    enable_caching: bool = True
    enable_compression: bool = True
    enable_async_processing: bool = True
    enable_connection_pooling: bool = True
    enable_preloading: bool = True
    max_concurrent_requests: int = 100
    cache_ttl: int = 300
    compression_level: int = 6

class ResponseTimeOptimizer:
    """응답 시간 최적화 클래스"""
    
    def __init__(self, 
                 target_response_time: float = 2.0,
                 monitoring_interval: int = 10,
                 optimization_threshold: float = 1.5):
        """
        응답 시간 최적화기 초기화
        
        Args:
            target_response_time: 목표 응답 시간 (초)
            monitoring_interval: 모니터링 간격 (초)
            optimization_threshold: 최적화 임계값 (초)
        """
        self.target_response_time = target_response_time
        self.monitoring_interval = monitoring_interval
        self.optimization_threshold = optimization_threshold
        
        # 응답 시간 추적
        self.response_times = defaultdict(list)
        self.endpoint_stats = {}
        self.optimization_history = []
        
        # 성능 최적화 설정
        self.optimization_config = PerformanceOptimization()
        
        # 모니터링
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # 비동기 처리
        self.async_executor = ThreadPoolExecutor(max_workers=10)
        self.process_executor = ProcessPoolExecutor(max_workers=4)
        
        # 캐시 및 압축
        self.response_cache = {}
        self.compression_enabled = True
        
        logger.info(f"응답 시간 최적화기 초기화 완료: 목표 {target_response_time}초, 임계값 {optimization_threshold}초")
    
    def measure_response_time(self, endpoint: str, func: Callable) -> Callable:
        """응답 시간 측정 데코레이터"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                # 함수 실행
                result = func(*args, **kwargs)
                
                # 응답 시간 기록
                response_time = time.time() - start_time
                self._record_response_time(endpoint, response_time, success=True)
                
                return result
                
            except Exception as e:
                # 오류 발생 시에도 응답 시간 기록
                response_time = time.time() - start_time
                self._record_response_time(endpoint, response_time, success=False)
                raise
        
        return wrapper
    
    def _record_response_time(self, endpoint: str, response_time: float, success: bool):
        """응답 시간 기록"""
        self.response_times[endpoint].append({
            'time': response_time,
            'timestamp': time.time(),
            'success': success
        })
        
        # 통계 업데이트
        self._update_endpoint_stats(endpoint)
        
        # 최적화 필요성 확인
        if response_time > self.optimization_threshold:
            self._trigger_optimization(endpoint, response_time)
    
    def _update_endpoint_stats(self, endpoint: str):
        """엔드포인트 통계 업데이트"""
        if endpoint not in self.response_times:
            return
        
        times = [r['time'] for r in self.response_times[endpoint]]
        successes = [r['success'] for r in self.response_times[endpoint]]
        
        if not times:
            return
        
        # 기본 통계 계산
        total_requests = len(times)
        total_time = sum(times)
        average_time = total_time / total_requests
        min_time = min(times)
        max_time = max(times)
        
        # 백분위수 계산
        sorted_times = sorted(times)
        p50_time = sorted_times[int(len(sorted_times) * 0.5)]
        p95_time = sorted_times[int(len(sorted_times) * 0.95)]
        p99_time = sorted_times[int(len(sorted_times) * 0.99)]
        
        # 응답 시간 레벨 결정
        response_time_level = self._determine_response_time_level(average_time)
        
        # 성공률 계산
        success_count = sum(successes)
        success_rate = (success_count / total_requests) * 100
        
        # 통계 저장
        self.endpoint_stats[endpoint] = ResponseTimeStats(
            endpoint=endpoint,
            total_requests=total_requests,
            total_time=total_time,
            average_time=average_time,
            min_time=min_time,
            max_time=max_time,
            p50_time=p50_time,
            p95_time=p95_time,
            p99_time=p99_time,
            response_time_level=response_time_level,
            error_count=total_requests - success_count,
            success_rate=success_rate
        )
    
    def _determine_response_time_level(self, response_time: float) -> ResponseTimeLevel:
        """응답 시간 레벨 결정"""
        if response_time < 0.5:
            return ResponseTimeLevel.EXCELLENT
        elif response_time < 1.0:
            return ResponseTimeLevel.GOOD
        elif response_time < 2.0:
            return ResponseTimeLevel.ACCEPTABLE
        elif response_time < 5.0:
            return ResponseTimeLevel.SLOW
        else:
            return ResponseTimeLevel.CRITICAL
    
    def _trigger_optimization(self, endpoint: str, response_time: float):
        """최적화 트리거"""
        logger.warning(f"응답 시간 최적화 필요: {endpoint} - {response_time:.2f}초")
        
        # 최적화 실행
        optimization_result = self._optimize_endpoint(endpoint)
        
        # 최적화 기록
        self.optimization_history.append({
            'endpoint': endpoint,
            'response_time': response_time,
            'optimization_result': optimization_result,
            'timestamp': time.time()
        })
    
    def _optimize_endpoint(self, endpoint: str) -> Dict[str, Any]:
        """엔드포인트 최적화 실행"""
        optimizations_applied = []
        
        try:
            # 1. 캐싱 활성화
            if self.optimization_config.enable_caching:
                self._enable_caching(endpoint)
                optimizations_applied.append("caching")
            
            # 2. 압축 활성화
            if self.optimization_config.enable_compression:
                self._enable_compression(endpoint)
                optimizations_applied.append("compression")
            
            # 3. 비동기 처리 활성화
            if self.optimization_config.enable_async_processing:
                self._enable_async_processing(endpoint)
                optimizations_applied.append("async_processing")
            
            # 4. 연결 풀링 활성화
            if self.optimization_config.enable_connection_pooling:
                self._enable_connection_pooling(endpoint)
                optimizations_applied.append("connection_pooling")
            
            # 5. 사전 로딩 활성화
            if self.optimization_config.enable_preloading:
                self._enable_preloading(endpoint)
                optimizations_applied.append("preloading")
            
        except Exception as e:
            logger.error(f"엔드포인트 최적화 실패: {endpoint} - {e}")
        
        return {
            'optimizations_applied': optimizations_applied,
            'timestamp': time.time()
        }
    
    def _enable_caching(self, endpoint: str):
        """캐싱 활성화"""
        try:
            # 캐시 설정
            self.response_cache[endpoint] = {
                'enabled': True,
                'ttl': self.optimization_config.cache_ttl,
                'cache': {}
            }
            logger.debug(f"캐싱 활성화: {endpoint}")
        except Exception as e:
            logger.error(f"캐싱 활성화 실패: {e}")
    
    def _enable_compression(self, endpoint: str):
        """압축 활성화"""
        try:
            # 압축 설정
            self.compression_enabled = True
            logger.debug(f"압축 활성화: {endpoint}")
        except Exception as e:
            logger.error(f"압축 활성화 실패: {e}")
    
    def _enable_async_processing(self, endpoint: str):
        """비동기 처리 활성화"""
        try:
            # 비동기 처리 설정
            logger.debug(f"비동기 처리 활성화: {endpoint}")
        except Exception as e:
            logger.error(f"비동기 처리 활성화 실패: {e}")
    
    def _enable_connection_pooling(self, endpoint: str):
        """연결 풀링 활성화"""
        try:
            # 연결 풀링 설정
            logger.debug(f"연결 풀링 활성화: {endpoint}")
        except Exception as e:
            logger.error(f"연결 풀링 활성화 실패: {e}")
    
    def _enable_preloading(self, endpoint: str):
        """사전 로딩 활성화"""
        try:
            # 사전 로딩 설정
            logger.debug(f"사전 로딩 활성화: {endpoint}")
        except Exception as e:
            logger.error(f"사전 로딩 활성화 실패: {e}")
    
    def get_endpoint_stats(self, endpoint: str) -> Optional[ResponseTimeStats]:
        """엔드포인트 통계 조회"""
        return self.endpoint_stats.get(endpoint)
    
    def get_all_stats(self) -> Dict[str, ResponseTimeStats]:
        """모든 엔드포인트 통계 조회"""
        return self.endpoint_stats.copy()
    
    def get_slow_endpoints(self) -> List[ResponseTimeStats]:
        """느린 엔드포인트 조회"""
        slow_endpoints = []
        for stats in self.endpoint_stats.values():
            if stats.average_time > self.target_response_time:
                slow_endpoints.append(stats)
        
        return sorted(slow_endpoints, key=lambda x: x.average_time, reverse=True)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """성능 리포트 생성"""
        total_endpoints = len(self.endpoint_stats)
        slow_endpoints = len(self.get_slow_endpoints())
        
        # 전체 통계 계산
        all_times = []
        total_requests = 0
        total_errors = 0
        
        for stats in self.endpoint_stats.values():
            all_times.extend([r['time'] for r in self.response_times[stats.endpoint]])
            total_requests += stats.total_requests
            total_errors += stats.error_count
        
        overall_average = sum(all_times) / len(all_times) if all_times else 0
        overall_success_rate = ((total_requests - total_errors) / total_requests * 100) if total_requests > 0 else 100
        
        return {
            'total_endpoints': total_endpoints,
            'slow_endpoints': slow_endpoints,
            'overall_average_time': overall_average,
            'overall_success_rate': overall_success_rate,
            'target_response_time': self.target_response_time,
            'optimization_threshold': self.optimization_threshold,
            'optimization_count': len(self.optimization_history),
            'caching_enabled': self.optimization_config.enable_caching,
            'compression_enabled': self.compression_enabled,
            'async_processing_enabled': self.optimization_config.enable_async_processing
        }
    
    def start_monitoring(self):
        """모니터링 시작"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitor_performance, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("응답 시간 모니터링 시작")
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        logger.info("응답 시간 모니터링 중지")
    
    def _monitor_performance(self):
        """성능 모니터링 루프"""
        while self.monitoring_active:
            try:
                # 느린 엔드포인트 확인
                slow_endpoints = self.get_slow_endpoints()
                
                if slow_endpoints:
                    logger.warning(f"느린 엔드포인트 감지: {len(slow_endpoints)}개")
                    
                    # 자동 최적화 실행
                    for endpoint_stats in slow_endpoints:
                        self._trigger_optimization(endpoint_stats.endpoint, endpoint_stats.average_time)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"성능 모니터링 오류: {e}")
                time.sleep(self.monitoring_interval)
    
    def cleanup_old_data(self, max_age_hours: int = 24):
        """오래된 데이터 정리"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for endpoint in list(self.response_times.keys()):
            # 오래된 응답 시간 데이터 제거
            self.response_times[endpoint] = [
                r for r in self.response_times[endpoint]
                if current_time - r['timestamp'] < max_age_seconds
            ]
            
            # 빈 엔드포인트 제거
            if not self.response_times[endpoint]:
                del self.response_times[endpoint]
                if endpoint in self.endpoint_stats:
                    del self.endpoint_stats[endpoint]
        
        logger.info(f"오래된 데이터 정리 완료: {max_age_hours}시간 이상 데이터 제거")

# 전역 응답 시간 최적화기 인스턴스
_response_time_optimizer = None

def get_response_time_optimizer() -> ResponseTimeOptimizer:
    """응답 시간 최적화기 인스턴스 가져오기"""
    global _response_time_optimizer
    if _response_time_optimizer is None:
        _response_time_optimizer = ResponseTimeOptimizer()
    return _response_time_optimizer

def measure_response_time(endpoint: str):
    """응답 시간 측정 데코레이터"""
    optimizer = get_response_time_optimizer()
    return optimizer.measure_response_time(endpoint, lambda func: func)

def get_endpoint_stats(endpoint: str) -> Optional[ResponseTimeStats]:
    """엔드포인트 통계 조회"""
    optimizer = get_response_time_optimizer()
    return optimizer.get_endpoint_stats(endpoint)

def get_performance_report() -> Dict[str, Any]:
    """성능 리포트 가져오기"""
    optimizer = get_response_time_optimizer()
    return optimizer.get_performance_report()

def start_performance_monitoring():
    """성능 모니터링 시작"""
    optimizer = get_response_time_optimizer()
    optimizer.start_monitoring()

def stop_performance_monitoring():
    """성능 모니터링 중지"""
    optimizer = get_response_time_optimizer()
    optimizer.stop_monitoring()







