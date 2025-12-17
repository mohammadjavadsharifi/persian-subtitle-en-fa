from flask import Flask, render_template, request, send_file
import pysrt
import io
import requests

app = Flask(__name__)

# <<<--- API Key Groq خودت رو اینجا بذار (با gsk_ شروع می‌شه)
GROQ_API_KEY = ""

API_URL = "https://api.groq.com/openai/v1/chat/completions"

def translate_text(text: str) -> str:
    if not text.strip():
        return ''
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",  # مدل جدید و جایگزین (کیفیت عالی برای ترجمه فارسی)
        # گزینه‌های جایگزین اگر بخوای:
        # "llama-3.1-8b-instant" → خیلی سریع‌تر اما کیفیت کمتر
        # "mixtral-8x7b-32768" → اگر هنوز موجود باشه، خوب برای چندزبانه
        "messages": [
            {
                "role": "system",
                "content": "You are a professional English-to-Persian subtitle translator. Translate the text naturally, fluently, and accurately for movie/TV subtitles. Keep the tone and context. Output ONLY the translated Persian text, nothing else."
            },
            {
                "role": "user",
                "content": text.strip()
            }
        ],
        "temperature": 0.3
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            print(f"خطای Groq ({response.status_code}): {response.text}")
            return '\u200F' + text.strip()
        
        result = response.json()
        translated = result['choices'][0]['message']['content'].strip()
        return '\u200F' + translated
    except Exception as e:
        print(f"استثنا در ارتباط با Groq: {e}")
        return '\u200F' + text.strip()

def translate_srt(file_content: bytes):
    content_str = file_content.decode('utf-8')
    subs = pysrt.from_string(content_str)
    
    for sub in subs:
        sub.text = translate_text(sub.text)
    
    # ساخت دستی فایل SRT — تمیز و بدون مشکل
    lines = []
    for sub in subs:
        lines.append(str(sub.index))
        start_str = sub.start.to_time().strftime('%H:%M:%S,%f')[:-3]
        end_str = sub.end.to_time().strftime('%H:%M:%S,%f')[:-3]
        lines.append(f"{start_str} --> {end_str}")
        lines.append(sub.text.strip() if sub.text else '')
        lines.append('')
    
    return '\n'.join(lines)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "فایلی آپلود نشده است.", 400
        file = request.files['file']
        if file.filename == '':
            return "فایلی انتخاب نشده است.", 400
        if not file.filename.lower().endswith('.srt'):
            return "فقط فایل‌های .srt مجاز هستند.", 400
        
        file_content = file.read()
        
        try:
            srt_content = translate_srt(file_content)
            output = io.BytesIO(srt_content.encode('utf-8'))
            output.seek(0)
            
            return send_file(
                output,
                as_attachment=True,
                download_name='translated_persian.srt',
                mimetype='application/x-subrip'
            )
        except Exception as e:
            return f"خطا در پردازش فایل: {str(e)}", 500
    
    return render_template('index.html')

if __name__ == '__main__':
    print("سرور ترجمه زیرنویس با Groq (مدل جدید Llama 3.3) راه‌اندازی شد!")
    print("برو به آدرس: http://127.0.0.1:5000")
    app.run(debug=True)
