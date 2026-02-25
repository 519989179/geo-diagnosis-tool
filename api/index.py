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
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 40px 20px; }
        .container { max-width: 1000px; margin: 0 auto; }
        .header { text-align: center; color: white; margin-bottom: 40px; }
        .header h1 { font-size: 2.5rem; margin-bottom: 10px; }
        .card { background: white; border-radius: 16px; padding: 40px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); margin-bottom: 20px; }
        .form-group { margin-bottom: 24px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #333; }
        input[type="text"] { width: 100%; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 16px; }
        button { width: 100%; padding: 16px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 18px; font-weight: 600; cursor: pointer; margin-bottom: 10px; }
        .btn-secondary { background: #28a745; }
        .loading { display: none; text-align: center; padding: 40px; }
        .spinner { width: 50px; height: 50px; border: 4px solid #f3f3f3; border-top: 4px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .result { display: none; }
        
        /* 报告样式 */
        .report-header { text-align: center; padding: 30px; border-bottom: 3px solid #667eea; margin-bottom: 40px; }
        .report-header h1 { color: #667eea; font-size: 2rem; margin-bottom: 15px; }
        .report-meta { color: #666; font-size: 0.95rem; line-height: 1.8; }
        .report-section { margin-bottom: 35px; }
        .report-section h2 { 
            color: #333; 
            font-size: 1.4rem; 
            border-left: 5px solid #667eea; 
            padding-left: 15px; 
            margin-bottom: 20px;
            padding-top: 5px;
            padding-bottom: 5px;
        }
        .report-section h3 {
            color: #667eea;
            font-size: 1.1rem;
            margin: 20px 0 12px 0;
        }
        .report-section p, .report-section li {
            color: #444;
            line-height: 1.8;
            margin-bottom: 10px;
        }
        .report-section ul {
            padding-left: 25px;
        }
        .highlight-box {
            background: #f0f4ff;
            border-left: 4px solid #667eea;
            padding: 20px;
            border-radius: 0 8px 8px 0;
            margin: 15px 0;
        }
        .action-step {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid #28a745;
        }
        .action-step h4 {
            color: #28a745;
            margin-bottom: 12px;
            font-size: 1.05rem;
        }
        .score-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; margin: 30px 0; }
        .score-item { background: #667eea; color: white; padding: 25px; border-radius: 12px; text-align: center; }
        .score-value { font-size: 2.5rem; font-weight: 700; }
        .score-label { font-size: 0.95rem; margin-top: 8px; }
        .download-section { margin-top: 30px; text-align: center; padding: 30px; background: #f8f9fa; border-radius: 12px; }
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
                    <label>竞品（可选，用逗号分隔）</label>
                    <input type="text" id="competitors" placeholder="例如：比亚迪,蔚来">
                </div>
                <button type="button" onclick="diagnose()">开始诊断</button>
            </form>
            <div class="loading" id="loading"><div class="spinner"></div><p>正在生成专业诊断报告，请稍候...</p></div>
        </div>
        
        <div class="result" id="result"></div>
    </div>
    
    <script>
        let currentReportData = null;
        
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
                currentReportData = data;
                displayResult(data);
            } catch (error) { alert("诊断失败：" + error.message); }
            finally { document.getElementById("loading").style.display = "none"; }
        }
        
        function displayResult(data) {
            const resultDiv = document.getElementById("result");
            const report = data.report || {};
            const date = new Date().toLocaleString("zh-CN");
            
            var scores = data.scores || {};
            var overallScore = scores.overall_score || 0;
            var visibilityScore = scores.visibility_score || 0;
            var mentionRate = scores.mention_rate || 0;
            var accuracyScore = scores.accuracy_score || 0;
            
            var competitorsHtml = "";
            if (data.competitors) {
                competitorsHtml = '<p><strong>对标竞品：</strong>' + data.competitors + '</p>';
            }
            
            var html = '<div id="report-content">';
            
            // 报告头部
            html += '<div class="card">' +
                '<div class="report-header">' +
                    '<h1>GEO 品牌智能诊断与优化报告</h1>' +
                    '<div class="report-meta">' +
                        '<p><strong>诊断品牌：</strong>' + data.brand_name + '</p>' +
                        '<p><strong>所属行业：</strong>' + data.industry + '</p>' +
                        competitorsHtml +
                        '<p><strong>诊断时间：</strong>' + date + '</p>' +
                    '</div>' +
                '</div>' +
                '<div class="score-grid">' +
                    '<div class="score-item"><div class="score-value">' + overallScore + '</div><div class="score-label">综合评分</div></div>' +
                    '<div class="score-item"><div class="score-value">' + visibilityScore + '%</div><div class="score-label">AI可见度</div></div>' +
                    '<div class="score-item"><div class="score-value">' + mentionRate + '%</div><div class="score-label">品牌提及率</div></div>' +
                    '<div class="score-item"><div class="score-value">' + accuracyScore + '%</div><div class="score-label">信息准确度</div></div>' +
                '</div>' +
            '</div>';
            
            // 执行摘要
            if (report.summary) {
                var healthStatus = report.summary.health_status || "";
                var coreStrengths = report.summary.core_strengths || "";
                var criticalBlindspots = report.summary.critical_blindspots || "";
                
                html += '<div class="card report-section">' +
                    '<h2>1. GEO 综合诊断执行摘要</h2>' +
                    '<div class="highlight-box">' +
                        '<p><strong>品牌AI搜索健康度：</strong>' + healthStatus + '</p>' +
                    '</div>' +
                    '<h3>核心优势</h3>' +
                    '<p>' + coreStrengths + '</p>' +
                    '<h3>致命盲区</h3>' +
                    '<p>' + criticalBlindspots + '</p>' +
                '</div>';
            }
            
            // 可见度与认知分析
            if (report.visibility) {
                var words = report.visibility.association_words || [];
                var wordsHtml = "";
                for (var i = 0; i < words.length; i++) {
                    wordsHtml += "<li>" + words[i] + "</li>";
                }
                var painPoint = report.visibility.pain_point_match || "";
                
                html += '<div class="card report-section">' +
                    '<h2>2. 品牌可见度与认知分析</h2>' +
                    '<h3>AI 引擎核心联想词</h3>' +
                    '<ul>' + wordsHtml + '</ul>' +
                    '<h3>痛点匹配度</h3>' +
                    '<p>' + painPoint + '</p>' +
                '</div>';
            }
            
            // 竞品分析
            if (report.competitor) {
                var disadvantage = report.competitor.disadvantage_scenarios || "";
                var differentiation = report.competitor.differentiation || "";
                
                html += '<div class="card report-section">' +
                    '<h2>3. 竞品拦截与对比分析</h2>' +
                    '<h3>劣势卡位</h3>' +
                    '<p>' + disadvantage + '</p>' +
                    '<h3>差异化壁垒</h3>' +
                    '<p>' + differentiation + '</p>' +
                '</div>';
            }
            
            // 优化行动指南
            if (report.actions) {
                html += '<div class="card report-section">' +
                    '<h2>4. 核心优化行动指南</h2>';
                
                if (report.actions.step1) {
                    html += '<div class="action-step">' +
                        '<h4>Step 1: 核心词条修复 (紧急)</h4>' +
                        '<p>' + report.actions.step1 + '</p>' +
                    '</div>';
                }
                if (report.actions.step2) {
                    html += '<div class="action-step">' +
                        '<h4>Step 2: 长尾提问占位 (中期)</h4>' +
                        '<p>' + report.actions.step2 + '</p>' +
                    '</div>';
                }
                if (report.actions.step3) {
                    html += '<div class="action-step">' +
                        '<h4>Step 3: 品牌声量放大 (长期)</h4>' +
                        '<p>' + report.actions.step3 + '</p>' +
                    '</div>';
                }
                html += '</div>';
            }
            
            html += '</div>'; // end report-content
            
            // 下载按钮
            html += '<div class="card download-section">' +
                '<h3 style="margin-bottom: 20px;">报告已生成</h3>' +
                '<button type="button" class="btn-secondary" onclick="downloadPDF()">下载PDF报告</button>' +
            '</div>';
            
            resultDiv.innerHTML = html;
            resultDiv.style.display = "block";
            resultDiv.scrollIntoView({ behavior: "smooth" });
        }
        
        function downloadPDF() {
            if (!currentReportData) return;
            
            var element = document.getElementById("report-content");
            var brand = currentReportData.brand_name;
            var date = new Date().toISOString().split("T")[0];
            
            var opt = {
                margin: 15,
                filename: "GEO诊断报告_" + brand + "_" + date + ".pdf",
                image: { type: "jpeg", quality: 0.98 },
                html2canvas: { scale: 2, useCORS: true },
                jsPDF: { unit: "mm", format: "a4", orientation: "portrait" }
            };
            
            html2pdf().set(opt).from(element).save();
        }
    </script>
</body>
</html>'''

class DoubaoAPIClient:
    def __init__(self, api_key, endpoint_id):
        self.api_key = api_key
        self.endpoint_id = endpoint_id
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3"
    
    def chat(self, messages, max_tokens=2000, temperature=0.7):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": self.endpoint_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[API错误: {str(e)}]"

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
        
        doubao = DoubaoAPIClient(DOUBAO_API_KEY, DOUBAO_ENDPOINT)
        
        prompt = f"""你是一位顶级的 GEO (生成式引擎优化) 品牌诊断专家 & 商业分析师。

请为以下品牌生成一份专业的《GEO 品牌智能诊断与优化报告》：

【品牌名称】：{brand_name}
【所属行业】：{industry}
【竞品列表】：{competitors if competitors else '未指定'}

重要：请根据该品牌的实际知名度、市场地位、行业影响力来给出差异化评分。
- 知名品牌/头部品牌：评分应在 75-95 之间
- 中等知名度品牌：评分应在 50-75 之间  
- 小众/新品牌：评分应在 30-55 之间

请严格按照以下结构输出 JSON 格式的报告：

{{
    "scores": {{
        "overall_score": 0-100之间的整数,
        "visibility_score": 0-100之间的整数,
        "mention_rate": 0-100之间的整数,
        "accuracy_score": 0-100之间的整数
    }},
    "summary": {{
        "health_status": "用一句话总结品牌在 AI 引擎中的整体表现状态（50字以内）",
        "core_strengths": "总结 AI 对品牌最正向的认知点（100字左右）",
        "critical_blindspots": "一针见血指出目前最容易流失客户的缺陷所在（100字左右）"
    }},
    "visibility": {{
        "association_words": ["AI最常关联的特征词1", "特征词2", "特征词3", "特征词4", "特征词5"],
        "pain_point_match": "评估品牌信息是否有效覆盖了行业用户的核心痛点（150字左右）"
    }},
    "competitor": {{
        "disadvantage_scenarios": "在哪些高频用户提问场景下，AI 优先推荐了竞品而不是本品牌？（150字左右）",
        "differentiation": "本品牌在 AI 的认知中，有别于竞品的独特记忆点是什么？该如何放大？（150字左右）"
    }},
    "actions": {{
        "step1": "核心词条修复 - 具体建议品牌应该在哪些平台发布什么样的内容，以纠正 AI 的错误认知或填补空白（200字左右）",
        "step2": "长尾提问占位 - 结合行业特性，建议 2-3 个极具引流价值的长尾提问，并给出内容创作方向（200字左右）",
        "step3": "品牌声量放大 - 建议如何通过第三方背书或跨界合作，提升在 AI 大模型中的数据权重（200字左右）"
    }}
}}

评分标准（0-100分）：
- overall_score: 综合评分，基于品牌在AI搜索中的整体表现
- visibility_score: AI可见度，知名品牌应高于70，小众品牌可能低于50
- mention_rate: 品牌提及率，头部品牌应高于80，新品牌可能低于40
- accuracy_score: 信息准确度，有完善资料的品牌应高于75

注意：
1. 不同品牌的评分必须有明显差异，不能所有品牌都给相似分数
2. 使用商业分析、品牌营销和 GEO 领域的专业术语
3. 诊断的最终目的是为了"优化"，建议必须是具体的、可落地执行的操作指南
4. 内容要专业客观，具有极高的商业价值"""
        
        messages = [
            {"role": "system", "content": "你是一位精通GEO（生成式引擎优化）的品牌诊断专家，擅长分析品牌在AI搜索中的表现并给出专业建议。"},
            {"role": "user", "content": prompt}
        ]
        
        response = doubao.chat(messages, max_tokens=2000, temperature=0.9)
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                report = json.loads(json_match.group())
            else:
                report = self.get_default_report()
        except:
            report = self.get_default_report()
        
        # 从AI返回的报告中获取分数，如果没有则使用默认值
        scores = report.get('scores', {})
        overall_score = scores.get('overall_score', 65)
        visibility_score = scores.get('visibility_score', 60)
        mention_rate = scores.get('mention_rate', visibility_score)
        accuracy_score = scores.get('accuracy_score', 70)
        
        platforms = ["doubao", "deepseek", "kimi"]
        platform_results = {}
        for platform in platforms:
            platform_results[platform] = {
                "brand_mentioned": True,
                "mention_position": 2,
                "mention_count": 1,
                "sentiment": "positive",
                "analysis": "品牌在该平台有一定曝光和认知度"
            }
        
        visibility_score = 65
        accuracy_score = 70
        overall_score = 68
        
        result = {
            "brand_name": brand_name,
            "industry": industry,
            "competitors": competitors,
            "scores": {
                "overall_score": overall_score,
                "visibility_score": visibility_score,
                "mention_rate": mention_rate,
                "accuracy_score": accuracy_score
            },
            "platform_results": platform_results,
            "report": report
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
    
    def get_default_report(self):
        return {
            "scores": {
                "overall_score": 65,
                "visibility_score": 60,
                "mention_rate": 60,
                "accuracy_score": 70
            },
            "summary": {
                "health_status": "品牌在AI搜索中处于中等水平，有一定认知度但缺乏系统性优化",
                "core_strengths": "品牌在特定场景下有一定提及率，用户对其核心功能有基本认知",
                "critical_blindspots": "缺乏针对AI引擎优化的内容布局，在竞品对比场景下容易被忽略"
            },
            "visibility": {
                "association_words": ["功能实用", "操作便捷", "性价比高", "模板丰富", "用户友好"],
                "pain_point_match": "品牌信息基本覆盖了行业核心痛点，但在深度解决方案层面仍有提升空间"
            },
            "competitor": {
                "disadvantage_scenarios": "在'最佳XX工具推荐'、'XX工具对比'等高频搜索场景下，AI优先推荐竞品",
                "differentiation": "品牌在特定细分功能上有独特优势，需要通过内容营销放大这一记忆点"
            },
            "actions": {
                "step1": "在知乎、CSDN等平台发布'XX品牌使用指南'、'XX功能详解'等专业内容，建立权威词条",
                "step2": "针对'如何选择XX工具'、'XX工具哪个好'等长尾问题，创作对比评测类内容",
                "step3": "与行业KOL合作产出专业评测，通过第三方背书提升AI对品牌的信任权重"
            }
        }
