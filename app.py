import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# 1. الحزم والـ SDKs التي سيتم تجاهلها كلياً لتسريع البحث وتصفية الضوضاء
EXCLUDED_PACKAGES = [
    "com/unity3d",
    "com/google/android/gms",
    "com/applovin",
    "com/google/firebase",
    "kotlin/",
    "androidx/",
    "android/support",
    "org/json",
]

# 2. الكلمات المفتاحية الحساسة للاشتراكات والترخيص والمميزات المدفوعة
TARGET_KEYWORDS = [
    "premium",
    "subscription",
    "purchase",
    "vip",
    "pro",
    "license",
    "billing",
    "is_pro",
    "is_premium",
    "has_premium",
    "sharedpreferences",
    "not_set",
    "receipt",
    "upgrade",
]

def should_skip(file_path):
    path_str = str(file_path).replace("\\", "/")
    for excl in EXCLUDED_PACKAGES:
        if excl in path_str:
            return True
    return False

def analyze_smali_file(file_path):
    if should_skip(file_path):
        return []

    matched_methods = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        methods = re.split(r"(?=\.method)", content)
        for method in methods:
            if not method.strip():
                continue

            method_lower = method.lower()
            score = sum(1 for kw in TARGET_KEYWORDS if kw in method_lower)

            if score > 0 and "throw p0" not in method:
                sig_match = re.search(
                    r"\.method\s+(?:public|private|protected|static|final|abstract|\s)*([^\n]+)",
                    method,
                )
                method_name = (
                    sig_match.group(1).strip()
                    if sig_match
                    else "Unknown Method"
                )

                matched_methods.append(
                    {
                        "file": str(file_path),
                        "name": method_name,
                        "score": score,
                        "code": method.strip()[:500], # جلب أول 500 حرف من الدالة للعرض
                    }
                )
    except Exception:
        pass

    return matched_methods

def scan_smali_directory(root_dir):
    smali_files = list(Path(root_dir).glob("**/*.smali"))
    all_results = []
    
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(analyze_smali_file, file) for file in smali_files
        ]
        for future in futures:
            res = future.result()
            if res:
                all_results.extend(res)

    return sorted(all_results, key=lambda x: x["score"], reverse=True)

@app.route("/")
def home():
    # يبحث تلقائياً في مجلد باسم smali مرفق مع المشروع، أو المجلد الحالي
    target_directory = "." 
    if os.path.exists("smali"):
        target_directory = "smali"
        
    results = scan_smali_directory(target_directory)
    
    # صفحة HTML بسيطة لعرض النتائج مباشرة على المتصفح
    html_template = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>نتائج فحص الـ Smali</title>
        <style>
            body { background-color: #121212; color: #e0e0e0; font-family: Tahoma, sans-serif; padding: 20px; }
            .card { background: #1e1e1e; border: 1px solid #333; padding: 15px; margin-bottom: 15px; border-radius: 8px; }
            h2 { color: #4caf50; }
            pre { background: #2d2d2d; padding: 10px; border-radius: 5px; overflow-x: auto; color: #ce9178; }
            .file { color: #4fc3f7; }
            .score { color: #ff9800; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>نتائج تحليل دوال الاشتراكات والـ VIP</h1>
        <p>عدد الدوال المكتشفة: {{ results|length }}</p>
        {% for item in results %}
        <div class="card">
            <span class="file">الملف: {{ item.file }}</span><br>
            <h2>الدالة: {{ item.name }}</h2>
            <span class="score">درجة التطابق: {{ item.score }}</span>
            <pre>{{ item.code }}</pre>
        </div>
        {% endfor %}
    </body>
    </html>
    """
    return render_template_string(html_template, results=results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
