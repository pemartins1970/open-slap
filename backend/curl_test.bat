@echo off
echo Testing MCPs API with token...

curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyMiIsImVtYWlsIjoidGVzdEBleGFtcGxlLmNvbSIsImV4cCI6MTc0NDY0NjQ3N30.5Q4Jz8L7xYdKz8q9X2mF3Gh8JzX1L2w3K4mN5zP7Q" http://127.0.0.1:5150/api/mcps

pause
