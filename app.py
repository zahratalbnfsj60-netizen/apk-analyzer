import os
from flask import Flask, request, jsonify, render_template_string
from androguard.misc import AnalyzeAPK

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML_PAGE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>فحص واستخراج الدوال من APK</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #f4f4f9; padding: 20px; text-align: center; }
        .container { max-width: 600px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); margin: auto; }
        input[type="file"] { margin: 20px 0; }
        button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        #output { text-align: left; background: #272822; color: #f8f8f2; padding: 15px; border-radius: 5px; margin-top: 20px; max-height: 300px; overflow-y: auto; direction: ltr; font-family: monospace; white-space: pre-wrap; }
    </style>
</head>
<body>
<div class="container">
    <h2>أداة استخراج الدوال من ملف APK</h2>
    <input type="file" id="apkFile" accept=".apk"><br>
    <button onclick="uploadApk()">تحليل واستخراج الدوال</button>
    <div id="output">نتائج التحليل ستظهر هنا...</div>
</div>
<script>
    async function uploadApk() {
        const fileInput = document.getElementById('apkFile');
        const outputDiv = document.getElementById('output');
        if (fileInput.files.length === 0) { alert('اختر ملف APK أولاً!'); return; }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        outputDiv.innerText = 'جاري رفع الملف وتحليله، قد يستغرق ذلك بعض الوقت...';

        const response = await fetch('/analyze', { method: 'POST', body: formData });
        const result = await response.json();
        
        if (result.success) {
            outputDiv.innerText = result.methods.join('\\n');
        } else {
            outputDiv.innerText = 'خطأ: ' + result.error;
        }
    }
</script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'لم يتم العثور على الملف'})
    
    file = request.files['file']
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        # استخدام الطريقة المتوافقة والمحدثة للتحليل عبر Androguard
        a, d, dx = AnalyzeAPK(file_path)
        
        methods_list = []
        for method in dx.get_methods():
            methods_list.append(f"Class: {method.get_class_name()} --> Method: {method.get_name()}")
            if len(methods_list) >= 500:
                break
                
        os.remove(file_path)
        return jsonify({'success': True, 'methods': methods_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
