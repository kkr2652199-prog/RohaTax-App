"""
고성능 캐싱 시스템
Python 3.14의 향상된 성능을 활용한 다층 캐싱 시스템
"""

import time
import threading
import hashlib
import json
import pickle
import os
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging
from collections import OrderedDict
import weakref

logger = logging.getLogger(__name__)

class CacheLevel(Enum):
    """캐시 레벨"""
    MEMORY = "memory"
    DISK = "disk"
    REDIS = "redis"

@dataclass
class CacheItem:
    """캐시 아이템"""
    key: str
    value: Any
    created_at: float
    expires_at: Optional[float] = None
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    size_bytes: int = 0

@dataclass
class CacheStats:
    """캐시 통계"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size: int = 0
    hit_rate: float = 0.0

class MemoryCache:
    """메모리 캐시 (LRU 기반)"""
    
    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache = OrderedDict()
        self.stats = CacheStats()
        self.lock = threading.RLock()
        
        logger.info(f"메모리 캐시 초기화: 최대 {max_size}개 아이템, {max_memory_mb}MB")
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        with self.lock:
            if key in self.cache:
                item = self.cache[key]
                
                # 만료 확인
                if item.expires_at and time.time() > item.expires_at:
                    del self.cache[key]
                    self.stats.misses += 1
                    return None
                
                # LRU 업데이트
                self.cache.move_to_end(key)
                item.access_count += 1
                item.last_accessed = time.time()
                
                self.stats.hits += 1
                return item.value
            
            self.stats.misses += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """캐시에 값 저장"""
        with self.lock:
            try:
                # 값 크기 계산
                size_bytes = self._calculate_size(value)
                
                # 메모리 제한 확인
                if size_bytes > self.max_memory_bytes:
                    logger.warning(f"아이템이 너무 큼: {size_bytes} bytes")
                    return False
                
                # 만료 시간 설정
                expires_at = None
                if ttl:
                    expires_at = time.time() + ttl
                
                # 캐시 아이템 생성
                item = CacheItem(
                    key=key,
                    value=value,
                    created_at=time.time(),
                    expires_at=expires_at,
                    size_bytes=size_bytes
                )
                
                # 기존 아이템 제거
                if key in self.cache:
                    old_item = self.cache[key]
                    self.stats.total_size -= old_item.size_bytes
                
                # 새 아이템 추가
                self.cache[key] = item
                self.stats.total_size += size_bytes
                
                # LRU 업데이트
                self.cache.move_to_end(key)
                
                # 크기 제한 확인
                self._evict_if_needed()
                
                return True
                
            except Exception as e:
                logger.error(f"캐시 저장 실패: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """캐시에서 값 삭제"""
        with self.lock:
            if key in self.cache:
                item = self.cache[key]
                self.stats.total_size -= item.size_bytes
                del self.cache[key]
                return True
            return False
    
    def clear(self):
        """캐시 전체 삭제"""
        with self.lock:
            self.cache.clear()
            self.stats.total_size = 0
    
    def _evict_if_needed(self):
        """필요시 캐시 아이템 제거"""
        # 크기 제한 확인
        while (len(self.cache) > self.max_size or 
               self.stats.total_size > self.max_memory_bytes):
            if not self.cache:
                break
            
            # LRU 아이템 제거
            key, item = self.cache.popitem(last=False)
            self.stats.total_size -= item.size_bytes
            self.stats.evictions += 1
            
            logger.debug(f"캐시 아이템 제거: {key}")
    
    def _calculate_size(self, value: Any) -> int:
        """값의 크기 계산"""
        try:
            if isinstance(value, (str, int, float, bool)):
                return len(str(value).encode('utf-8'))
            else:
                return len(pickle.dumps(value))
        except Exception:
            return 1024  # 기본값
    
    def get_stats(self) -> CacheStats:
        """캐시 통계 반환"""
        with self.lock:
            total_requests = self.stats.hits + self.stats.misses
            self.stats.hit_rate = self.stats.hits / total_requests if total_requests > 0 else 0
            return self.stats

class DiskCache:
    """디스크 캐시"""
    
    def __init__(self, cache_dir: str = "cache", max_size_mb: int = 500):
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.stats = CacheStats()
        self.lock = threading.RLock()
        
        # 캐시 디렉토리 생성
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"디스크 캐시 초기화: {cache_dir}, 최대 {max_size_mb}MB")
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        with self.lock:
            try:
                cache_file = self.cache_dir / f"{self._hash_key(key)}.cache"
                
                if not cache_file.exists():
                    self.stats.misses += 1
                    return None
                
                # 메타데이터 읽기
                meta_file = cache_file.with_suffix('.meta')
                if not meta_file.exists():
                    self.stats.misses += 1
                    return None
                
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                
                # 만료 확인
                if metadata.get('expires_at') and time.time() > metadata['expires_at']:
                    self.delete(key)
                    self.stats.misses += 1
                    return None
                
                # 값 읽기
                with open(cache_file, 'rb') as f:
                    value = pickle.load(f)
                
                # 접근 시간 업데이트
                metadata['last_accessed'] = time.time()
                metadata['access_count'] = metadata.get('access_count', 0) + 1
                
                with open(meta_file, 'w') as f:
                    json.dump(metadata, f)
                
                self.stats.hits += 1
                return value
                
            except Exception as e:
                logger.error(f"디스크 캐시 읽기 실패: {e}")
                self.stats.misses += 1
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """캐시에 값 저장"""
        with self.lock:
            try:
                cache_file = self.cache_dir / f"{self._hash_key(key)}.cache"
                meta_file = cache_file.with_suffix('.meta')
                
                # 값 저장
                with open(cache_file, 'wb') as f:
                    pickle.dump(value, f)
                
                # 메타데이터 저장
                metadata = {
                    'key': key,
                    'created_at': time.time(),
                    'last_accessed': time.time(),
                    'access_count': 0,
                    'size_bytes': cache_file.stat().st_size
                }
                
                if ttl:
                    metadata['expires_at'] = time.time() + ttl
                
                with open(meta_file, 'w') as f:
                    json.dump(metadata, f)
                
                # 크기 제한 확인
                self._evict_if_needed()
                
                return True
                
            except Exception as e:
                logger.error(f"디스크 캐시 저장 실패: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """캐시에서 값 삭제"""
        with self.lock:
            try:
                cache_file = self.cache_dir / f"{self._hash_key(key)}.cache"
                meta_file = cache_file.with_suffix('.meta')
                
                if cache_file.exists():
                    cache_file.unlink()
                if meta_file.exists():
                    meta_file.unlink()
                
                return True
                
            except Exception as e:
                logger.error(f"디스크 캐시 삭제 실패: {e}")
                return False
    
    def clear(self):
        """캐시 전체 삭제"""
        with self.lock:
            try:
                for file in self.cache_dir.glob("*.cache"):
                    file.unlink()
                for file in self.cache_dir.glob("*.meta"):
                    file.unlink()
            except Exception as e:
                logger.error(f"디스크 캐시 전체 삭제 실패: {e}")
    
    def _hash_key(self, key: str) -> str:
        """키 해시화"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def _evict_if_needed(self):
        """필요시 캐시 아이템 제거"""
        try:
            # 캐시 파일들 수집
            cache_files = []
            for meta_file in self.cache_dir.glob("*.meta"):
                try:
                    with open(meta_file, 'r') as f:
                        metadata = json.load(f)
                    
                    cache_file = meta_file.with_suffix('.cache')
                    if cache_file.exists():
                        cache_files.append((meta_file, cache_file, metadata))
                except Exception:
                    continue
            
            # 크기 계산
            total_size = sum(metadata.get('size_bytes', 0) for _, _, metadata in cache_files)
            
            # 크기 제한 확인
            if total_size > self.max_size_bytes:
                # 접근 시간 기준으로 정렬
                cache_files.sort(key=lambda x: x[2].get('last_accessed', 0))
                
                # 오래된 파일부터 제거
                for meta_file, cache_file, metadata in cache_files:
                    if total_size <= self.max_size_bytes:
                        break
                    
                    try:
                        cache_file.unlink()
                        meta_file.unlink()
                        total_size -= metadata.get('size_bytes', 0)
                        self.stats.evictions += 1
                    except Exception:
                        continue
                        
        except Exception as e:
            logger.error(f"디스크 캐시 제거 실패: {e}")
    
    def get_stats(self) -> CacheStats:
        """캐시 통계 반환"""
        with self.lock:
            total_requests = self.stats.hits + self.stats.misses
            self.stats.hit_rate = self.stats.hits / total_requests if total_requests > 0 else 0
            return self.stats

class MultiLevelCache:
    """다층 캐시 시스템"""
    
    def __init__(self, 
                 memory_cache_size: int = 1000,
                 memory_cache_mb: int = 100,
                 disk_cache_dir: str = "cache",
                 disk_cache_mb: int = 500):
        
        self.memory_cache = MemoryCache(memory_cache_size, memory_cache_mb)
        self.disk_cache = DiskCache(disk_cache_dir, disk_cache_mb)
        
        logger.info("다층 캐시 시스템 초기화 완료")
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기 (메모리 → 디스크 순)"""
        # 메모리 캐시에서 먼저 확인
        value = self.memory_cache.get(key)
        if value is not None:
            return value
        
        # 디스크 캐시에서 확인
        value = self.disk_cache.get(key)
        if value is not None:
            # 메모리 캐시에 복사
            self.memory_cache.set(key, value)
            return value
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """캐시에 값 저장 (메모리 + 디스크)"""
        memory_success = self.memory_cache.set(key, value, ttl)
        disk_success = self.disk_cache.set(key, value, ttl)
        
        return memory_success or disk_success
    
    def delete(self, key: str) -> bool:
        """캐시에서 값 삭제"""
        memory_success = self.memory_cache.delete(key)
        disk_success = self.disk_cache.delete(key)
        
        return memory_success or disk_success
    
    def clear(self):
        """캐시 전체 삭제"""
        self.memory_cache.clear()
        self.disk_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        memory_stats = self.memory_cache.get_stats()
        disk_stats = self.disk_cache.get_stats()
        
        return {
            'memory': {
                'hits': memory_stats.hits,
                'misses': memory_stats.misses,
                'hit_rate': memory_stats.hit_rate,
                'evictions': memory_stats.evictions,
                'total_size': memory_stats.total_size
            },
            'disk': {
                'hits': disk_stats.hits,
                'misses': disk_stats.misses,
                'hit_rate': disk_stats.hit_rate,
                'evictions': disk_stats.evictions,
                'total_size': disk_stats.total_size
            },
            'combined': {
                'total_hits': memory_stats.hits + disk_stats.hits,
                'total_misses': memory_stats.misses + disk_stats.misses,
                'overall_hit_rate': (memory_stats.hits + disk_stats.hits) / 
                                  (memory_stats.hits + memory_stats.misses + disk_stats.hits + disk_stats.misses) 
                                  if (memory_stats.hits + memory_stats.misses + disk_stats.hits + disk_stats.misses) > 0 else 0
            }
        }

# 전역 캐시 인스턴스
_cache_instance = None

def get_cache() -> MultiLevelCache:
    """캐시 인스턴스 가져오기"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = MultiLevelCache()
    return _cache_instance

def cache_result(ttl: Optional[int] = None, key_prefix: str = ""):
    """결과 캐싱 데코레이터"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # 캐시 키 생성
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # 캐시에서 확인
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"캐시 히트: {cache_key}")
                return cached_result
            
            # 함수 실행
            result = func(*args, **kwargs)
            
            # 캐시에 저장
            cache.set(cache_key, result, ttl)
            logger.debug(f"캐시 저장: {cache_key}")
            
            return result
        
        return wrapper
    return decorator

def get_cache_stats() -> Dict[str, Any]:
    """캐시 통계 가져오기"""
    cache = get_cache()
    return cache.get_stats()







