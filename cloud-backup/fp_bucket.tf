// 오탐데이터 R2 버킷 선언
resource "cloudflare_r2_bucket" "fp_r2_bucket" {
  account_id    = var.account_id
  name          = var.fp_bucket_name // 주의: 버킷 실제 이름은 kebab-case를 지켜야 함
  storage_class = "Standard"
}

// 오탐데이터 버킷 생명주기 설정
resource "cloudflare_r2_bucket_lifecycle" "fp_r2_bucket_lifecycle" {
  account_id  = var.account_id
  bucket_name = var.fp_bucket_name
  rules = [{
    id      = "Expire All fp objects older than 100days"
    enabled = true
    conditions = {
      prefix = "" // 모든 객체에 대해서
    }
    delete_objects_transition = {
      condition = {
        max_age = 60 * 60 * 24 * 100 // 초 단위, 즉 100일 이후 삭제
        type    = "Age"
      }
    }
  }]

}

