import sqlite3
from pathlib import Path
from datetime import datetime
import shutil

db_path = Path('homepage1/database/app.db')
backup_dir = Path('homepage1/database/backups')
backup_dir.mkdir(parents=True, exist_ok=True)
backup_path = backup_dir / f'app_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'

print(f'백업 중: {backup_path.name}')
shutil.copy2(db_path, backup_path)
print('백업 완료')

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

tables = ['activity_logs', 'token_history', 'conversion_logs', 'usage_logs', 'validation_logs', 'payment_history']

print('\n삭제 전 레코드 수:')
total = 0
for t in tables:
    try:
        cursor.execute(f'SELECT COUNT(*) FROM {t}')
        count = cursor.fetchone()[0]
        print(f'  {t}: {count:,}건')
        total += count
    except:
        print(f'  {t}: 테이블 없음')

print(f'\n총 {total:,}건 삭제 중...\n')

for t in tables:
    try:
        cursor.execute(f'DELETE FROM {t}')
        print(f'  {t}: {cursor.rowcount:,}건 삭제 완료')
    except Exception as e:
        print(f'  {t}: 오류 - {str(e)}')

print('\n데이터베이스 최적화 중...')
conn.execute('VACUUM')

conn.commit()
conn.close()

print('\n통합 관제실 로그 초기화 완료!')
print(f'백업 파일: {backup_path}')


