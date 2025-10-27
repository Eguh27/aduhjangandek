# 🔥 aduhjangandek v2.1

  > _"When your password is weaker than your wifi signal"_ 📶

<img width="248" height="249" alt="image"  src="https://github.com/user-attachments/assets/b8574d44-f725-43f8-9965-7ca5bbd19b05" />
<br></br>

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/yEguh27/aduhjangandek/graphs/commit-activity)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

**Advanced Bruteforce Engine with Interactive Mode** - Karena kadang script Hydra terlalu mainstream, dan GitHub kamu perlu isi selain fork repo orang 💀

## 🎭 What is this?

Aduhjangandek adalah tool bruteforce yang terinspirasi dari Hydra, tapi dengan twist modern:

- ✨ **Interactive Mode** - Pilih level skill kamu: Script Kiddie sampai Advanced (NEW! 🎉)
- 🎯 **Dynamic payload templates** - Ga cuma `username` & `password`, customize sesukamu
- 📄 **SQLMap-style request parsing** - Copy-paste dari Burp Suite langsung jalan
- ⚡ **Smart queue system** - Thread/async workers yang kerja cerdas, bukan kerja keras
- 🎪 **Multi-target support** - Serang banyak endpoint sekaligus (for legal pentesting, tentunya)
- 🔥 **WSL & Linux compatible** - Karena kita semua pake WSL kan? Kan?

### 🆕 What's New in v2.1?

**Interactive Mode** yang bikin hidup lebih mudah:

- 👶 **Script Kiddie Mode** - Tinggal isi target & wordlist, sisanya auto-pilot
- 😎 **Simple Mode** - Custom payload tapi ga ribet
- 🎯 **Medium Mode** - Multi-target dengan rate limiting
- 😈 **Advanced Mode** - Full control, semua opsi di tangan lo
- 🤖 **CLI Mode** - Classic command-line mode buat automation

No more `-h` spam cari tau argument! Tinggal jalanin `python3 main.py` langsung muncul menu interaktif 🚀

## 🚀 Features

### Core Features

- [x] **Interactive Mode** dengan 5 difficulty levels (NEW!)
- [x] Async & Threading engines (pilih sesuai mood)
- [x] Smart queue-based task distribution
- [x] Dynamic payload templates dengan placeholders
- [x] Parse raw HTTP request (à la SQLMap)
- [x] Multi-target attack dari file
- [x] Auto-stop on success (single mode) atau continue (multi mode)
- [x] Progress bar dengan tqdm (biar keliatan profesional)
- [x] Atomic file operations (multiple process safe)
- [x] Distributed attack support dengan sharding

### Payload Placeholders

```
{USER}     → username
{USERNAME} → username (alias)
{PASS}     → password
{PASSWORD} → password (alias)
{EMAIL}    → auto-generate email dari username
{PHONE}    → username as phone number
```

### Distribution Modes

- **user-round**: Round-robin users (default)
- **user-chunk**: Split users into chunks per worker
- **user-queue**: Dynamic per-user queue (atomic pop) 🔥
- **pass-interleave**: Interleave passwords across users

## 📦 Installation

```bash
# Clone repo (atau download zip kalo malu-malu)
git clone https://github.com/Eguh27/aduhjangandek.git
cd aduhjangandek

# Install dependencies
pip install -r requirements.txt

# Atau manual install
pip install aiohttp aiofiles requests tqdm
```

## 🎮 Usage

### 🆕 Interactive Mode (Recommended!)

Jalanin tanpa argument buat masuk interactive mode:

```bash
python3 main.py
```

Nanti muncul menu kece:

```
╔══════════════════════════════════════════════════════════╗
║              Choose Your Fighter! 🎮                      ║
╠══════════════════════════════════════════════════════════╣
║  [1] 👶 Script Kiddie Mode                               ║
║  [2] 😎 Simple Mode                                      ║
║  [3] 🎯 Medium Mode                                      ║
║  [4] 😈 Advanced Mode                                    ║
║  [5] 🤖 CLI Mode (Classic)                               ║
╚══════════════════════════════════════════════════════════╝
```

**Script Kiddie Mode** - Perfect untuk pemula:

- Auto-detect rockyou.txt
- Safe default settings (10 workers, 0.2s delay)
- Tinggal isi target URL & username
- Ga perlu pusing mikir concurrency atau payload

**Simple Mode** - Untuk yang udah familiar:

- Custom payload support
- Single/multi user options
- Adjustable performance settings
- Masih friendly tapi lebih flexible

**Medium Mode** - Buat yang udah pengalaman:

- Multi-target support
- Raw HTTP request parsing
- Rate limiting options
- Distribution mode selection

**Advanced Mode** - Full control freak mode:

- Semua opsi available
- Sharding support untuk distributed attack
- Custom engine selection
- Global coordination dengan flag files

### CLI Mode (Classic)

Buat yang suka old-school atau mau automation:

#### Basic Attack

```bash
# Simple login bruteforce
python3 main.py \
  -t https://api.target.com/login \
  -U users.txt \
  -P passwords.txt \
  -c 20
```

#### Single User Mode

```bash
# Bruteforce single user
python3 main.py \
  -t https://api.target.com/login \
  -u admin \
  -P passwords.txt \
  -c 10 \
  --delay 0.2
```

#### Custom Payload Template

```bash
# Kalo API-nya pake format aneh
python3 main.py \
  -t https://api.target.com/auth \
  -U users.txt \
  -P passwords.txt \
  --payload '{"email":"{EMAIL}","pwd":"{PASS}","remember":true}' \
  --content-type application/json
```

#### SQLMap-Style (Raw HTTP Request)

1. Capture request di Burp Suite
2. Copy as raw HTTP request
3. Save ke file `request.txt`:

```http
POST /api/v1/login HTTP/1.1
Host: api.target.com
Content-Type: application/json
Authorization: Bearer static-token-here
User-Agent: Mozilla/5.0

{"username":"{USER}","password":"{PASS}"}
```

4. Run:

```bash
python3 main.py \
  -r request.txt \
  -U users.txt \
  -P passwords.txt
```

#### Multi-Target Attack

```bash
# File targets.txt berisi list URL
python3 main.py \
  -T targets.txt \
  -U users.txt \
  -P passwords.txt \
  --dist-mode user-queue \
  -c 30
```

#### Advanced: Distributed Bruteforce

Pecah attack ke multiple machines/terminals:

```bash
# Terminal 1 (shard 0)
python3 main.py \
  -t https://api.target.com/login \
  -U users.txt -P passwords.txt \
  --shards 3 --shard-index 0 \
  --global-stop-flag /tmp/stop.flag

# Terminal 2 (shard 1)
python3 main.py \
  -t https://api.target.com/login \
  -U users.txt -P passwords.txt \
  --shards 3 --shard-index 1 \
  --global-stop-flag /tmp/stop.flag

# Terminal 3 (shard 2)
python3 main.py \
  -t https://api.target.com/login \
  -U users.txt -P passwords.txt \
  --shards 3 --shard-index 2 \
  --global-stop-flag /tmp/stop.flag
```

Begitu satu shard nemu password, semua shard auto-stop! 🎯

## 🎯 Real-World Examples

### Example 1: JWT API Login

```bash
python3 main.py \
  -t https://api.example.com/auth/login \
  -U emails.txt \
  -P rockyou.txt \
  --payload '{"email":"{EMAIL}","password":"{PASS}"}' \
  --check-substring '"token":' \
  -c 50 \
  --delay 0.1
```

### Example 2: Form-Based Login

```bash
python3 main.py \
  -t https://example.com/login \
  -U users.txt \
  -P passwords.txt \
  --method POST \
  --content-type application/x-www-form-urlencoded \
  --payload 'username={USER}&password={PASS}&submit=Login' \
  --check-substring 'Welcome back'
```

### Example 3: Phone Number OTP

```bash
python3 main.py \
  -t https://api.example.com/otp/request \
  -U phone_numbers.txt \
  -P otp_codes.txt \
  --payload '{"phone":"{PHONE}","code":"{PASS}"}' \
  --engine threads \
  -c 10 \
  --delay 1.0
```

### Example 4: Custom Headers (via Raw Request)

Save ke `request.txt`:

```http
POST /api/login HTTP/1.1
Host: api.target.com
Content-Type: application/json
X-API-Key: your-static-api-key
X-Client-Version: 2.1.0
User-Agent: MyApp/2.1

{"username":"{USER}","password":"{PASS}"}
```

Run:

```bash
python3 main.py -r request.txt -U users.txt -P passwords.txt
```

## 📊 Output

Results disimpan di folder `found_responses/`:

```
found_responses/
├── hasils.csv                                # Summary semua yang berhasil
├── resp_api_target_com_admin_pass123.json
├── resp_api_target_com_user1_password.json
└── ...
```

Format `hasils.csv`:

```csv
user,pass,file,target
admin,pass123,resp_api_target_com_admin_pass123.json,api.target.com
user1,password,resp_api_target_com_user1_password.json,api.target.com
```

Setiap response disimpan sebagai JSON lengkap, termasuk auto-extract token kalo ada:

- `token`
- `access_token`
- `Token`
- `jwt`
- `sessionId`

## 🎨 Command Line Options

### Required Arguments

```
-t, --target          Target URL
-r, --request         Raw HTTP request file (sqlmap-style)
-T, --targets-file    Multiple targets file

-u, --user            Single username
-U, --users-file      Usernames file

-P, --pass-file       Passwords file (REQUIRED)
```

### Optional Arguments

```
--payload             Custom payload template with {USER}, {PASS}, {EMAIL} placeholders
--content-type        Content-Type header (default: application/json)
--method              HTTP method (default: POST)

-c, --concurrency     Concurrent workers (default: 20)
--timeout             Request timeout in seconds (default: 15)
--delay               Delay between requests per worker (default: 0.0)

-e, --engine          async|threads (default: async)
--dist-mode           user-round|user-chunk|user-queue|pass-interleave (default: user-round)
-m, --mode            single|cartesian (default: cartesian)

--check-substring     Success detection substring (default: "message":"200")
--save-dir            Output directory (default: found_responses)

--shards              Total shards for distributed attack (default: 1)
--shard-index         This shard index, 0-based (default: 0)
--global-stop-flag    Global coordination flag file path
```

### Help & Examples

```bash
# Show full help
python3 main.py --help

# Interactive mode
python3 main.py

# Examples included in help
python3 main.py -h
```

## 🔬 Technical Details

### Architecture

```
┌─────────────────┐
│   Main Thread   │
└────────┬────────┘
         │
    ┌────▼─────┐
    │  Queue   │ (user,pass) pairs
    └────┬─────┘
         │
    ┌────▼──────────────────────┐
    │  Worker Pool (async/thread)│
    │  ┌─────┐ ┌─────┐ ┌─────┐ │
    │  │ W1  │ │ W2  │ │ Wn  │ │
    │  └──┬──┘ └──┬──┘ └──┬──┘ │
    └─────┼──────┼──────┼───────┘
          │      │      │
       ┌──▼──────▼──────▼───┐
       │   Target API       │
       └────────────────────┘
```

**Smart Queue System**:

- Workers ambil task dari queue secara dynamic
- Thread selesai → langsung ambil task baru
- No idle workers, maximum efficiency
- Auto-stop begitu ketemu (single mode)

**Distributed Architecture** (dengan sharding):

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Machine 1   │  │  Machine 2   │  │  Machine 3   │
│  (Shard 0)   │  │  (Shard 1)   │  │  (Shard 2)   │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                  ┌──────▼──────┐
                  │ Global Flag │
                  │   (Stop)    │
                  └─────────────┘
```

### Performance Tips

1. **Async vs Threads**:

   - Use `async` untuk I/O-bound (banyak request, response cepat)
   - Use `threads` untuk CPU-bound atau koneksi lambat
   - Async umumnya 2-3x lebih cepat untuk web requests

2. **Concurrency Sweet Spot**:

   - Script Kiddie: `-c 10` (safe & polite)
   - Normal: `-c 20-50` (balanced)
   - Aggressive: `-c 100-200` (fast but risky)
   - Insane: `-c 500+` (server go brrr... then ban)

3. **Delay Strategy**:

   - No delay (`--delay 0`): YOLO mode 🚀
   - Small delay (`--delay 0.1-0.5`): Polite bruteforce
   - Medium delay (`--delay 0.5-1.0`): Avoid rate limit
   - Large delay (`--delay 1.0+`): Stealth mode (tapi lama banget)

4. **Distribution Modes**:

   - `user-queue`: Best untuk multi-process coordination
   - `user-round`: Best untuk single-process, balanced load
   - `user-chunk`: Best untuk distributed shard attack
   - `pass-interleave`: Best untuk avoiding pattern detection

5. **Memory Considerations**:
   - Wordlist di-load ke memory (keep it reasonable)
   - Jangan load rockyou.txt full kalo RAM cuma 2GB
   - Use `head -n 10000 rockyou.txt > top10k.txt` buat testing

## 📁 Project Structure

Biar gampang di-maintain dan di-contribute:

```
aduhjangandek/
├── main.py                   # Main script
├── README.md                 # You are here
├── LICENSE                   # MIT License
├── requirements.txt          # Production deps
├── requirements-dev.txt      # Dev dependencies (pytest, black, etc)
├── examples/
│   ├── request.txt          # Sample raw HTTP request
│   ├── targets.txt          # Sample multiple targets
│   ├── users.txt            # Sample usernames
│   └── passwords.txt        # Sample passwords
└── tests/
    └── test_main.py # Unit tests
```

Script di-design modular biar gampang:

- Tambahin payload template baru
- Bikin distribution mode baru
- Custom success detection logic
- Integrate dengan tool lain

## ⚠️ Legal Disclaimer

**PENTING BANGET INI DIBACA (ga boong, serius):**

Tool ini dibuat untuk:

- ✅ Security testing dengan izin explicit (pentesting legal)
- ✅ Testing aplikasi sendiri/klien yang authorized
- ✅ Educational purposes di lab environment
- ✅ CTF competitions
- ✅ Bug bounty programs (yang authorized & in-scope)
- ✅ Research purposes dengan ethical approval

Tool ini **TIDAK** boleh digunakan untuk:

- ❌ Unauthorized access ke sistem apapun
- ❌ Illegal hacking activities
- ❌ Nyerang server/API tanpa izin
- ❌ Violating terms of service
- ❌ Hal-hal yang bikin kamu masuk penjara
- ❌ Flexing di forum underground (cringe + illegal)

> **Remember**: Just because you can, doesn't mean you should. Be ethical, be legal, be smart.

**Yang perlu kamu tau:**

1. Selalu minta **written permission** sebelum testing
2. Respect **rate limits** & **ToS** target
3. Jangan DOS-in server orang (ini bruteforce, bukan DDoS tool)
4. Kalo dapet creds, **report responsibly** (jangan di-leak)
5. **Encrypt** hasil finding kamu, jangan simpen plaintext

Penulis tidak bertanggung jawab atas penyalahgunaan tool ini. Kalo kamu pake buat hal illegal terus ketangkep, itu masalah kamu sendiri ya. Jangan mention-mention gw di persidangan 🙏

**Kalo ragu, jangan lakukan.** Simple.

## 🐛 Known Issues & Limitations

- [ ] Pairwise mode masih legacy (belum di-refactor)
- [ ] CAPTCHA detection (belum support, manual handling needed)
- [ ] Auto rate-limit detection (manual adjust delay for now)
- [ ] Session/cookie persistence (use raw request workaround)
- [ ] 2FA bypass (obviously not supported, ini bukan magic)
- [ ] Progress bar kadang loncat kalo pake sharding
- [ ] Memory usage tinggi kalo wordlist gede (load full ke RAM)

**Workarounds**:

- Untuk CAPTCHA: Ya wassalam, manual aja
- Untuk rate-limit: Monitor response, adjust `--delay`
- Untuk session: Save cookies di raw request
- Untuk 2FA: Good luck buddy, that's beyond bruteforce

## 🤝 Contributing

PRs are welcome! Especially untuk:

- 🎯 Better success detection algorithms
- 🔐 Support untuk auth schemes lain (OAuth, SAML, etc)
- 🚀 Performance optimizations
- 🎨 UI/UX improvements (curses-based TUI?)
- 🐳 Docker support
- 📱 Mobile API specific features
- 🧪 More unit tests
- 📚 Documentation improvements
- 🌍 i18n support (kalo sempet)

### Code Style

- Use **Black** untuk formatting
- Follow **PEP 8** (tapi ga strict-strict amat)
- Comment penting di-comment, jangan over-comment
- Variable names: descriptive > singkat
- Function names: verb-based (get_users, parse_request, etc)

### Development Setup

```bash
# Clone & setup
git clone https://github.com/Eguh27aduhjangandek.git
cd aduhjangandek

# Create venv (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
python3 -m pytest tests/ -v

# Format code
black main.py

# Run linting
flake8 main.py --ignore=E501,W503
```

### Pull Request Guidelines

1. Fork repo
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request
6. Wait for review (gw try respon cepet, ga kaya PR gw di kantor)

## 📝 Changelog

### v2.1.0 (2024-10-27) - "Interactive Revolution"

- ✨ **NEW**: Interactive mode dengan 5 difficulty levels
- ✨ **NEW**: Script Kiddie mode untuk absolute beginners
- ✨ **NEW**: Auto-detect rockyou.txt
- ✨ **NEW**: Better input validation & user guidance
- 🎨 Improved banner & menu designs
- 📚 Comprehensive inline help texts
- 🐛 Fixed edge cases di argument parsing
- 🚀 Better error messages & user feedback

### v2.0.0 (2024-10-27)

- ✨ Dynamic payload templates
- ✨ SQLMap-style request parsing
- ✨ Multi-target support
- ✨ Distributed attack dengan sharding
- 🐛 Fixed progress bar accuracy
- 🎨 Improved CLI interface
- 📚 Better documentation

### v1.1.0 (2024-10-25)

- ✨ User-queue distribution mode
- ✨ Atomic file operations
- 🐛 Fixed race conditions
- 🚀 Performance improvements

### v1.0.0 (2024-10-20)

- 🎉 Initial release
- ✨ Async & threading engines
- ✨ Smart queue system
- 📦 Basic payload support

## 🎓 Learn More

### Recommended Reading

- [Hydra Documentation](https://github.com/vanhauser-thc/thc-hydra) - The OG bruteforce tool
- [SQLMap Documentation](https://sqlmap.org/) - Request parsing inspiration
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/) - Web security testing
- [PortSwigger Academy](https://portswigger.net/web-security) - Free web security training

### Bug Bounty Platforms

- [HackerOne](https://www.hackerone.com/)
- [Bugcrowd](https://www.bugcrowd.com/)
- [Intigriti](https://www.intigriti.com/)
- [YesWeHack](https://www.yeswehack.com/)

### CTF Practice

- [HackTheBox](https://www.hackthebox.eu/)
- [TryHackMe](https://tryhackme.com/)
- [PentesterLab](https://pentesterlab.com/)

## 👨‍💻 Author

Dibuat dengan 💀 dan ☕ oleh budak ai yang:

- Capek liat GitHub-nya kosong melompong
- Suka bikin tool yang sebenarnya ga kepake
- Lebih lama bikin README daripada coding
- Ngetik ini sambil nunggu CI/CD selesai

**Contact**:

- GitHub: [@yourusername](https://github.com/Eguh27)
- Twitter: coming soon🥲
- LinkedIn: Ga usah deh, awkward

## 📄 License

MIT License - Bebas dipake, bebas dimodif, tapi kalo bikin masalah jangan salahin gw.

See [LICENSE](LICENSE) file for details.

**TL;DR License**:

- ✅ Use commercially
- ✅ Modify
- ✅ Distribute
- ✅ Private use
- ❌ Liability (kalo error, bukan salah gw)
- ❌ Warranty (works on my machine™)

---

<div align="center">

### ⭐ Star repo ini kalo berguna!

**Atau minimal fork lah biar GitHub ga kaya kuburan** 💀

[![GitHub stars](https://img.shields.io/github/stars/Eguh27/aduhjangandek?style=social)](https://github.com/Eguh27/aduhjangandek/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Eguh27/aduhjangandek?style=social)](https://github.com/Eguh27/aduhjangandek/network/members)

Made with ❤️ and existential dread in Indonesia 🇮🇩

_"Password 'admin123' detected. We're doomed as a species."_

</div>

---

## 🎪 Fun Facts

- Script ini ditulis sambil nunggu PR di kantor di-review (3 minggu belum di-review juga)
- Total coffee consumed: `∞` (mostly instant coffee)
- Times almost gave up: 42 (coincidence? I think not)
- GitHub stars goal: 10 (realistic for once)
- Actual GitHub stars: 0 (reality check)
- Lines of code: ~1000 (termasuk comment yang sok lucu)
- Lines of README: 800+ (priorities, people!)

## 🍕 Support

Kalo script ini ngebantu kamu:

- Dapet bounty: Beliin gw kopi ☕
- Tembus interview: Mention gw di LinkedIn (jk, jangan)
- Passed certification: Good job! (gw ga butuh apa-apa)
- Ace your CTF: Share writeup-nya dong

**Buy me a coffee** (or indomie, gw ga picky):

```
Bitcoin: 1AduhjangandekCoffeeAddressHere
Ethereum: 0xAduhjangandekNeedsCoffeeNotETH
Trakteer: https://trakteer.id/yourname
PayPal: Mimpi kali ye
```

Atau cara paling gampang: **Star this repo** ⭐

---

## 💬 FAQ

**Q: Kenapa harus pake tool ini? Kan ada Hydra?**  
A: Hydra bagus, tapi kadang payload-nya terbatas. Tool ini lebih flexible buat modern APIs.

**Q: Kok lambat banget?**  
A: Coba increase `-c` (concurrency) atau decrease `--delay`. Atau servernya emang lambat.

**Q: Bisa buat bypass 2FA ga?**  
A: Ga bisa. Kalo bisa bypass 2FA pakai bruteforce, itu bukan 2FA namanya.

**Q: Bisa hack Facebook ga?**  
A: _sigh_... No. Please don't.

**Q: Legal ga sih pake ini?**  
A: Legal kalo kamu punya izin. Illegal kalo ga punya izin. Simple.

**Q: Kenapa interactive mode?**  
A: Karena ga semua orang hapal semua CLI flags. Plus, lebih fun!

**Q: Bisa request fitur X?**  
A: Bisa! Open issue atau PR. Tapi ga janji implement, lagi sibuk nge-debug hidup.

**Q: Kontribusi gimana?**  
A: Fork → Code → PR → Profit (in the form of internet points)

---

**PS**: Kalo kamu baca sampe sini, you're awesome! And probably procrastinating something important. Get back to work! (after starring this repo ofc) ⭐

**PPS**: Yes, README ini lebih panjang dari code-nya. That's how we roll in 2024. Documentation is king 👑

**PPPS**: Kalo ada typo, itu feature bukan bug. Namanya "authentic gen-z writing style" ✨
