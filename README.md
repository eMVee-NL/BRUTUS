# BRUTUS ─ HTTP Form Brute Forcer 

A fast, multithreaded HTTP POST web form brute forcing utility written in Python. Specially optimized for penetration testing automation, security auditing, and Capture The Flag (CTF) or vulnerable machines.

---

## Technical Architecture Overview

BRUTUS leverages concurrent system worker threads via `ThreadPoolExecutor` to rapidly execute high volume authentication sequences against specialized entry nodes. Unlike static tools, it incorporates robust thread synchronization (`threading.Lock`) to map real time performance attributes without cross contamination.

### Flexible Infiltration Analysis Modes
BRUTUS adapts dynamically to target endpoint response behavior using three distinct auditing mechanisms:
1. **Failure Mode (`-m F`):** Flagged as an active verification match if the defined string *disappears* from the application body response canvas.
2. **Success Mode (`-m S`):** Triggers successful extraction credentials when specific response markers or valid destination maps *appear* inside text responses or location headers.
3. **Redirect Mode (`-m R`):** Targets status code 302/301 shifts to map successful state transitions natively.

---

## Features
- **Concurrent Thread Pools:** Fully asynchronous execution with dynamic worker pool mapping.
- **Real-Time Visual Progress:** Thread safe terminal overlay capturing ongoing credentials and percentage steps.
- **Fail-Safe Mechanism:** Instantly cancels and tears down remaining connection pipelines (`threading.Event`) the millisecond valid keys are exfiltrated.
- **Universal Parameter Binding:** Custom flags to specify injection points for both usernames and password fields.
- **Proxy Layer Integration:** Native HTTP/HTTPS upstream routing interface.

---

## Usage

### Command Line Arguments
```text
options:
  -h, --help            show this help message and exit
  -u URL, --url URL     Target URL endpoint (e.g., http://judiciary.hmv)
  -l USERNAME, --username USERNAME
                        Single target username string
  -L USERLIST, --userlist USERLIST
                        Path to the target users wordlist file
  -p PASSWORD, --password PASSWORD
                        Single target password string
  -P PASSLIST, --passlist PASSLIST
                        Path to the target passwords wordlist file
  -t THREADS, --threads THREADS
                        Number of concurrent execution threads (default: 20)
  -m {F,S,R}, --mode {F,S,R}
                        Evaluation mode: F=Failure string, S=Success string, R=Redirect status
  -c CONDITION, --condition CONDITION
                        The specific string, error or redirect route to match against
  -A USER_AGENT, --user-agent USER_AGENT
                        Custom User-Agent header transmission string (default: brutus)
  -x PROXY, --proxy PROXY
                        HTTP proxy URL address (e.g., http://127.0.0.1:8080)
  --user-param USER_PARAM
                        POST parameter key for the username field (default: username)
  --pass-param PASS_PARAM
                        POST parameter name for the password field (default: password)
```

---

## Deployment Examples

### Scenario: Auditing a Registry Portal Form (Failure String matching)
Audit an absolute user matrix file (`users.txt`) looking for a specific target password string, tracking responses on an authentication failure message block:
```bash
python3 brutus.py -u http://URL.hmv \
  -L users.txt \
  -p SecretPassword \
  -m F \
  -c "Invalid username identifier" \
  -t 40
```

### Scenario: High-Speed Custom Ingestion Parameter Check
```bash
python3 brutus.py -u http://target.local \
  -l hacker \
  -P wordlist.txt \
  --user-param registry_id \
  --pass-param credentials \
  -m S \
  -c "Dashboard Access Granted"
```
<img width="954" height="465" alt="afbeelding" src="https://github.com/user-attachments/assets/7b13bc33-0d54-4250-9c37-f18703674a49" />
