from http.server import BaseHTTPRequestHandler
import json
import requests
import re

DOUBAO_API_KEY = "e6ee3334-bb39-4396-8c80-8fb8aaa43dca"
DOUBAO_ENDPOINT = "ep-20250326152755-qgvdv"

HTML_PAGE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GEO智能诊断工具</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 40px 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .header { text-align: center; color: white; margin-bottom: 40px; }
        .header h1 { font-size: 2.5rem; margin-bottom: 10px; }
        .card { background: white; border-radius: 16px; padding: 40px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
        .form-group { margin-bottom: 24px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #333; }
        input[type="text"] { width: 100%; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 16px; }
        button { width: 100%; padding: 16px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 18px; font-weight: 600; cursor: pointer; }
        .loading { display: none; text-align: center; padding: 40px; }
        .spinner { width: 50px; height: 50px; border: 4px solid #f3f3f3; border-top: 4px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .result { display: none; margin-top: 30px; }
        .score-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .score-item { background: #f8f9fa; padding: 20px; border-radius: 12px; text-align: center; }
        .score-value { font-size: 2rem; font-weight: 700; color: #667eea; }
        .score-label { font-size: 0.9rem; color: #666; margin-top: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>GEO智能诊断工具</h1>
            <p>检测品牌在AI搜索中的可见度</p>
        </div>
        <div class="card">
            <form id="diagnoseForm">
                <div class="form-group">
                    <label>品牌名称</label>
                    <input type="text" id="brand_name" placeholder="例如：特斯拉" required>
                </div>
                <div class="form-group">
                    <label>行业</label>
                    <input type="text" id="industry" placeholder="例如：新能源汽车" required>
                </div>
                <div class="form-group">
                    <label>竞品（可选）</label>
                    <input type="text" id="competitors" placeholder="例如：比亚迪,蔚来">
                </div>
                <button type="button" onclick="diagnose()">开始诊断</button>
            </form>
            <div class="loading" id="loading"><div class="spinner"></div><p>正在分析...</p></div>
            <div class="result" id="result"></div>
        </div>
    </div>
    <script>
        async function diagnose() {
            const brand = document.getElementById("brand_name").value;
            const industry = document.getElementById("industry").value;
            const competitors = document.getElementById("competitors").value;
            
            if (!brand || !industry) { alert("请填写品牌名称和行业"); return; }
            
            document.getElementById("loading").style.display = "block";
            document.getElementById("result").style.display = "none";
            
            try {
                const response = await fetch("/api/diagnose?brand=" + encodeURIComponent(brand) + "&industry=" + encodeURIComponent(industry) + "&competitors=" + encodeURIComponent(competitors));
                const data = await response.json();
                displayResult(data);
            } catch (error) { alert("诊断失败：" + error.message); }
            finally { document.getElementById("loading").style.display = "none"; }
        }
        
        function displayResult(data) {
            const resultDiv = document.getElementById("result");
            const scores = data.scores;
            resultDiv.innerHTML = `<div class="score-grid">
                <div class="score-item"><div class="score-value">${scores.overall_score}</div><div class="score-label">综合评分</div></div>
                <div class="score-item"><div class="score-value">${scores.visibility_score}%</div><div class="score-label">AI可见度</div></div>
                <div class="score-item"><div class="score-value">${scores.mention_rate}%</div><div class="score-label">品牌提及率</div></div>
                <div class="score-item"><div class="score-value">${scores.accuracy_score}%</div><div class="score-label">信息准确度</div></div>
            </div>`;
            resultDiv.style.display = "block";
        }
    </script>
</body>
</html>'''

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())
        elif self.path.startswith("/api/diagnose"):
            self.handle_diagnose()
        else:
            self.send_response(404)
            self.end_headers()
    
    def handle_diagnose(self):
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        brand_name = params.get('brand', [''])[0]
        industry = params.get('industry', [''])[0]
        competitors = params.get('competitors', [''])[0]
        
        if not brand_name or not industry:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing parameters"}).encode())
            return
        
        # 模拟诊断结果
        platforms = ["doubao", "deepseek", "kimi"]
        mentioned_count = 2  # 模拟数据
        visibility_score = int((mentioned_count / len(platforms)) * 100)
        accuracy_score = 75
        overall_score = int((visibility_score + visibility_score + accuracy_score) / 3)
        
        result = {
            "brand_name": brand_name,
            "industry": industry,
            "scores": {
                "overall_score": overall_score,
                "visibility_score": visibility_score,
                "mention_rate": visibility_score,
                "accuracy_score": accuracy_score
            }
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())
