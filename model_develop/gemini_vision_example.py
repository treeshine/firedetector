import google.generativeai as genai
import PIL.Image
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 1. API 키 설정
# .env 파일에서 GOOGLE_API_KEY를 가져옵니다.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("오류: .env 파일에서 GOOGLE_API_KEY를 찾을 수 없습니다.")
    print(".env 파일을 생성하고 GOOGLE_API_KEY=your_api_key 형식으로 키를 저장해주세요.")
    exit()

genai.configure(api_key=GOOGLE_API_KEY)

def analyze_image_with_gemini(image_path):
    """
    Gemini API를 사용하여 이미지를 분석하고 내용을 설명합니다.
    """
    try:
        # 이미지 파일 존재 확인
        if not os.path.exists(image_path):
            print(f"오류: '{image_path}' 파일을 찾을 수 없습니다.")
            return

        # 2. 이미지 로드 (Pillow 라이브러리 사용)
        img = PIL.Image.open(image_path)
        print(f"이미지 로드 성공: {image_path}")

        # 3. 모델 초기화
        model = genai.GenerativeModel('gemini-2.5-flash-lite')

        # 4. 콘텐츠 생성 요청 (프롬프트 + 이미지)
        print("Gemini에게 분석 요청 중...")
        prompt = """
        가정집 환경의 CCTV 이미지다. 화재 위험을 분석해라.
        화재 단계를 [경고, 위험, 대피] 중 하나로 판단하고, 발화 위치와 화재 원점으로 보이는 물체, 불길 강도를 포함하여 전체 답변을 100자 이내로 핵심만 요약해라.
        화재의 단계는 다음 기준을 따른다:
        - 경고: 연기나 작은 불꽃이 보이는 초기 단계
        - 위험: 불길이 확산되고 주변 물체에 영향을 미치는 중간 단계
        - 대피: 큰 불길과 심각한 피해가 발생하는 단계
        이미지에서 화재가 감지되지 않으면 '화재 없음'이라고만 답해라.
        답변은 한국어로 작성해라.

        """
        response = model.generate_content([prompt, img])
        
        # 5. 결과 출력
        print("\n" + "="*30)
        print("Gemini 분석 결과")
        print("="*30)
        print(response.text)
        print("="*30)

    except Exception as e:
        print(f"\n오류가 발생했습니다: {e}")

if __name__ == "__main__":
    # 분석할 이미지 경로를 지정하세요.
    # 예: 현재 폴더에 있는 'test.jpg'
    target_image = "test.jpg" 
    
    # 테스트를 위해 이미지가 없다면 안내 메시지 출력
    if not os.path.exists(target_image):
        print(f"'{target_image}' 파일이 현재 폴더에 없습니다.")
        print("분석하고 싶은 이미지 파일의 경로를 'target_image' 변수에 지정해주세요.")
    else:
        analyze_image_with_gemini(target_image)
