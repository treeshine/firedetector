// 프로젝트 전역 설정
terraform {
  // Provider 정의
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5"
    }
  }
}

// provider 세부설정
provider "cloudflare" {
  // R2 API Token입력
  // 토큰이 VCS에 추적되지 않도록 주의
  api_token = var.cloudflare_api_token
}

