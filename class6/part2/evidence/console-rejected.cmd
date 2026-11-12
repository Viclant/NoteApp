@echo off
setlocal
mode con: cols=150 lines=45 >nul
cls
echo == NotesApp JWT Part 2 - unsigned / tampered tokens are refused ==
echo == every request carries the Authorization header only - no cookie ==
echo [1] Part 1 style token: header alg=none, empty signature
curl.exe --noproxy "*" -s -v -o NUL -H "Authorization: Bearer eyJhbGciOiAibm9uZSIsICJ0eXAiOiAiSldUIn0.eyJ1c2VyX2lkIjogMiwgInVzZXJuYW1lIjogInByb2YudHVyaW5nIiwgInJvbGUiOiAidGVhY2hlciJ9." http://127.0.0.1:8082/api/notes/3 2>&1 | findstr /B /C:"> " /C:"< HTTP/1.1"
curl.exe --noproxy "*" -s -H "Authorization: Bearer eyJhbGciOiAibm9uZSIsICJ0eXAiOiAiSldUIn0.eyJ1c2VyX2lkIjogMiwgInVzZXJuYW1lIjogInByb2YudHVyaW5nIiwgInJvbGUiOiAidGVhY2hlciJ9." http://127.0.0.1:8082/api/notes/3
echo [2] forged teacher token with ONE character of the signature changed
curl.exe --noproxy "*" -s -v -o NUL -H "Authorization: Bearer eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJ1c2VyX2lkIjogMiwgInVzZXJuYW1lIjogInByb2YudHVyaW5nIiwgInJvbGUiOiAidGVhY2hlciJ9.dpMXBRkAqUOSb41DJ8FcIshfAm_JNUkL40MRaTUcpdA" http://127.0.0.1:8082/api/notes/3 2>&1 | findstr /B /C:"> " /C:"< HTTP/1.1"
echo [3] no credentials at all
curl.exe --noproxy "*" -s -v -o NUL http://127.0.0.1:8082/api/notes/3 2>&1 | findstr /B /C:"> " /C:"< HTTP/1.1"
echo (all three answers above are HTTP/1.1 401 UNAUTHORIZED, body: error unauthorized)
pause
