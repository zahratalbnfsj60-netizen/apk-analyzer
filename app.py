import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# --- ألوان العرض في التيرمينال ---
GREEN = "\033[92m"  # دالة ذات تطابق قوي جداً (هدف محتمل)
CYAN = "\033[96m"  # مسار الملف وا الاسم
YELLOW = "\033[93m"  # تنبيهات أو إحصائيات
RED = "\033[91m"  # استثناءات أو مسارات مهملة
RESET = "\033[0m"  # إعادة اللون الافتراضي

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
    """التحقق مما إذا كان الملف ينتمي لـ SDK خارجي مستبعد لتوفير الوقت"""
    path_str = str(file_path).replace("\\", "/")
    for excl in EXCLUDED_PACKAGES:
        if excl in path_str:
            return True
    return False


def analyze_smali_file(file_path):
    """قراءة وتحليل ملف الـ Smali واستخراج الدوال المستهدفة فقط"""
    if should_skip(file_path):
        return []

    matched_methods = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # تقسيم الملف إلى دوال بناءً على كلمة .method
        methods = re.split(r"(?=\.method)", content)
        for method in methods:
            if not method.strip():
                continue

            method_lower = method.lower()

            # حساب عدد الكلمات المفتاحية الموجودة في الدالة
            score = sum(1 for kw in TARGET_KEYWORDS if kw in method_lower)

            # شروط التصفية الصارمة: يجب أن تحتوي على الأقل على كلمة مفتاحية واحدة وليست دالة فحص أمان فارغة
            if score > 0 and "throw p0" not in method:
                # استخراج توقيع الدالة (اسمها)
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
                        "code": method.strip(),
                    }
                )
    except Exception:
        pass

    return matched_methods


def scan_smali_directory(root_dir):
    """بحث متوازي وسريع في كافة مجلدات المشروع"""
    print(f"{YELLOW}[*] جاري البحث عن ملفات الـ Smali وتصفية الـ SDKs...{RESET}")
    smali_files = list(Path(root_dir).glob("**/*.smali"))
    print(
        f"{YELLOW}[*] تم العثور على {len(smali_files)} ملف مستهدف للفحص.{RESET}\n"
    )

    all_results = []
    # استخدام ThreadPoolExecutor للبحث السريع جداً عبر المعالجات المتعددة
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(analyze_smali_file, file) for file in smali_files
        ]
        for future in futures:
            res = future.result()
            if res:
                all_results.extend(res)

    return all_results


if __name__ == "__main__":
    # ضع مسار مجلد فك الضغط (يعمل تلقائياً في نفس المجلد إذا وُضع داحله)
    target_directory = input(
        "[?] أدخل مسار مجلد استخراج التطبيق (اضغط Enter لاختيار المجلد الحالي): "
    ).strip()
    if not target_directory:
        target_directory = "."

    results = scan_smali_directory(target_directory)

    print(
        f"\n{GREEN}=================================================={RESET}"
    )
    print(
        f"{GREEN} تم العثور على {len(link := len(results))} دالة محتملة تتعلق بالاشتراكات والمميزات المدفوعة:{RESET}"
    )
    print(
        f"{GREEN}=================================================={RESET}\n"
    )

    # فرز النتائج تنازلياً حسب قوة التطابق (Score)
    results = sorted(results, key=lambda x: x["score"], reverse=True)

    for idx, item in enumerate(results, 1):
        print(f"{CYAN}[{idx}] الملف: {item['file']}{RESET}")
        print(f"{GREEN}    الدالة: {item['name']} (Score: {item['score']}){RESET}")
        print(f"    ----------------------------------------------")
        # عرض أول أسطر من الكود لتوفير الرؤية السريعة
        code_lines = item["code"].split("\n")[:10]
        for line in code_lines:
            print(f"    {line}")
        print(
            f"    ..............................................\n"
        )
