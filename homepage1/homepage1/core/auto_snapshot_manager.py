import os
import shutil
import json
import hashlib
from datetime import datetime
from typing import List, Dict
import zipfile


class SnapshotManager:
    """RohaTax 스냅샷 백업/복원 관리자

    - 스냅샷 경로: snapshots/YYYY-MM-DD_HH-MM-SS_사유/
    - 포함 경로: database/*app.db*, templates_data/, user_data/, output/, config/*.json, file_manager_config.json
    - 메타데이터: snapshot.json (사유/작성시각/포함파일/해시/크기)
    - 보존: 외부 정책에서 관리 (기본 N개 유지)
    """

    def __init__(self, project_root: str) -> None:
        self.project_root = os.path.abspath(project_root)
        self.snapshots_dir = os.path.join(self.project_root, 'snapshots')
        os.makedirs(self.snapshots_dir, exist_ok=True)

    def _now_stamp(self) -> str:
        return datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    def _safe_rel(self, path: str) -> str:
        return os.path.relpath(path, self.project_root)

    def _iter_includes(self) -> List[str]:
        # 대상 경로 목록 (존재하는 것만 수집)
        candidates = [
            os.path.join(self.project_root, 'database', 'app.db'),
            os.path.join(self.project_root, 'database', 'app.db-wal'),
            os.path.join(self.project_root, 'database', 'app.db-shm'),
            os.path.join(self.project_root, 'templates_data'),
            os.path.join(self.project_root, 'user_data'),
            os.path.join(self.project_root, 'output'),
            os.path.join(self.project_root, 'config', 'absolute_guidelines_v5.json'),
            os.path.join(self.project_root, 'config', 'industry_config.json'),
            os.path.join(self.project_root, 'file_manager_config.json'),
        ]
        existing = []
        for c in candidates:
            if os.path.isfile(c) or os.path.isdir(c):
                existing.append(c)
        return existing

    def _hash_file(self, file_path: str) -> str:
        h = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                h.update(chunk)
        return h.hexdigest()

    def _collect_hashes(self, root_dir: str) -> Dict[str, str]:
        result: Dict[str, str] = {}
        for base, _, files in os.walk(root_dir):
            for name in files:
                full = os.path.join(base, name)
                rel = os.path.relpath(full, root_dir)
                result[rel] = self._hash_file(full)
        return result

    def create_snapshot(self, reason: str) -> str:
        """스냅샷 생성. 사유(reason)는 한글 가능.

        Returns: 스냅샷 디렉터리 경로
        """
        reason_sanitized = ''.join(ch for ch in reason.strip() if ch not in '\\/:*?"<>|').strip()
        if not reason_sanitized:
            reason_sanitized = '스냅샷'

        snap_name = f"{self._now_stamp()}_{reason_sanitized}"
        snap_dir = os.path.join(self.snapshots_dir, snap_name)
        os.makedirs(snap_dir, exist_ok=True)

        includes = self._iter_includes()
        copied: List[str] = []

        for src in includes:
            rel = self._safe_rel(src)
            dst = os.path.join(snap_dir, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            copied.append(rel)

        # zip 생성
        zip_path = os.path.join(self.snapshots_dir, f"{snap_name}.zip")
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for base, _, files in os.walk(snap_dir):
                for name in files:
                    full = os.path.join(base, name)
                    arc = os.path.relpath(full, snap_dir)
                    zf.write(full, arc)

        # 해시 수집
        hashes = self._collect_hashes(snap_dir)

        meta = {
            'name': snap_name,
            'created_at': datetime.now().isoformat(),
            'reason': reason,
            'project_root': self.project_root,
            'included': copied,
            'zip': os.path.relpath(zip_path, self.project_root),
            'hashes': hashes,
        }
        with open(os.path.join(snap_dir, 'snapshot.json'), 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # checksums.txt (zip 해시)
        with open(os.path.join(snap_dir, 'checksums.txt'), 'w', encoding='utf-8') as f:
            f.write(f"zip_sha256 {self._hash_file(zip_path)}\n")

        return snap_dir

    def restore_snapshot(self, snapshot_dir: str) -> None:
        """스냅샷 복원: 현재 대상 파일은 restore_backup/에 안전 보관 후 스냅샷 파일로 교체"""
        snap_abs = os.path.abspath(snapshot_dir)
        if not os.path.isdir(snap_abs):
            raise FileNotFoundError(f"스냅샷 폴더를 찾을 수 없습니다: {snapshot_dir}")

        # 안전 보관 디렉터리
        safe_dir = os.path.join(self.project_root, 'restore_backup', self._now_stamp())
        os.makedirs(safe_dir, exist_ok=True)

        # 포함 목록 기준 교체
        for src_base, _, files in os.walk(snap_abs):
            for name in files:
                full_src = os.path.join(src_base, name)
                rel = os.path.relpath(full_src, snap_abs)
                dst = os.path.join(self.project_root, rel)
                # 기존 파일/폴더 안전 보관
                if os.path.exists(dst):
                    os.makedirs(os.path.dirname(os.path.join(safe_dir, rel)), exist_ok=True)
                    shutil.move(dst, os.path.join(safe_dir, rel))
                # 부모 생성 후 복원
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(full_src, dst)



