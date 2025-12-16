"""
시스템 관리자 모듈
- 파일 모니터링
- 성능 최적화
- 에러 추적
- 자동 정리
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class SystemMetrics:
    """시스템 메트릭"""
    timestamp: str
    total_files: int
    python_files: int
    large_files: int
    conversion_success_rate: float
    avg_response_time: float
    memory_usage: float

class SystemManager:
    """시스템 관리자"""
    
    def __init__(self, db_path: str = "system_metrics.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.check_database()
    
    def check_database(self):
        """데이터베이스 체크 및 초기화"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 메트릭 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                total_files INTEGER,
                python_files INTEGER,
                large_files INTEGER,
                conversion_success_rate REAL,
                avg_response_time REAL,
                memory_usage REAL
            )
        ''')
        
        # 에러 로그 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                error_type TEXT,
                error_message TEXT,
                file_path TEXT,
                line_number INTEGER,
                severity TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def scan_file_system(self) -> Dict[str, Any]:
        """파일 시스템 스캔"""
        stats = {
            'total_files': 0,
            'python_files': 0,
            'large_files': 0,
            'file_sizes': [],
            'large_file_details': []
        }
        
        # 100KB 이상 파일 체크
        threshold = 100 * 1024  # 100KB
        
        for root, dirs, files in os.walk("."):
            # 숨김 디렉토리 제외
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'node_modules', '__pycache__']]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    stats['total_files'] += 1
                    stats['file_sizes'].append(file_size)
                    
                    if file.endswith('.py'):
                        stats['python_files'] += 1
                    
                    if file_size > threshold:
                        stats['large_files'] += 1
                        stats['large_file_details'].append({
                            'path': file_path,
                            'size': file_size,
                            'size_kb': round(file_size / 1024, 1)
                        })
        
        # 큰 파일들 정렬 (크기순)
        stats['large_file_details'].sort(key=lambda x: x['size'], reverse=True)
        
        return stats
    
    def log_metrics(self, metrics: SystemMetrics):
        """메트릭을 데이터베이스에 저장"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO system_metrics 
            (timestamp, total_files, python_files, large_files, conversion_success_rate, avg_response_time, memory_usage)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.timestamp,
            metrics.total_files,
            metrics.python_files,
            metrics.large_files,
            metrics.conversion_success_rate,
            metrics.avg_response_time,
            metrics.memory_usage
        ))
        
        conn.commit()
        conn.close()
    
    def get_recent_metrics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 메트릭 조회"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM system_metrics 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        metrics = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return metrics
    
    def analyze_performance_trends(self) -> Dict[str, Any]:
        """성능 트렌드 분석"""
        metrics = self.get_recent_metrics(20)  # 최근 20개 메트릭
        
        if len(metrics) < 2:
            return {'status': 'insufficient_data', 'message': '분석을 위한 충분한 데이터가 없습니다.'}
        
        # 트렌드 계산
        total_files_trend = self._calculate_trend([d['total_files'] for d in metrics])
        success_rate_trend = self._calculate_trend([d['conversion_success_rate'] for d in metrics])
        response_time_trend = self._calculate_trend([d['avg_response_time'] for d in metrics])
        
        # 가장 큰 파일들 식별
        file_stats = self.scan_file_system()
        
        return {
            'status': 'success',
            'trends': {
                'total_files': total_files_trend,
                'success_rate': success_rate_trend,
                'response_time': response_time_trend
            },
            'current_state': {
                'total_files': file_stats['total_files'],
                'python_files': file_stats['python_files'],
                'large_files': file_stats['large_files'],
                'top_large_files': file_stats['large_file_details'][:5]
            },
            'recommendations': self._generate_recommendations(metrics[-1] if metrics else {}, file_stats)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """트렌드 계산 (향상/하락/안정)"""
        if len(values) < 2:
            return "안정"
        
        # 선형 회귀로 트렌드 확인
        recent_avg = sum(values[:len(values)//2]) / (len(values)//2)
        older_avg = sum(values[len(values)//2:]) / (len(values)//2)
        
        diff_pct = (recent_avg - older_avg) / older_avg * 100
        
        if abs(diff_pct) < 5:
            return "안정"
        elif diff_pct > 0:
            return f"상승 ({diff_pct:.1f}%)"
        else:
            return f"하락 ({abs(diff_pct):.1f}%)"
    
    def _generate_recommendations(self, latest_metrics: Dict[str, Any], file_stats: Dict[str, Any]) -> List[str]:
        """개선 권장사항 생성"""
        recommendations = []
        
        # 파일 수 관련
        if file_stats['large_files'] > 10:
            recommendations.append(f"대용량 파일이 {file_stats['large_files']}개 많습니다. 리팩토링을 고려하세요.")
        
        # 성능 관련
        if latest_metrics['conversion_success_rate'] < 0.8:
            recommendations.append("변환 성공률이 낮습니다. 에러 로그를 확인하세요.")
        
        if latest_metrics['avg_response_time'] > 5.0:
            recommendations.append("응답 시간이 느립니다. 성능 최적화가 필요합니다.")
        
        # 파일 구조 관련
        if file_stats['python_files'] > 50:
            recommendations.append("Python 파일이 많습니다. 모듈화를 고려하세요.")
        
        return recommendations
    
    def generate_report(self) -> str:
        """시스템 리포트 생성"""
        analysis = self.analyze_performance_trends()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 충분한 데이터가 없는 경우 간단한 리포트 생성
        if analysis['status'] == 'insufficient_data':
            file_stats = self.scan_file_system()
            return f"""
🏢 시스템 관리 리포트 - {timestamp}
============================================================

⚠️ 데이터 부족 (새로운 시스템 모니터링 시작)

📊 현재 상태:
  📁 총 파일: {file_stats['total_files']:,}개
  🐍 Python 파일: {file_stats['python_files']:,}개  
  🚨 대용량 파일: {file_stats['large_files']:,}개

📄 상위 대용량 파일:
"""
        
        report = f"""
🏢 시스템 관리 리포트 - {timestamp}
============================================================

📊 현재 상태:
  📁 총 파일: {analysis['current_state']['total_files']:,}개
  🐍 Python 파일: {analysis['current_state']['python_files']:,}개  
  🚨 대용량 파일: {analysis['current_state']['large_files']:,}개

📈 트렌드 분석:
  📁 파일 수: {analysis['trends']['total_files']}
  ✅ 성공률: {analysis['trends']['success_rate']}
  ⏱️ 응답시간: {analysis['trends']['response_time']}

🔧 개선 권장사항:
"""
        
        for rec in analysis['recommendations']:
            report += f"  💡 {rec}\n"
        
        # 상위 대용량 파일 목록
        report += "\n📄 상위 대용량 파일 (처리 권장):\n"
        for file_info in analysis['current_state']['top_large_files'][:5]:
            report += f"  📄 {file_info['size_kb']:8.1f}KB - {file_info['path']}\n"
        
        return report

# 전역 시스템 관리자 인스턴스
system_manager = SystemManager()
