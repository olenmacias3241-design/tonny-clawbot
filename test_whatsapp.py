#!/usr/bin/env python3
"""测试 WhatsApp 发送功能"""

import httpx
import sys

API_BASE = "http://localhost:8000"

def test_whatsapp(phone_number):
    """
    测试 WhatsApp 消息发送

    参数:
        phone_number: 手机号，格式: +86xxxxxxxxxx
    """
    print(f"📱 正在向 {phone_number} 发送 WhatsApp 测试消息...")

    try:
        response = httpx.post(
            f"{API_BASE}/send-whatsapp",
            json={
                "to": phone_number,
                "message": "🎉 恭喜！WhatsApp 通知功能已成功激活！\n\n这是来自 Claw Bot AI 的测试消息。\n\n✅ 系统已就绪！"
            },
            timeout=30.0
        )

        result = response.json()

        if result.get("success"):
            print("\n✅ 发送成功！")
            print("请检查您的 WhatsApp 是否收到消息。")
        else:
            print("\n❌ 发送失败")
            print(f"错误: {result.get('error', '未知错误')}")
            print(f"详情: {result.get('message', '')}")

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python test_whatsapp.py +86xxxxxxxxxx")
        print("\n示例:")
        print("  python test_whatsapp.py +8613812345678")
        sys.exit(1)

    phone = sys.argv[1]
    test_whatsapp(phone)
