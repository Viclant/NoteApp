# Class 9 — session transcript

All commands run on the lab copy at `127.0.0.1:8084` (compose project `class9-lab`).
The real repository was only read.

## 1. Lab start

```
$ docker compose -p class9-lab -f app/docker-compose.yml --env-file app/.env up -d --build
 Volume class9-lab_pgdata  Created
 Container class9-lab-db-1  Started
 Container class9-lab-db-1  Healthy
 Container class9-lab-web-1  Started
$ curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8084/login
200
```

## 2. SQL injection — document's payload (pre-fix)

```
$ curl -s -c sqli-doc.jar \
    --data-urlencode "username=admin' -- " \
    --data-urlencode "password=anything" \
    http://127.0.0.1:8084/login -o sqli-doc-response.html -w "%{http_code}"
200
$ curl -s -b sqli-doc.jar -o /dev/null -w "%{http_code}" http://127.0.0.1:8084/admin
302
$ grep error sqli-doc-response.html
<p class="error">Invalid credentials.</p>
```

Reason: this revision verifies the stored password in Python after the row lookup.

## 3. SQL injection — UNION payload (pre-fix)

```
$ curl -s -c sqli-union.jar \
    --data-urlencode "username=zzz' UNION SELECT 1,'admin','admin','pwned' -- " \
    --data-urlencode "password=pwned" \
    http://127.0.0.1:8084/login -o sqli-union-response.html -w "%{http_code}"
302
$ curl -s -b sqli-union.jar -o admin-after-union.html -w "%{http_code}" http://127.0.0.1:8084/admin
200
$ grep -o "<h1>[^<]*</h1>" admin-after-union.html
<h1>Users</h1>
```

The injected row (`id=1`) was treated as the admin account. Side effect: the app's
password-upgrade branch rewrote the real admin password to `argon2("pwned")`.
The lab volume was rebuilt before the remaining tests.

## 4. SQLi fix

```diff
-        query = (
-            "SELECT id, username, role, password FROM users "
-            "WHERE username = '" + username + "'"
-        )
+        query = (
+            "SELECT id, username, role, password FROM users "
+            "WHERE username = %s"
+        )
...
-            cur.execute(query)
+            cur.execute(query, (username,))
```

Rebuild, then both payloads again:

```
doc payload:    login=200  admin=302  page=[Invalid credentials.]
UNION payload:  login=200  admin=302  page=[Invalid credentials.]
```

## 5. Command injection (pre-fix)

```
$ curl -s -c admin-real.jar -d "username=admin&password=admin123" \
    http://127.0.0.1:8084/login -o /dev/null -w "%{http_code}"
302
$ curl -s -b admin-real.jar -o /dev/null -w "%{http_code}" http://127.0.0.1:8084/admin
200
$ curl -s -b admin-real.jar \
    --data-urlencode "host=127.0.0.1; id; head -2 /etc/passwd" \
    http://127.0.0.1:8084/admin/ping -o cmdi-break.html -w "%{http_code}"
200
$ grep -E "uid=|root:x:0|daemon:" cmdi-break.html
<pre>PING 127.0.0.1 (127.0.0.1) 56(84) bytes of data.
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.054 ms
--- 127.0.0.1 ping statistics ---
uid=0(root) gid=0(root) groups=0(root)
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
```

## 6. Command injection fix and replay

```diff
-    # Host is concatenated straight into a shell command.
-    cmd = "ping -c 1 " + host
     try:
         result = subprocess.run(
-            cmd, shell=True, capture_output=True, text=True, timeout=10,
+            ["ping", "-c", "1", host],
+            capture_output=True, text=True, timeout=10,
         )
```

```
$ curl -s -b admin-real.jar \
    --data-urlencode "host=127.0.0.1; id; head -2 /etc/passwd" \
    http://127.0.0.1:8084/admin/ping -o cmdi-fixed.html -w "%{http_code}"
200
uid/passwd lines: 0
$ grep "Name or service" cmdi-fixed.html
<pre>ping: 127.0.0.1; id; head -2 /etc/passwd: Name or service not known
```

## 7. Normal use after the fixes

```
$ curl -s -c alice.jar -d "username=alice&password=alicepw" \
    http://127.0.0.1:8084/login -o /dev/null -w "%{http_code}"
302
$ curl -s -b alice.jar -o alice-dashboard.html -w "%{http_code}" http://127.0.0.1:8084/dashboard
200
$ grep "<h1>" alice-dashboard.html
<h1>My grades</h1>

$ curl -s -b admin-real.jar --data-urlencode "host=127.0.0.1" \
    http://127.0.0.1:8084/admin/ping -o ping-normal.html -w "%{http_code}"
200
$ grep -m1 "bytes from" ping-normal.html
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.039 ms
```

## 8. Patch check against the real repository

```
$ git -C C:\Users\Viclant\Desktop\NoteApp\NoteApp apply --check injection-fix.patch
(no output)
exit=0
$ git -C C:\Users\Viclant\Desktop\NoteApp\NoteApp status --short
(no output)
```
