# Class 5 audits

Student: 2023905420 - WU YANLAN (Viclant)

Pair: WU YANLAN / CHEN ZIMING

## C5a: HTTPS

- [Traffic audit](https/Audit-summary.txt)
- [HTTPS stream](https/after-https.png)
- [TLS packet list](https/after-https-packets.png)
- [GitHub certificate issuer](https/github-certificate.png)

The HTTP audit records the observed login form line. The original HTTP screenshot
is kept locally because it also contains browser login cookies.

## C5b: password storage

- [Password audit](passwords/Audit-summary.txt)
- [Dictionary attack results](passwords/crack-results.json)
- [MD5 and Argon2 measurements](passwords/measure-results.json)
- [Login and migration checks](passwords/login-checks.json)

The measurements use the six practice accounts and the public wordlist from the
course. The rate comparison is one local CPU/container measurement. The per-day
values are estimates obtained by multiplying the measured rates by 86,400.

Setup and verification commands are in the main [README](../README.md).
