"""
Token 消耗估算工具
根据文件大小和片段数量估算 token 消耗
"""

def estimate_tokens():
    print("=" * 60)
    print("Token 消耗估算")
    print("=" * 60)
    
    # 基本信息
    file_size_mb = 251.88  # 文件大小 MB
    total_fragments = 1276  # 总片段数
    avg_fragment_chars = 500  # 平均每个片段字符数（估算）
    
    # 提示词长度
    style_prompt_chars = 800  # 风格分析提示词约 800 字符
    rewrite_prompt_chars = 1000  # 改写提示词约 1000 字符
    
    # 预期输出长度
    style_output_chars = 500  # 风格分析输出约 500 字符
    rewrite_output_chars = 1000  # 改写输出约 1000 字符（假设改写后长度相似）
    
    # Token 估算（中文约 1.5 字符/token，英文约 4 字符/token）
    chars_per_token = 1.5  # 中文
    
    print(f"\n【文件信息】")
    print(f"  文件大小: {file_size_mb} MB")
    print(f"  总片段数: {total_fragments}")
    
    # 风格分析 token 估算
    print(f"\n【风格分析】")
    
    # 每个请求的 token
    input_tokens_per_request = (style_prompt_chars + avg_fragment_chars) / chars_per_token
    output_tokens_per_request = style_output_chars / chars_per_token
    total_tokens_per_request = input_tokens_per_request + output_tokens_per_request
    
    print(f"  每个请求:")
    print(f"    - 输入 token: ~{int(input_tokens_per_request)} (提示词 {int(style_prompt_chars/chars_per_token)} + 文本 {int(avg_fragment_chars/chars_per_token)})")
    print(f"    - 输出 token: ~{int(output_tokens_per_request)}")
    print(f"    - 总计: ~{int(total_tokens_per_request)} token")
    
    # 总 token
    total_style_tokens = total_tokens_per_request * total_fragments
    total_style_input = input_tokens_per_request * total_fragments
    total_style_output = output_tokens_per_request * total_fragments
    
    print(f"\n  全部片段:")
    print(f"    - 输入 token: ~{int(total_style_input):,}")
    print(f"    - 输出 token: ~{int(total_style_output):,}")
    print(f"    - 总计: ~{int(total_style_tokens):,} token")
    
    # 改写 token 估算（假设改写 10% 的片段）
    rewrite_ratio = 0.1  # 只改写 10% 的片段
    rewrite_fragments = int(total_fragments * rewrite_ratio)
    
    print(f"\n【改写】（假设改写 {rewrite_ratio*100:.0f}% 的片段，即 {rewrite_fragments} 个）")
    
    input_tokens_per_rewrite = (rewrite_prompt_chars + avg_fragment_chars) / chars_per_token
    output_tokens_per_rewrite = rewrite_output_chars / chars_per_token
    total_tokens_per_rewrite = input_tokens_per_rewrite + output_tokens_per_rewrite
    
    print(f"  每个请求:")
    print(f"    - 输入 token: ~{int(input_tokens_per_rewrite)}")
    print(f"    - 输出 token: ~{int(output_tokens_per_rewrite)}")
    print(f"    - 总计: ~{int(total_tokens_per_rewrite)} token")
    
    total_rewrite_tokens = total_tokens_per_rewrite * rewrite_fragments
    total_rewrite_input = input_tokens_per_rewrite * rewrite_fragments
    total_rewrite_output = output_tokens_per_rewrite * rewrite_fragments
    
    print(f"\n  全部改写:")
    print(f"    - 输入 token: ~{int(total_rewrite_input):,}")
    print(f"    - 输出 token: ~{int(total_rewrite_output):,}")
    print(f"    - 总计: ~{int(total_rewrite_tokens):,} token")
    
    # 总计
    print(f"\n{'=' * 60}")
    print(f"【总计】")
    total_all = total_style_tokens + total_rewrite_tokens
    total_input_all = total_style_input + total_rewrite_input
    total_output_all = total_style_output + total_rewrite_output
    
    print(f"  输入 token: ~{int(total_input_all):,}")
    print(f"  输出 token: ~{int(total_output_all):,}")
    print(f"  总计: ~{int(total_all):,} token")
    
    # 费用估算（以阿里云为例）
    print(f"\n【费用估算】（阿里云百练平台）")
    # qwen3.6-flash: 输入 0.001 元/千token，输出 0.002 元/千token
    input_price = 0.001  # 元/千token
    output_price = 0.002  # 元/千token
    
    cost_input = total_input_all / 1000 * input_price
    cost_output = total_output_all / 1000 * output_price
    cost_total = cost_input + cost_output
    
    print(f"  qwen3.6-flash 价格:")
    print(f"    - 输入: {input_price} 元/千token")
    print(f"    - 输出: {output_price} 元/千token")
    print(f"  预计费用:")
    print(f"    - 输入费用: ¥{cost_input:.2f}")
    print(f"    - 输出费用: ¥{cost_output:.2f}")
    print(f"    - 总计: ¥{cost_total:.2f}")
    
    # 本地模型对比
    print(f"\n【本地模型对比】")
    print(f"  使用 Ollama 本地模型:")
    print(f"    - Token 消耗: 0（本地计算）")
    print(f"    - 费用: ¥0")
    print(f"    - 节省: ¥{cost_total:.2f}")
    
    print(f"\n{'=' * 60}")

if __name__ == "__main__":
    estimate_tokens()
