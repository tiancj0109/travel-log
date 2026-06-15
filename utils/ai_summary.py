from utils.trip import get_trip_summary_data

def format_trip_data_for_ai(trip_id):
    """
    将旅行数据格式化为文本，供AI生成总结
    
    Args:
        trip_id: 旅行ID
    
    Returns:
        str: 格式化的文本数据
    """
    data = get_trip_summary_data(trip_id)
    
    if not data:
        return None
    
    trip = data['trip']
    members = data['members']
    pre_plan = data['pre_plan']
    logs = data['logs']
    total_expense = data['total_expense']
    
    # 构建文本
    text_parts = []
    
    # 基本信息
    text_parts.append(f"=== 旅行总结数据 ===\n")
    text_parts.append(f"旅行标题：{trip['title']}")
    text_parts.append(f"旅行描述：{trip['description'] or '无'}")
    text_parts.append(f"创建者：{trip['creator_name']}")
    text_parts.append(f"创建时间：{trip['created_at']}")
    text_parts.append(f"当前状态：{trip['status']}\n")
    
    # 同行人
    text_parts.append(f"=== 同行人员 ===")
    for member in members:
        role_text = "创建者" if member['role'] == 'creator' else "成员"
        text_parts.append(f"- {member['username']} ({role_text})")
    text_parts.append("")
    
    # 前期计划
    if pre_plan:
        text_parts.append(f"=== 前期计划 ===")
        text_parts.append(f"时间线：{pre_plan['timeline'] or '未填写'}")
        text_parts.append(f"目的地：{pre_plan['location'] or '未填写'}")
        text_parts.append(f"准备物资：{pre_plan['supplies'] or '未填写'}")
        text_parts.append(f"备注：{pre_plan['notes'] or '未填写'}\n")
    
    # 旅行记录
    if logs:
        text_parts.append(f"=== 旅行记录 ({len(logs)}条) ===")
        for i, log in enumerate(logs, 1):
            text_parts.append(f"\n--- 记录 {i} ---")
            text_parts.append(f"日期：{log['log_date']}")
            text_parts.append(f"心得：{log['notes'] or '无'}")
            text_parts.append(f"花销：¥{log['expense']}")
            text_parts.append(f"有趣的事：{log['interesting_notes'] or '无'}")
        text_parts.append("")
    
    # 总花销
    text_parts.append(f"=== 总计 ===")
    text_parts.append(f"总花销：¥{total_expense}")
    text_parts.append(f"记录天数：{len(logs)}")
    
    return "\n".join(text_parts)

def generate_ai_summary(trip_id):
    """
    生成AI旅行总结
    
    注意：这是一个占位函数，实际需要集成真实的AI API
    
    Args:
        trip_id: 旅行ID
    
    Returns:
        str: AI生成的总结
    """
    formatted_data = format_trip_data_for_ai(trip_id)
    
    if not formatted_data:
        return "无法生成总结：旅行数据不存在"
    
    # TODO: 集成真实的AI API（OpenAI、Google Gemini等）
    # 这里提供一个简单的占位实现
    
    summary = f"""
# 旅行总结

## 原始数据
{formatted_data}

---

## AI总结（待集成）

此处应该是AI生成的总结。请根据需要集成以下AI服务之一：

1. **OpenAI GPT API**
   ```python
   import openai
   response = openai.ChatCompletion.create(
       model="gpt-3.5-turbo",
       messages=[{{"role": "user", "content": f"请总结以下旅行数据：{{formatted_data}}"}}]
   )
   summary = response.choices[0].message.content
   ```

2. **Google Gemini API**
   ```python
   import google.generativeai as genai
   model = genai.GenerativeModel('gemini-pro')
   response = model.generate_content(f"请总结以下旅行数据：{{formatted_data}}")
   summary = response.text
   ```

3. **其他AI服务**
   根据您的需求选择合适的AI服务

---

请修改 `utils/ai_summary.py` 文件以集成真实的AI API。
"""
    
    return summary
