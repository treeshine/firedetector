import google.generativeai as genai
import os
from dotenv import load_dotenv
import PIL.Image

# .env 파일 로드
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# 모델 초기화 (모듈 로드 시 한 번만 실행)
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    # 속도와 비용 효율적인 flash-lite 모델 사용 권장
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    model = None
    print("Warning: GOOGLE_API_KEY not found in .env file.")

def analyze_frame_with_gemini(pil_image):
    """
    PIL 이미지 객체를 받아 Gemini로 분석하고 결과를 문자열로 반환합니다.
    """
    if not model:
        return "Error: API Key is missing. Please check .env file."
    
    try:
        print("Gemini에게 분석 요청 중...")
        prompt = """
        가정집 환경의 CCTV 이미지다. 화재 위험을 분석해라.
        화재 단계를 [경고, 위험, 대피] 중 하나로 판단하고, 발화 위치와 화재 원점으로 보이는 물체, 불길 강도를 포함하여 전체 답변을 100자 이내로 핵심만 요약해라.
        화재의 단계는 다음 기준을 따른다:
        - 관심 : 가스레인지에 불이 켜져있는 경우, 요리 중 발생하는 불꽃이나 연기로 판단되는 경우.
        - 경고: 연기나 작은 불꽃이 보이는 초기 단계
        - 위험: 불길이 확산되고 주변 물체에 영향을 미치는 중간 단계
        - 대피: 큰 불길과 심각한 피해가 발생하는 단계
        이미지에서 화재가 감지되지 않으면 '화재 없음'이라고만 답해라.
        답변은 한국어로 작성해라.

        """
        
        # 이미지와 프롬프트를 함께 전송
        response = model.generate_content([prompt, pil_image])
        return response.text.strip()
        
    except Exception as e:
        return f"Gemini Analysis Error: {e}"
