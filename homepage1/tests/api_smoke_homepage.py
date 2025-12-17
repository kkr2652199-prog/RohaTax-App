#!/usr/bin/env python3
"""
로하 홈페이지 API 스모크 테스트 스크립트
Python 3.13+ 호환 버전

이 스크립트는 유튜브 데모 컴포넌트 통합 후
전체 페이지의 API 호출에 문제가 없는지 자동으로 테스트합니다.
"""

import asyncio
import aiohttp
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse


@dataclass
class TestResult:
    """테스트 결과 데이터 클래스"""
    url: str
    method: str
    status_code: int
    response_time: float
    success: bool
    error_message: Optional[str] = None
    content_type: Optional[str] = None


class RohaAPISmokeTester:
    """로하 API 스모크 테스터"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        self.results: List[TestResult] = []
        
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
    
    def get_test_endpoints(self) -> List[Tuple[str, str, Dict]]:
        """테스트할 엔드포인트 목록 반환"""
        return [
            # 홈페이지 관련
            ("GET", "/", {}),
            ("GET", "/static/css/homepage.css", {}),
            ("GET", "/static/css/components/youtube_demo.css", {}),
            ("GET", "/static/js/homepage.js", {}),
            
            # 변환 관련 (새로 추가된 CTA 버튼 경로)
            ("GET", "/conversion/start", {}),
            ("GET", "/conversion", {}),
            
            # API 엔드포인트
            ("GET", "/api/health", {}),
            ("GET", "/api/user/profile", {}),
            ("POST", "/api/conversion/validate", {"test": "data"}),
            
            # 관리자 관련
            ("GET", "/admin", {}),
            ("GET", "/admin/users", {}),
        ]
    
    async def test_endpoint(self, method: str, path: str, data: Dict = None) -> TestResult:
        """단일 엔드포인트 테스트"""
        url = urljoin(self.base_url, path)
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                async with self.session.get(url) as response:
                    response_time = time.time() - start_time
                    content_type = response.headers.get('content-type', '')
                    
                    return TestResult(
                        url=url,
                        method=method,
                        status_code=response.status,
                        response_time=response_time,
                        success=200 <= response.status < 400,
                        content_type=content_type
                    )
                    
            elif method.upper() == "POST":
                json_data = json.dumps(data) if data else None
                async with self.session.post(url, data=json_data, 
                                           headers={'Content-Type': 'application/json'}) as response:
                    response_time = time.time() - start_time
                    content_type = response.headers.get('content-type', '')
                    
                    return TestResult(
                        url=url,
                        method=method,
                        status_code=response.status,
                        response_time=response_time,
                        success=200 <= response.status < 400,
                        content_type=content_type
                    )
                    
        except asyncio.TimeoutError:
            return TestResult(
                url=url,
                method=method,
                status_code=0,
                response_time=time.time() - start_time,
                success=False,
                error_message="Request timeout"
            )
        except Exception as e:
            return TestResult(
                url=url,
                method=method,
                status_code=0,
                response_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
    
    async def run_all_tests(self) -> List[TestResult]:
        """모든 테스트 실행"""
        print("🚀 로하 API 스모크 테스트 시작...")
        print(f"📍 테스트 대상: {self.base_url}")
        print("-" * 60)
        
        endpoints = self.get_test_endpoints()
        tasks = []
        
        for method, path, data in endpoints:
            task = self.test_endpoint(method, path, data)
            tasks.append(task)
        
        # 모든 테스트를 병렬로 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 처리
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                method, path, _ = endpoints[i]
                processed_results.append(TestResult(
                    url=urljoin(self.base_url, path),
                    method=method,
                    status_code=0,
                    response_time=0,
                    success=False,
                    error_message=f"Test execution error: {str(result)}"
                ))
            else:
                processed_results.append(result)
        
        self.results = processed_results
        return processed_results
    
    def print_results(self):
        """테스트 결과 출력"""
        if not self.results:
            print("❌ 테스트 결과가 없습니다.")
            return
        
        success_count = sum(1 for r in self.results if r.success)
        total_count = len(self.results)
        
        print(f"\n📊 테스트 결과 요약: {success_count}/{total_count} 성공")
        print("=" * 60)
        
        for result in self.results:
            status_icon = "✅" if result.success else "❌"
            print(f"{status_icon} {result.method} {result.url}")
            print(f"   상태: {result.status_code} | 응답시간: {result.response_time:.3f}s")
            if result.content_type:
                print(f"   Content-Type: {result.content_type}")
            if result.error_message:
                print(f"   오류: {result.error_message}")
            print()
    
    def generate_report(self) -> Dict:
        """테스트 리포트 생성"""
        if not self.results:
            return {"error": "테스트 결과가 없습니다."}
        
        success_count = sum(1 for r in self.results if r.success)
        total_count = len(self.results)
        avg_response_time = sum(r.response_time for r in self.results) / total_count
        
        failed_tests = [r for r in self.results if not r.success]
        
        return {
            "summary": {
                "total_tests": total_count,
                "successful_tests": success_count,
                "failed_tests": len(failed_tests),
                "success_rate": f"{(success_count/total_count)*100:.1f}%",
                "average_response_time": f"{avg_response_time:.3f}s"
            },
            "failed_endpoints": [
                {
                    "url": r.url,
                    "method": r.method,
                    "status_code": r.status_code,
                    "error": r.error_message
                }
                for r in failed_tests
            ],
            "all_results": [
                {
                    "url": r.url,
                    "method": r.method,
                    "status_code": r.status_code,
                    "response_time": r.response_time,
                    "success": r.success,
                    "error_message": r.error_message
                }
                for r in self.results
            ]
        }


async def main():
    """메인 실행 함수"""
    # 명령행 인수 처리
    base_url = "http://localhost:5000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print("🔧 로하 홈페이지 API 스모크 테스트")
    print(f"🎯 Python 버전: {sys.version}")
    print(f"🌐 테스트 서버: {base_url}")
    print()
    
    try:
        async with RohaAPISmokeTester(base_url) as tester:
            # 테스트 실행
            await tester.run_all_tests()
            
            # 결과 출력
            tester.print_results()
            
            # 리포트 생성 및 저장
            report = tester.generate_report()
            
            # JSON 리포트 저장
            report_file = Path("test_results") / f"api_smoke_test_{int(time.time())}.json"
            report_file.parent.mkdir(exist_ok=True)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"📄 상세 리포트 저장: {report_file}")
            
            # 종료 코드 결정
            if report["summary"]["failed_tests"] > 0:
                print(f"\n⚠️  {report['summary']['failed_tests']}개의 테스트가 실패했습니다.")
                sys.exit(1)
            else:
                print(f"\n🎉 모든 테스트가 성공했습니다!")
                sys.exit(0)
                
    except KeyboardInterrupt:
        print("\n⏹️  사용자에 의해 테스트가 중단되었습니다.")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 테스트 실행 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Python 3.13+ 호환성 확인
    if sys.version_info < (3, 13):
        print("❌ 이 스크립트는 Python 3.13 이상이 필요합니다.")
        print(f"현재 버전: {sys.version}")
        sys.exit(1)
    
    # 비동기 메인 함수 실행
    asyncio.run(main())
