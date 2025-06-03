# 1. Test Slack Command
Write-Host "`n[1/2] Testing Slack Command..." -ForegroundColor Cyan
$slackBody = @{
    "text" = "CASE-DEMO-001"
    "user_id" = "U123"
} | ConvertTo-Json

$slackResponse = Invoke-RestMethod -Uri "http://localhost:8000/slack/commands" `
    -Method Post `
    -Body $slackBody `
    -ContentType "application/json"

Write-Host "Slack Response:" $slackResponse -ForegroundColor Green

# 2. Test Webhook
Write-Host "`n[2/2] Testing Webhook..." -ForegroundColor Cyan
$webhookResponse = Invoke-RestMethod -Uri "http://localhost:8000/mock/persona-webhook" `
    -Method Post

Write-Host "Webhook Response:" $webhookResponse -ForegroundColor Green

Write-Host "`nDEMO SUCCESS! Check your Slack channel." -ForegroundColor Green