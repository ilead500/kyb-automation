# Demo Test 1 - Successful Slack Command
Write-Host "Testing Slack Command..." -ForegroundColor Cyan
$body = @{
    "text" = "CASE-DEMO-001"
    "user_id" = "U123"
    "response_url" = "https://slack.com/fake-webhook"
} | ConvertTo-Json -Compress

Invoke-RestMethod -Uri "http://localhost:8000/slack/commands" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"

# Demo Test 2 - Mock Webhook
Write-Host "`nTesting Mock Webhook..." -ForegroundColor Cyan
Invoke-RestMethod -Uri "http://localhost:8000/mock/persona-webhook" -Method Post

Write-Host "`nDemo complete! Check your Slack channel." -ForegroundColor Green