#!/usr/bin/env python
"""测试 Claw Bot AI 的简单脚本"""

import httpx
import json
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    print("🔍 测试健康检查...")
    try:
        response = httpx.get(f"{BASE_URL}/health", timeout=5.0)
        print(f"✅ 健康检查通过: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

def test_root():
    """测试根端点"""
    print("\n🔍 测试根端点...")
    try:
        response = httpx.get(f"{BASE_URL}/", timeout=5.0)
        data = response.json()
        print(f"✅ 服务信息:")
        print(f"   名称: {data['name']}")
        print(f"   版本: {data['version']}")
        print(f"   状态: {data['status']}")
        return True
    except Exception as e:
        print(f"❌ 根端点测试失败: {e}")
        return False

def chat(message, conversation_id=None):
    """发送聊天消息"""
    print(f"\n💬 发送消息: {message}")
    try:
        payload = {"message": message}
        if conversation_id:
            payload["conversation_id"] = conversation_id

        response = httpx.post(
            f"{BASE_URL}/chat",
            json=payload,
            timeout=30.0
        )
        data = response.json()

        if data.get("error"):
            print(f"❌ 错误: {data['error']}")
            return None

        print(f"✅ Bot 回复: {data['message'][:100]}...")
        print(f"   对话ID: {data['conversation_id']}")
        return data
    except Exception as e:
        print(f"❌ 聊天失败: {e}")
        return None

def test_chat():
    """测试聊天功能"""
    print("\n🔍 测试聊天功能...")

    # 第一轮对话
    result1 = chat("Hello! Please respond with 'OK' if you can hear me.")
    if not result1 or result1.get("error"):
        print("\n⚠️  模型可能不可用，请检查 .env 中的 OPENAI_MODEL 配置")
        return False

    # 第二轮对话（保持上下文）
    conv_id = result1['conversation_id']
    result2 = chat("What was my first message?", conversation_id=conv_id)

    return result1 and result2

def test_conversations():
    """测试对话管理"""
    print("\n🔍 测试对话管理...")
    try:
        response = httpx.get(f"{BASE_URL}/conversations", timeout=5.0)
        conversations = response.json()
        print(f"✅ 当前对话数量: {len(conversations)}")
        return True
    except Exception as e:
        print(f"❌ 对话管理测试失败: {e}")
        return False

def interactive_mode():
    """交互模式"""
    print("\n💬 进入交互模式（输入 'exit' 退出）")
    conversation_id = None

    while True:
        try:
            user_input = input("\n你: ").strip()
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("👋 再见！")
                break

            if not user_input:
                continue

            result = chat(user_input, conversation_id)
            if result and not result.get("error"):
                conversation_id = result['conversation_id']
                print(f"\nBot: {result['message']}\n")

        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"错误: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("🤖 Claw Bot AI - 测试脚本")
    print("=" * 60)

    # 运行测试
    tests = [
        ("健康检查", test_health),
        ("根端点", test_root),
        ("聊天功能", test_chat),
        ("对话管理", test_conversations),
    ]

    passed = 0
    for name, test_func in tests:
        if test_func():
            passed += 1

    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{len(tests)} 通过")
    print("=" * 60)

    # 询问是否进入交互模式
    if passed >= 2:  # 至少基础功能可用
        response = input("\n是否进入交互模式？(y/n): ").strip().lower()
        if response == 'y':
            interactive_mode()
    else:
        print("\n⚠️  基础测试未通过，请检查服务器状态和配置")

if __name__ == "__main__":
    main()
