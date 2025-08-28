#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TTUGTTAG Streamlit 앱 실행 스크립트
"""

import os
import sys
import subprocess
import webbrowser
import time

def check_dependencies():
    """의존성 패키지 확인"""
    print("🔍 의존성 패키지 확인 중...")
    
    required_packages = [
        'streamlit',
        'langgraph', 
        'chromadb',
        'requests',
        'numpy',
        'tqdm'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (설치 필요)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 설치 필요한 패키지: {', '.join(missing_packages)}")
        install = input("자동으로 설치하시겠습니까? (y/N): ")
        
        if install.lower() in ['y', 'yes']:
            print("📦 패키지 설치 중...")
            for package in missing_packages:
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                    print(f"   ✅ {package} 설치 완료")
                except subprocess.CalledProcessError:
                    print(f"   ❌ {package} 설치 실패")
                    return False
        else:
            print("❌ 필요한 패키지가 설치되지 않았습니다.")
            return False
    
    return True

def check_database():
    """데이터베이스 확인"""
    print("\n🗄️ 데이터베이스 확인 중...")
    
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'cafe_vector_db')
    
    if os.path.exists(db_path):
        print(f"   ✅ 데이터베이스 발견: {db_path}")
        return True
    else:
        print(f"   ⚠️ 데이터베이스가 없습니다: {db_path}")
        print("   💡 데이터베이스를 먼저 구축해주세요:")
        print("      cd tools")
        print("      python build_database.py")
        return False

def run_streamlit():
    """Streamlit 앱 실행"""
    print("\n🚀 Streamlit 앱 실행 중...")
    
    # 현재 디렉토리를 web 폴더로 변경
    web_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(web_dir)
    
    # Streamlit 앱 파일 경로
    app_file = os.path.join(web_dir, 'streamlit_app.py')
    
    if not os.path.exists(app_file):
        print(f"❌ Streamlit 앱 파일을 찾을 수 없습니다: {app_file}")
        return False
    
    print(f"   📁 앱 파일: {app_file}")
    print("   🌐 브라우저에서 http://localhost:8501 을 열어주세요")
    print("   ⏹️ 종료하려면 Ctrl+C를 누르세요")
    
    try:
        # Streamlit 실행
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 'streamlit_app.py',
            '--server.port', '8501',
            '--server.address', 'localhost'
        ])
    except KeyboardInterrupt:
        print("\n👋 앱이 종료되었습니다.")
    except Exception as e:
        print(f"❌ 앱 실행 중 오류 발생: {e}")
        return False
    
    return True

def main():
    """메인 실행 함수"""
    print("🎯 TTUGTTAG Streamlit 앱 실행기")
    print("=" * 50)
    
    # 1. 의존성 확인
    if not check_dependencies():
        print("\n❌ 의존성 확인 실패")
        return
    
    # 2. 데이터베이스 확인
    if not check_database():
        print("\n⚠️ 데이터베이스가 없습니다. 계속 진행하시겠습니까? (y/N): ")
        continue_anyway = input()
        if continue_anyway.lower() not in ['y', 'yes']:
            return
    
    # 3. Streamlit 앱 실행
    print("\n🎉 모든 준비가 완료되었습니다!")
    run_streamlit()

if __name__ == "__main__":
    main() 