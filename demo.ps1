# 1. Test Slack Command
Write-Host "`n[1/2] Testing Slack Command..." -ForegroundColor Cyan
$slackBody = @{
    "text" = "CASE-DEMO-001"
    "user_id" = "U123"
    "response_url" = "https://slack.com/fake"
} | ConvertTo-Json -Compress

try {
    $slackResponse = Invoke-RestMethod -Uri "http://localhost:8000/slack/commands" `
        -Method Post `
        -Body $slackBody `
        -ContentType "application/json" `
        -TimeoutSec 5
    Write-Host "Slack Response:" $slackResponse -ForegroundColor Green
}
catch {
    Write-Host "Slack Command Error: $($_.Exception.Message)" -ForegroundColor Red
}

# 2. Test Webhook
Write-Host "`n[2/2] Testing Webhook..." -ForegroundColor Cyan
try {
    $webhookResponse = Invoke-RestMethod -Uri "http://localhost:8000/mock/persona-webhook" `
        -Method Post `
        -TimeoutSec 5
    Write-Host "Webhook Response:" $webhookResponse -ForegroundColor Green
}
catch {
    Write-Host "Webhook Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nCheck your Slack channel for results!" -ForegroundColor Green