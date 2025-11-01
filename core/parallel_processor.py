"""
파일 처리 병렬화 모듈
Python 3.14의 Free-Threaded Python을 활용한 고성능 파일 처리
"""

import os
import time
import threading
from typing import Dict, List, Any, Optional, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from pathlib import Path
import logging
import queue
import multiprocessing as mp
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ProcessingMode(Enum):
    """처리 모드"""
    THREAD = "thread"
    PROCESS = "process"
    HYBRID = "hybrid"

@dataclass
class ProcessingResult:
    """처리 결과"""
    file_path: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    worker_id: Optional[str] = None

@dataclass
class ProcessingStats:
    """처리 통계"""
    total_files: int = 0
    processed_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    total_time: float = 0.0
    average_time: float = 0.0
    throughput: float = 0.0  # 파일/초

class ParallelFileProcessor:
    """Python 3.14 Free-Threaded Python을 활용한 병렬 파일 처리기"""
    
    def __init__(self, 
                 max_workers: int = None,
                 processing_mode: ProcessingMode = ProcessingMode.THREAD,
                 chunk_size: int = 100):
        """
        병렬 파일 처리기 초기화
        
        Args:
            max_workers: 최대 워커 수 (None이면 CPU 코어 수)
            processing_mode: 처리 모드 (THREAD, PROCESS, HYBRID)
            chunk_size: 청크 크기
        """
        self.max_workers = max_workers or mp.cpu_count()
        self.processing_mode = processing_mode
        self.chunk_size = chunk_size
        
        # Python 3.14 Free-Threaded Python 활용
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=self.max_workers)
        
        # 처리 통계
        self.stats = ProcessingStats()
        self.results_queue = queue.Queue()
        
        # 워커 ID 생성
        self.worker_counter = 0
        self.worker_lock = threading.Lock()
        
        logger.info(f"병렬 파일 처리기 초기화 완료: {self.max_workers} 워커, {self.processing_mode.value} 모드")
    
    def _get_worker_id(self) -> str:
        """워커 ID 생성"""
        with self.worker_lock:
            self.worker_counter += 1
            return f"worker_{self.worker_counter}"
    
    def process_single_file(self, 
                           file_path: str, 
                           processor_func: Callable,
                           *args, **kwargs) -> ProcessingResult:
        """단일 파일 처리"""
        start_time = time.time()
        worker_id = self._get_worker_id()
        
        try:
            logger.debug(f"[{worker_id}] 파일 처리 시작: {file_path}")
            
            # 파일 처리 실행
            result_data = processor_func(file_path, *args, **kwargs)
            
            processing_time = time.time() - start_time
            
            logger.debug(f"[{worker_id}] 파일 처리 완료: {file_path} ({processing_time:.2f}초)")
            
            return ProcessingResult(
                file_path=file_path,
                success=True,
                data=result_data,
                processing_time=processing_time,
                worker_id=worker_id
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            logger.error(f"[{worker_id}] 파일 처리 실패: {file_path} - {error_msg}")
            
            return ProcessingResult(
                file_path=file_path,
                success=False,
                error=error_msg,
                processing_time=processing_time,
                worker_id=worker_id
            )
    
    def process_files_parallel(self, 
                              file_paths: List[str],
                              processor_func: Callable,
                              *args, **kwargs) -> List[ProcessingResult]:
        """파일들을 병렬로 처리"""
        if not file_paths:
            return []
        
        logger.info(f"병렬 파일 처리 시작: {len(file_paths)}개 파일")
        start_time = time.time()
        
        # 통계 초기화
        self.stats = ProcessingStats(total_files=len(file_paths))
        
        results = []
        
        if self.processing_mode == ProcessingMode.THREAD:
            results = self._process_with_threads(file_paths, processor_func, *args, **kwargs)
        elif self.processing_mode == ProcessingMode.PROCESS:
            results = self._process_with_processes(file_paths, processor_func, *args, **kwargs)
        elif self.processing_mode == ProcessingMode.HYBRID:
            results = self._process_with_hybrid(file_paths, processor_func, *args, **kwargs)
        
        # 통계 업데이트
        self.stats.total_time = time.time() - start_time
        self.stats.processed_files = len(results)
        self.stats.successful_files = sum(1 for r in results if r.success)
        self.stats.failed_files = sum(1 for r in results if not r.success)
        self.stats.average_time = self.stats.total_time / len(results) if results else 0
        self.stats.throughput = len(results) / self.stats.total_time if self.stats.total_time > 0 else 0
        
        logger.info(f"병렬 파일 처리 완료: {self.stats.successful_files}/{self.stats.total_files} 성공 "
                   f"({self.stats.total_time:.2f}초, {self.stats.throughput:.2f} 파일/초)")
        
        return results
    
    def _process_with_threads(self, 
                             file_paths: List[str],
                             processor_func: Callable,
                             *args, **kwargs) -> List[ProcessingResult]:
        """ThreadPoolExecutor를 사용한 병렬 처리"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 작업 제출
            future_to_path = {
                executor.submit(self.process_single_file, path, processor_func, *args, **kwargs): path
                for path in file_paths
            }
            
            # 결과 수집
            for future in as_completed(future_to_path):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"스레드 처리 오류: {e}")
                    results.append(ProcessingResult(
                        file_path=future_to_path[future],
                        success=False,
                        error=str(e)
                    ))
        
        return results
    
    def _process_with_processes(self, 
                               file_paths: List[str],
                               processor_func: Callable,
                               *args, **kwargs) -> List[ProcessingResult]:
        """ProcessPoolExecutor를 사용한 병렬 처리"""
        results = []
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # 작업 제출
            future_to_path = {
                executor.submit(self.process_single_file, path, processor_func, *args, **kwargs): path
                for path in file_paths
            }
            
            # 결과 수집
            for future in as_completed(future_to_path):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"프로세스 처리 오류: {e}")
                    results.append(ProcessingResult(
                        file_path=future_to_path[future],
                        success=False,
                        error=str(e)
                    ))
        
        return results
    
    def _process_with_hybrid(self, 
                            file_paths: List[str],
                            processor_func: Callable,
                            *args, **kwargs) -> List[ProcessingResult]:
        """하이브리드 모드: 큰 파일은 프로세스, 작은 파일은 스레드"""
        results = []
        
        # 파일 크기별로 분류
        large_files = []
        small_files = []
        
        for file_path in file_paths:
            try:
                file_size = os.path.getsize(file_path)
                if file_size > 10 * 1024 * 1024:  # 10MB 이상
                    large_files.append(file_path)
                else:
                    small_files.append(file_path)
            except OSError:
                small_files.append(file_path)  # 크기 확인 실패 시 작은 파일로 분류
        
        logger.info(f"하이브리드 처리: 큰 파일 {len(large_files)}개, 작은 파일 {len(small_files)}개")
        
        # 큰 파일은 프로세스로 처리
        if large_files:
            process_results = self._process_with_processes(large_files, processor_func, *args, **kwargs)
            results.extend(process_results)
        
        # 작은 파일은 스레드로 처리
        if small_files:
            thread_results = self._process_with_threads(small_files, processor_func, *args, **kwargs)
            results.extend(thread_results)
        
        return results
    
    def process_files_in_chunks(self, 
                               file_paths: List[str],
                               processor_func: Callable,
                               *args, **kwargs) -> List[ProcessingResult]:
        """청크 단위로 파일 처리"""
        if not file_paths:
            return []
        
        logger.info(f"청크 단위 파일 처리 시작: {len(file_paths)}개 파일, 청크 크기: {self.chunk_size}")
        
        all_results = []
        
        # 파일을 청크로 분할
        for i in range(0, len(file_paths), self.chunk_size):
            chunk = file_paths[i:i + self.chunk_size]
            logger.info(f"청크 {i//self.chunk_size + 1} 처리 중: {len(chunk)}개 파일")
            
            # 청크 처리
            chunk_results = self.process_files_parallel(chunk, processor_func, *args, **kwargs)
            all_results.extend(chunk_results)
            
            # 청크 간 잠시 대기 (시스템 부하 방지)
            time.sleep(0.1)
        
        logger.info(f"청크 단위 파일 처리 완료: {len(all_results)}개 결과")
        return all_results
    
    def get_processing_stats(self) -> ProcessingStats:
        """처리 통계 반환"""
        return self.stats
    
    def get_performance_report(self) -> Dict[str, Any]:
        """성능 리포트 생성"""
        return {
            'total_files': self.stats.total_files,
            'processed_files': self.stats.processed_files,
            'successful_files': self.stats.successful_files,
            'failed_files': self.stats.failed_files,
            'success_rate': self.stats.successful_files / self.stats.total_files if self.stats.total_files > 0 else 0,
            'total_time': self.stats.total_time,
            'average_time': self.stats.average_time,
            'throughput': self.stats.throughput,
            'processing_mode': self.processing_mode.value,
            'max_workers': self.max_workers,
            'chunk_size': self.chunk_size
        }
    
    def close(self):
        """리소스 정리"""
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)
        logger.info("병렬 파일 처리기 종료")

# 전역 처리기 인스턴스
_parallel_processor = None

def get_parallel_processor() -> ParallelFileProcessor:
    """병렬 파일 처리기 인스턴스 가져오기"""
    global _parallel_processor
    if _parallel_processor is None:
        _parallel_processor = ParallelFileProcessor()
    return _parallel_processor

def process_files_parallel(file_paths: List[str], 
                          processor_func: Callable,
                          *args, **kwargs) -> List[ProcessingResult]:
    """파일들을 병렬로 처리하는 편의 함수"""
    processor = get_parallel_processor()
    return processor.process_files_parallel(file_paths, processor_func, *args, **kwargs)

def get_processing_performance_report() -> Dict[str, Any]:
    """처리 성능 리포트 가져오기"""
    processor = get_parallel_processor()
    return processor.get_performance_report()







