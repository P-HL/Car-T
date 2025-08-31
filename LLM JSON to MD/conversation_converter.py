#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini对话转Markdown转换器
专门用于转换 Gemini API 格式的对话文件

作者: GitHub Copilot
版本: 4.0.0
"""

import os
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


def extract_conversations_from_gemini_file(file_path: str) -> List[Dict[str, Any]]:
    """
    直接从Gemini文件中提取对话内容
    
    Args:
        file_path: Gemini Python文件路径
        
    Returns:
        对话列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"文件大小: {len(content)} 字符")
        
        # 查找contents数组的起始位置
        contents_start = content.find('contents = [')
        if contents_start == -1:
            contents_start = content.find('contents=[')
        
        if contents_start == -1:
            print("❌ 未找到 contents 数组")
            return []
        
        print(f"✅ 找到 contents 数组，起始位置: {contents_start}")
        
        # 找到对应的结束位置（找到匹配的方括号）
        bracket_count = 0
        contents_end = contents_start
        in_contents = False
        
        for i in range(contents_start, len(content)):
            char = content[i]
            if char == '[':
                bracket_count += 1
                in_contents = True
            elif char == ']':
                bracket_count -= 1
                if in_contents and bracket_count == 0:
                    contents_end = i + 1
                    break
        
        # 提取contents内容
        contents_section = content[contents_start:contents_end]
        print(f"✅ 提取 contents 部分，长度: {len(contents_section)} 字符")
        
        # 查找所有的text="""..."""内容
        conversations = []
        
        # 使用正则表达式匹配所有的 types.Content 块
        content_pattern = r'types\.Content\s*\(\s*role\s*=\s*["\'](\w+)["\'].*?text\s*=\s*"""(.*?)"""\s*\)'
        matches = re.findall(content_pattern, contents_section, re.DOTALL)
        
        print(f"✅ 找到 {len(matches)} 个对话片段")
        
        for i, (role, text) in enumerate(matches):
            conversations.append({
                'role': role,
                'content': text.strip(),
                'index': i + 1
            })
            print(f"  - {role}: {len(text)} 字符")
        
        return conversations
        
    except Exception as e:
        print(f"❌ 提取对话时出错: {e}")
        return []


def extract_metadata_from_file(file_path: str, content: str) -> Dict[str, Any]:
    """
    提取文件元数据
    
    Args:
        file_path: 文件路径
        content: 文件内容
        
    Returns:
        元数据字典
    """
    metadata = {
        'file_name': os.path.basename(file_path),
        'file_path': file_path,
        'creation_time': datetime.now().isoformat(),
        'model': None,
        'api_key_ref': None,
        'file_size': f"{len(content)} 字符",
        'total_lines': len(content.split('\n'))
    }
    
    # 提取模型信息
    model_match = re.search(r'model\s*=\s*["\']([^"\']+)["\']', content)
    if model_match:
        metadata['model'] = model_match.group(1)
    
    # 提取API密钥引用
    api_key_match = re.search(r'api_key\s*=\s*os\.environ\.get\(["\']([^"\']+)["\']\)', content)
    if api_key_match:
        metadata['api_key_ref'] = api_key_match.group(1)
    
    return metadata


def generate_markdown_document(conversations: List[Dict[str, Any]], metadata: Dict[str, Any]) -> str:
    """
    生成Markdown文档
    
    Args:
        conversations: 对话列表
        metadata: 元数据
        
    Returns:
        Markdown内容
    """
    md_lines = []
    
    # 标题
    file_name = metadata.get('file_name', 'Unknown')
    md_lines.append(f"# 📝 Gemini 对话记录: {file_name}\n")
    
    # 生成时间
    creation_time = metadata.get('creation_time', '')
    if creation_time:
        try:
            dt = datetime.fromisoformat(creation_time.replace('Z', '+00:00'))
            formatted_date = dt.strftime('%Y年%m月%d日 %H:%M:%S')
            md_lines.append(f"**生成时间:** {formatted_date}\n")
        except:
            pass
    
    # 文档信息
    md_lines.append("## 📊 文档信息\n")
    md_lines.append("| 项目 | 值 |")
    md_lines.append("|------|-----|")
    md_lines.append(f"| 文件名 | `{metadata.get('file_name', 'N/A')}` |")
    
    if metadata.get('model'):
        md_lines.append(f"| AI模型 | `{metadata['model']}` |")
    
    if metadata.get('api_key_ref'):
        md_lines.append(f"| API密钥环境变量 | `{metadata['api_key_ref']}` |")
    
    md_lines.append(f"| 文件大小 | {metadata.get('file_size', 'N/A')} |")
    md_lines.append(f"| 总行数 | {metadata.get('total_lines', 'N/A')} 行 |")
    md_lines.append(f"| 对话数量 | {len(conversations)} 条 |\n")
    
    # 目录（如果对话较多）
    user_count = sum(1 for conv in conversations if conv['role'] == 'user')
    if user_count > 3:
        md_lines.append("## 📋 目录\n")
        round_num = 0
        for conv in conversations:
            if conv['role'] == 'user':
                round_num += 1
                title = conv['content'][:50].replace('\n', ' ').strip()
                if len(conv['content']) > 50:
                    title += '...'
                md_lines.append(f"{round_num}. [对话轮次 {round_num}: {title}](#对话轮次-{round_num})")
        md_lines.append("")
    
    # 对话内容
    md_lines.append("## 💬 对话内容\n")
    
    if not conversations:
        md_lines.append("⚠️ **未找到对话内容**\n")
        return '\n'.join(md_lines)
    
    # 生成对话
    round_num = 0
    i = 0
    
    while i < len(conversations):
        conv = conversations[i]
        
        if conv['role'] == 'user':
            round_num += 1
            md_lines.append(f"### 对话轮次 {round_num}\n")
            
            # 用户消息
            md_lines.append("#### 👤 用户\n")
            md_lines.append(format_message_content(conv['content']))
            md_lines.append("")
            
            # 查找对应的AI回复
            if i + 1 < len(conversations) and conversations[i + 1]['role'] == 'model':
                ai_conv = conversations[i + 1]
                md_lines.append("#### 🤖 AI助手\n")
                md_lines.append(format_message_content(ai_conv['content']))
                md_lines.append("")
                i += 2
            else:
                i += 1
            
            md_lines.append("---\n")
        
        elif conv['role'] == 'model':
            # 独立的AI消息
            round_num += 1
            md_lines.append(f"### AI消息 {round_num}\n")
            md_lines.append("#### 🤖 AI助手\n")
            md_lines.append(format_message_content(conv['content']))
            md_lines.append("")
            md_lines.append("---\n")
            i += 1
        else:
            i += 1
    
    return '\n'.join(md_lines)


def format_message_content(content: str) -> str:
    """
    格式化消息内容
    
    Args:
        content: 原始内容
        
    Returns:
        格式化后的内容
    """
    # 如果已经包含代码块，直接返回
    if '```' in content:
        return content
    
    # 检测是否是代码内容
    code_indicators = [
        'import ', 'def ', 'class ', 'if __name__', 'print(', 'return ',
        'import pandas', 'import numpy', 'import matplotlib', 'import seaborn',
        '.py', '.csv', 'DataFrame', 'plt.', 'sns.', 'def main', '# ',
        'for ', 'while ', 'try:', 'except:', 'with open'
    ]
    
    code_count = sum(1 for indicator in code_indicators if indicator in content)
    
    # 如果包含多个代码特征，包装为代码块
    if code_count >= 3 or content.count('\n') > 10:
        return f'```python\n{content}\n```'
    
    return content


def convert_gemini_to_markdown(input_file: str, output_file: Optional[str] = None) -> str:
    """
    转换Gemini文件为Markdown
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径（可选）
        
    Returns:
        输出文件路径
    """
    print(f"🚀 开始转换文件: {input_file}")
    
    # 读取文件
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return ""
    
    # 提取对话
    conversations = extract_conversations_from_gemini_file(input_file)
    
    # 提取元数据
    metadata = extract_metadata_from_file(input_file, content)
    
    # 生成Markdown
    markdown_content = generate_markdown_document(conversations, metadata)
    
    # 确定输出路径
    if output_file is None:
        input_path = Path(input_file)
        output_file = input_path.parent / f"{input_path.stem}_conversation.md"
    
    # 保存文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"✅ 转换完成: {output_file}")
        print(f"📊 提取了 {len(conversations)} 条对话")
        return str(output_file)
    except Exception as e:
        print(f"❌ 保存文件失败: {e}")
        return ""


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Gemini对话转Markdown转换器")
    parser.add_argument('input', help='输入的Gemini Python文件路径')
    parser.add_argument('-o', '--output', help='输出Markdown文件路径（可选）')
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.exists(args.input):
        print(f"❌ 输入文件不存在: {args.input}")
        return 1
    
    # 转换文件
    result = convert_gemini_to_markdown(args.input, args.output)
    
    if result:
        print(f"🎉 转换成功！输出文件: {result}")
        return 0
    else:
        print("❌ 转换失败")
        return 1


if __name__ == '__main__':
    exit(main())