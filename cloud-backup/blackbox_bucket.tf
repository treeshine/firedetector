// 블랙박스 R2 버킷 선언
resource "cloudflare_r2_bucket" "blackbox_r2_bucket" {
  account_id    = var.account_id
  name          = var.blackbox_bucket_name // 주의: 버킷 실제 이름은 kebab-case를 지켜야 함
  storage_class = "Standard"
}

// 블랙박스 버킷 생명주기 설정
resource "cloudflare_r2_bucket_lifecycle" "blackbox_r2_bucket_lifecycle" {
  account_id  = var.account_id
  bucket_name = var.blackbox_bucket_name
  rules = [{
    id      = "Make sure to move objects older than 30 days to infrequent-access storageclass"
    enabled = true
    conditions = {
      prefix = "" // 모든 객체에 대해서
    }
    storage_class_transitions = [{
      condition = {
        max_age = 60 * 60 * 24 * 30 // 초 단위, 즉 30일 이후
        type    = "Age"
      }
      storage_class = "InfrequentAccess"
    }]
  }]

}

