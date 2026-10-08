#!/usr/bin/env python3
import sys
import os
import base64
import json
import urllib.request
import urllib.error

def github_api(method, endpoint, token, data=None):
    url = f"https://api.github.com{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "InstaAnaliz-Deployer"
    }
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8")), resp.status
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        return {"error": err_msg}, e.code

def deploy(token, username, repo_name="takip-temizle"):
    print(f"[*] GitHub deposu kontrol ediliyor: {username}/{repo_name}...")
    
    # 1. Depoyu oluşturmayı dene
    create_data = {
        "name": repo_name,
        "description": "Instagram Takip Yöneticisi — Özel ve Cihazda Çalışan PWA",
        "private": False,
        "auto_init": False
    }
    resp, code = github_api("POST", "/user/repos", token, create_data)
    if code in (201, 200):
        print(f"[+] Depo başarıyla oluşturuldu: https://github.com/{username}/{repo_name}")
    elif code == 422:
        print(f"[*] Depo zaten mevcut, dosyalar güncellenecek.")
    else:
        print(f"[-] Depo oluşturulamadı ({code}): {resp}")
        return False

    # 2. Dosyaları yükle
    deploy_dir = os.path.dirname(os.path.abspath(__file__))
    files_to_upload = ["index.html", "jszip.min.js", "favicon.ico", "apple-touch-icon.png", "apple-touch-icon-precomposed.png", "apple-touch-icon-240x240.png"]

    for fname in files_to_upload:
        fpath = os.path.join(deploy_dir, fname)
        if not os.path.exists(fpath):
            continue
        
        with open(fpath, "rb") as f:
            content_b64 = base64.b64encode(f.read()).decode("utf-8")
        
        # Mevcut dosyanın SHA'sını al (varsa güncellemek için)
        get_resp, get_code = github_api("GET", f"/repos/{username}/{repo_name}/contents/{fname}", token)
        sha = get_resp.get("sha") if get_code == 200 else None

        put_data = {
            "message": f"Add {fname}",
            "content": content_b64
        }
        if sha:
            put_data["sha"] = sha

        put_resp, put_code = github_api("PUT", f"/repos/{username}/{repo_name}/contents/{fname}", token, put_data)
        if put_code in (200, 201):
            print(f"[+] {fname} yüklendi.")
        else:
            print(f"[-] {fname} yüklenirken hata ({put_code}): {put_resp}")

    # 3. GitHub Pages'i etkinleştir
    pages_data = {
        "source": {
            "branch": "main",
            "path": "/"
        }
    }
    pg_resp, pg_code = github_api("POST", f"/repos/{username}/{repo_name}/pages", token, pages_data)
    if pg_code in (201, 200):
        print(f"[+] GitHub Pages başarıyla etkinleştirildi!")
    else:
        print(f"[*] GitHub Pages durumu ({pg_code}). Zaten aktif olabilir.")

    live_url = f"https://{username}.github.io/{repo_name}/"
    print("\n" + "="*50)
    print(f"🎉 TEBRİKLER! UYGULAMANIZ CANLIDA:")
    print(f"👉 {live_url}")
    print("="*50)
    return live_url

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Kullanım: python3 upload_to_github.py <GITHUB_TOKEN> <GITHUB_KULLANICI_ADI> [DEPO_ADI]")
        sys.exit(1)
    t = sys.argv[1]
    u = sys.argv[2]
    r = sys.argv[3] if len(sys.argv) > 3 else "takip-temizle"
    deploy(t, u, r)
