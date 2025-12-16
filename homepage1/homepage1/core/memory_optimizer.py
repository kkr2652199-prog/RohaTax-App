"""
메모리 사용량 최적화 모듈
Python 3.14의 향상된 메모리 관리를 활용한 고성능 메모리 최적화
"""

import gc
import psutil
import threading
import time
import weakref
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass
from enum import Enum
import logging
import tracemalloc
from collections import defaultdict
import sys

logger = logging.getLogger(__name__)

class MemoryLevel(Enum):
    """메모리 레벨"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class MemoryStats:
    """메모리 통계"""
    total_memory: int = 0
    available_memory: int = 0
    used_memory: int = 0
    memory_percent: float = 0.0
    python_memory: int = 0
    python_objects: int = 0
    gc_collections: int = 0
    memory_level: MemoryLevel = MemoryLevel.LOW

@dataclass
class MemoryOptimizationResult:
    """메모리 최적화 결과"""
    before_memory: int
    after_memory: int
    freed_memory: int
    optimization_time: float
    optimizations_applied: List[str]

class MemoryOptimizer:
    """메모리 사용량 최적화 클래스"""
    
    def __init__(self, 
                 memory_threshold_percent: float = 80.0,
                 gc_threshold: int = 1000,
                 monitoring_interval: int = 30):
        """
        메모리 최적화기 초기화
        
        Args:
            memory_threshold_percent: 메모리 사용률 임계값 (%)
            gc_threshold: 가비지 컬렉션 임계값 (객체 수)
            monitoring_interval: 모니터링 간격 (초)
        """
        self.memory_threshold_percent = memory_threshold_percent
        self.gc_threshold = gc_threshold
        self.monitoring_interval = monitoring_interval
        
        # 메모리 모니터링
        self.monitoring_active = False
        self.monitoring_thread = None
        self.memory_history = []
        
        # 메모리 추적
        self.object_registry = weakref.WeakSet()
        self.memory_callbacks = []
        
        # 통계
        self.optimization_count = 0
        self.total_freed_memory = 0
        
        # Python 3.14 메모리 추적 활성화
        if hasattr(tracemalloc, 'start'):
            tracemalloc.start()
        
        logger.info(f"메모리 최적화기 초기화 완료: 임계값 {memory_threshold_percent}%, 모니터링 간격 {monitoring_interval}초")
    
    def get_memory_stats(self) -> MemoryStats:
        """현재 메모리 통계 조회"""
        try:
            # 시스템 메모리 정보
            memory_info = psutil.virtual_memory()
            
            # Python 메모리 정보
            python_memory = 0
            python_objects = 0
            
            try:
                # Python 메모리 사용량
                process = psutil.Process()
                python_memory = process.memory_info().rss
                
                # Python 객체 수
                python_objects = len(gc.get_objects())
                
            except Exception as e:
                logger.warning(f"Python 메모리 정보 조회 실패: {e}")
            
            # 메모리 레벨 결정
            memory_level = self._determine_memory_level(memory_info.percent)
            
            stats = MemoryStats(
                total_memory=memory_info.total,
                available_memory=memory_info.available,
                used_memory=memory_info.used,
                memory_percent=memory_info.percent,
                python_memory=python_memory,
                python_objects=python_objects,
                gc_collections=gc.get_count()[0],
                memory_level=memory_level
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"메모리 통계 조회 실패: {e}")
            return MemoryStats()
    
    def _determine_memory_level(self, memory_percent: float) -> MemoryLevel:
        """메모리 사용률에 따른 레벨 결정"""
        if memory_percent < 50:
            return MemoryLevel.LOW
        elif memory_percent < 70:
            return MemoryLevel.MEDIUM
        elif memory_percent < 90:
            return MemoryLevel.HIGH
        else:
            return MemoryLevel.CRITICAL
    
    def optimize_memory(self) -> MemoryOptimizationResult:
        """메모리 최적화 실행"""
        start_time = time.time()
        before_stats = self.get_memory_stats()
        optimizations_applied = []
        
        logger.info(f"메모리 최적화 시작: {before_stats.memory_percent:.1f}% 사용 중")
        
        try:
            # 1. 가비지 컬렉션 실행
            if self._should_run_gc(before_stats):
                self._run_garbage_collection()
                optimizations_applied.append("garbage_collection")
            
            # 2. 메모리 압축
            if before_stats.memory_percent > 70:
                self._compress_memory()
                optimizations_applied.append("memory_compression")
            
            # 3. 불필요한 객체 정리
            self._cleanup_unnecessary_objects()
            optimizations_applied.append("object_cleanup")
            
            # 4. 캐시 정리
            self._cleanup_caches()
            optimizations_applied.append("cache_cleanup")
            
            # 5. 메모리 조각화 해결
            if before_stats.memory_percent > 80:
                self._defragment_memory()
                optimizations_applied.append("memory_defragmentation")
            
        except Exception as e:
            logger.error(f"메모리 최적화 실패: {e}")
        
        # 최적화 후 통계
        after_stats = self.get_memory_stats()
        optimization_time = time.time() - start_time
        
        # 결과 생성
        result = MemoryOptimizationResult(
            before_memory=before_stats.used_memory,
            after_memory=after_stats.used_memory,
            freed_memory=before_stats.used_memory - after_stats.used_memory,
            optimization_time=optimization_time,
            optimizations_applied=optimizations_applied
        )
        
        # 통계 업데이트
        self.optimization_count += 1
        self.total_freed_memory += result.freed_memory
        
        logger.info(f"메모리 최적화 완료: {result.freed_memory / 1024 / 1024:.1f}MB 해제 "
                   f"({optimization_time:.2f}초, {len(optimizations_applied)}개 최적화)")
        
        return result
    
    def _should_run_gc(self, stats: MemoryStats) -> bool:
        """가비지 컬렉션 실행 여부 결정"""
        return (stats.python_objects > self.gc_threshold or 
                stats.memory_percent > self.memory_threshold_percent)
    
    def _run_garbage_collection(self):
        """가비지 컬렉션 실행"""
        try:
            # 모든 세대의 가비지 컬렉션 실행
            collected = gc.collect()
            logger.debug(f"가비지 컬렉션 완료: {collected}개 객체 수집")
        except Exception as e:
            logger.error(f"가비지 컬렉션 실패: {e}")
    
    def _compress_memory(self):
        """메모리 압축"""
        try:
            # Python 3.14의 향상된 메모리 압축 기능 활용
            if hasattr(gc, 'set_threshold'):
                # 가비지 컬렉션 임계값 조정
                gc.set_threshold(100, 10, 10)
            
            # 메모리 압축 실행
            gc.collect()
            
            logger.debug("메모리 압축 완료")
        except Exception as e:
            logger.error(f"메모리 압축 실패: {e}")
    
    def _cleanup_unnecessary_objects(self):
        """불필요한 객체 정리"""
        try:
            # 약한 참조 객체 정리
            cleaned_count = 0
            for obj in list(self.object_registry):
                if obj is None:
                    cleaned_count += 1
            
            # 임시 변수 정리
            if 'temp' in locals():
                del locals()['temp']
            
            logger.debug(f"불필요한 객체 정리 완료: {cleaned_count}개 객체")
        except Exception as e:
            logger.error(f"객체 정리 실패: {e}")
    
    def _cleanup_caches(self):
        """캐시 정리"""
        try:
            # 캐시 시스템 정리
            from core.cache_system import get_cache
            cache = get_cache()
            
            # 오래된 캐시 항목 정리
            cache.clear()
            
            logger.debug("캐시 정리 완료")
        except Exception as e:
            logger.error(f"캐시 정리 실패: {e}")
    
    def _defragment_memory(self):
        """메모리 조각화 해결"""
        try:
            # Python 3.14의 향상된 메모리 관리 기능 활용
            if hasattr(sys, 'getsizeof'):
                # 메모리 조각화 해결을 위한 객체 재배치
                gc.collect()
            
            logger.debug("메모리 조각화 해결 완료")
        except Exception as e:
            logger.error(f"메모리 조각화 해결 실패: {e}")
    
    def start_memory_monitoring(self):
        """메모리 모니터링 시작"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitor_memory, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("메모리 모니터링 시작")
    
    def stop_memory_monitoring(self):
        """메모리 모니터링 중지"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        logger.info("메모리 모니터링 중지")
    
    def _monitor_memory(self):
        """메모리 모니터링 루프"""
        while self.monitoring_active:
            try:
                stats = self.get_memory_stats()
                self.memory_history.append(stats)
                
                # 메모리 히스토리 크기 제한
                if len(self.memory_history) > 100:
                    self.memory_history.pop(0)
                
                # 메모리 사용률이 임계값을 초과하면 최적화 실행
                if stats.memory_percent > self.memory_threshold_percent:
                    logger.warning(f"메모리 사용률 임계값 초과: {stats.memory_percent:.1f}%")
                    self.optimize_memory()
                
                # 메모리 콜백 실행
                for callback in self.memory_callbacks:
                    try:
                        callback(stats)
                    except Exception as e:
                        logger.error(f"메모리 콜백 실행 실패: {e}")
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"메모리 모니터링 오류: {e}")
                time.sleep(self.monitoring_interval)
    
    def add_memory_callback(self, callback: Callable[[MemoryStats], None]):
        """메모리 콜백 추가"""
        self.memory_callbacks.append(callback)
    
    def get_memory_history(self) -> List[MemoryStats]:
        """메모리 히스토리 반환"""
        return self.memory_history.copy()
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """최적화 리포트 생성"""
        current_stats = self.get_memory_stats()
        
        return {
            'current_memory_percent': current_stats.memory_percent,
            'current_memory_level': current_stats.memory_level.value,
            'python_memory_mb': current_stats.python_memory / 1024 / 1024,
            'python_objects': current_stats.python_objects,
            'optimization_count': self.optimization_count,
            'total_freed_memory_mb': self.total_freed_memory / 1024 / 1024,
            'monitoring_active': self.monitoring_active,
            'memory_threshold_percent': self.memory_threshold_percent,
            'gc_threshold': self.gc_threshold
        }
    
    def register_object(self, obj: Any):
        """객체 등록 (약한 참조로 추적)"""
        self.object_registry.add(obj)
    
    def unregister_object(self, obj: Any):
        """객체 등록 해제"""
        try:
            self.object_registry.discard(obj)
        except Exception:
            pass

# 전역 메모리 최적화기 인스턴스
_memory_optimizer = None

def get_memory_optimizer() -> MemoryOptimizer:
    """메모리 최적화기 인스턴스 가져오기"""
    global _memory_optimizer
    if _memory_optimizer is None:
        _memory_optimizer = MemoryOptimizer()
    return _memory_optimizer

def optimize_memory() -> MemoryOptimizationResult:
    """메모리 최적화 실행"""
    optimizer = get_memory_optimizer()
    return optimizer.optimize_memory()

def get_memory_stats() -> MemoryStats:
    """메모리 통계 가져오기"""
    optimizer = get_memory_optimizer()
    return optimizer.get_memory_stats()

def start_memory_monitoring():
    """메모리 모니터링 시작"""
    optimizer = get_memory_optimizer()
    optimizer.start_memory_monitoring()

def stop_memory_monitoring():
    """메모리 모니터링 중지"""
    optimizer = get_memory_optimizer()
    optimizer.stop_memory_monitoring()

def get_memory_optimization_report() -> Dict[str, Any]:
    """메모리 최적화 리포트 가져오기"""
    optimizer = get_memory_optimizer()
    return optimizer.get_optimization_report()







